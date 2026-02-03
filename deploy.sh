#!/bin/bash
# EC2 Deployment Script for ERCOT NLSQL
# Run this after cloning the repo on EC2

set -e

echo "=== ERCOT NLSQL Deployment Script ==="

# Get EC2 public IP
EC2_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")
echo "Detected EC2 IP: $EC2_IP"

# Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo "ERROR: .env file not found!"
    echo "Create a .env file with the following variables:"
    echo ""
    echo "DB_USER=your_db_username"
    echo "DB_PASS=your_db_password"
    echo "DB_HOST=your_db_host"
    echo "DB_PORT=5432"
    echo "DB_NAME=your_db_name"
    echo ""
    exit 1
fi

# Setup Python virtual environment
echo ""
echo "=== Setting up Python backend ==="
python3 -m venv venv 2>/dev/null || python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Setup frontend
echo ""
echo "=== Setting up React frontend ==="
cd frontend
npm install

# Configure frontend API URL
echo "VITE_API_URL=http://${EC2_IP}:8000" > .env
echo "Frontend will connect to: http://${EC2_IP}:8000"

# Build frontend
npm run build
cd ..

# Install PM2 if not present
if ! command -v pm2 &> /dev/null; then
    echo ""
    echo "=== Installing PM2 ==="
    sudo npm install -g pm2 serve
fi

# Create PM2 ecosystem config
echo ""
echo "=== Creating PM2 configuration ==="
SCRIPT_DIR=$(pwd)

cat > ecosystem.config.cjs << EOF
module.exports = {
  apps: [
    {
      name: 'nlsql-backend',
      cwd: '${SCRIPT_DIR}',
      script: '${SCRIPT_DIR}/venv/bin/uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 8000',
      interpreter: 'none',
      env_file: '${SCRIPT_DIR}/.env'
    },
    {
      name: 'nlsql-frontend',
      cwd: '${SCRIPT_DIR}/frontend',
      script: 'serve',
      args: '-s dist -l 5173',
      interpreter: 'none'
    }
  ]
};
EOF

# Stop existing processes
pm2 delete all 2>/dev/null || true

# Start services
echo ""
echo "=== Starting services with PM2 ==="
pm2 start ecosystem.config.cjs
pm2 save

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "Frontend: http://${EC2_IP}:5173"
echo "Backend:  http://${EC2_IP}:8000"
echo ""
echo "Useful commands:"
echo "  pm2 status          - Check service status"
echo "  pm2 logs            - View logs"
echo "  pm2 restart all     - Restart services"
echo ""
