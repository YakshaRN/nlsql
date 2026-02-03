import { useMemo } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface DataChartProps {
  data: Record<string, unknown>[];
}

const COLORS = [
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#f97316', // orange
];

export function DataChart({ data }: DataChartProps) {
  const { chartData, xKey, numericKeys, chartType } = useMemo(() => {
    if (!data || data.length === 0) {
      return { chartData: [], xKey: '', numericKeys: [], chartType: 'line' as const };
    }

    const columns = Object.keys(data[0]);
    
    // Find potential X-axis (datetime or string column)
    const dateColumns = columns.filter(col => 
      col.toLowerCase().includes('date') || 
      col.toLowerCase().includes('time') ||
      col.toLowerCase().includes('datetime')
    );
    const stringColumns = columns.filter(col => 
      typeof data[0][col] === 'string' && !dateColumns.includes(col)
    );
    
    // Find numeric columns for Y-axis
    const numericCols = columns.filter(col => 
      typeof data[0][col] === 'number'
    );

    // Determine X key
    let xAxisKey = dateColumns[0] || stringColumns[0] || columns[0];
    
    // Determine chart type
    let type: 'line' | 'bar' = 'line';
    if (data.length <= 10 && numericCols.length <= 3) {
      type = 'bar';
    }

    // Format data for chart
    const formattedData = data.slice(0, 100).map(row => {
      const formatted: Record<string, unknown> = {};
      
      columns.forEach(col => {
        if (col === xAxisKey) {
          // Format datetime for display
          const value = row[col];
          if (typeof value === 'string' && value.includes('T')) {
            const date = new Date(value);
            formatted[col] = date.toLocaleDateString('en-US', { 
              month: 'short', 
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            });
          } else {
            formatted[col] = value;
          }
        } else {
          formatted[col] = row[col];
        }
      });
      
      return formatted;
    });

    return {
      chartData: formattedData,
      xKey: xAxisKey,
      numericKeys: numericCols,
      chartType: type,
    };
  }, [data]);

  if (!chartData.length || !numericKeys.length) {
    return (
      <div className="h-64 flex items-center justify-center text-slate-400">
        <p>No numeric data available for chart visualization</p>
      </div>
    );
  }

  const formatTooltipValue = (value: number | undefined) => {
    if (value === undefined || typeof value !== 'number') return String(value);
    if (Math.abs(value) >= 1000000) {
      return `${(value / 1000000).toFixed(2)}M`;
    }
    if (Math.abs(value) >= 1000) {
      return `${(value / 1000).toFixed(2)}K`;
    }
    return value.toFixed(4);
  };

  const formatAxisLabel = (label: string): string => {
    return label
      .replace(/_/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const commonProps = {
    data: chartData,
    margin: { top: 10, right: 30, left: 10, bottom: 0 },
  };

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        {chartType === 'bar' ? (
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis 
              dataKey={xKey} 
              stroke="#94a3b8" 
              fontSize={11}
              tickLine={false}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis 
              stroke="#94a3b8" 
              fontSize={11}
              tickLine={false}
              tickFormatter={(v) => formatTooltipValue(v)}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #475569',
                borderRadius: '8px',
                color: '#f1f5f9',
              }}
              formatter={(value, name) => [formatTooltipValue(value as number | undefined), formatAxisLabel(String(name))]}
            />
            <Legend formatter={(value) => formatAxisLabel(value)} />
            {numericKeys.slice(0, 4).map((key, index) => (
              <Bar
                key={key}
                dataKey={key}
                fill={COLORS[index % COLORS.length]}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        ) : (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis 
              dataKey={xKey} 
              stroke="#94a3b8" 
              fontSize={11}
              tickLine={false}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis 
              stroke="#94a3b8" 
              fontSize={11}
              tickLine={false}
              tickFormatter={(v) => formatTooltipValue(v)}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #475569',
                borderRadius: '8px',
                color: '#f1f5f9',
              }}
              formatter={(value, name) => [formatTooltipValue(value as number | undefined), formatAxisLabel(String(name))]}
            />
            <Legend formatter={(value) => formatAxisLabel(value)} />
            {numericKeys.slice(0, 4).map((key, index) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={COLORS[index % COLORS.length]}
                strokeWidth={2}
                dot={data.length <= 20}
                activeDot={{ r: 6 }}
              />
            ))}
          </LineChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
