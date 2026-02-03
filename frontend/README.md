# ERCOT NLSQL Frontend

A modern React frontend for the ERCOT Natural Language to SQL API.

## Features

- Chat-based interface for natural language queries
- Real-time data visualization with charts and tables
- Session management for conversation context
- Example queries for quick exploration
- Dark theme with modern UI

## Tech Stack

- React 18 with TypeScript
- Vite for fast development
- Tailwind CSS for styling
- Recharts for data visualization
- Lucide React for icons

## Getting Started

### Prerequisites

- Node.js 18+
- Backend server running on http://localhost:8000

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The frontend will be available at http://localhost:5173

### Build for Production

```bash
npm run build
```

The production build will be in the `dist/` folder.

## Configuration

Create a `.env` file to configure the API URL:

```env
VITE_API_URL=http://localhost:8000
```

## Usage

1. Start the backend server (`uvicorn app.main:app --reload`)
2. Start the frontend (`npm run dev`)
3. Open http://localhost:5173 in your browser
4. Ask questions about ERCOT energy forecasting data in natural language
