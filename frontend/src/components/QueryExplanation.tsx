import { Info, TrendingUp, TrendingDown, BarChart2 } from 'lucide-react';

interface QueryExplanationProps {
  queryId: string | null;
  params: Record<string, unknown> | null;
  data: Record<string, unknown>[] | null;
}

// Human-readable explanations for each query type
const QUERY_EXPLANATIONS: Record<string, { title: string; description: string; unit?: string }> = {
  // GSI Queries
  GSI_PEAK_PROBABILITY_14_DAYS: {
    title: 'Grid Stress Index (GSI) Peak Probability',
    description: 'Shows the probability of grid stress exceeding the specified threshold over the forecast period. Higher probabilities indicate greater risk of grid constraints.',
    unit: 'probability (0-1)',
  },
  GSI_PEAK_TIMING: {
    title: 'GSI Peak Timing Forecast',
    description: 'Identifies when grid stress is expected to peak. Useful for planning demand response and resource scheduling.',
  },
  GSI_THRESHOLD_EXCEEDANCE: {
    title: 'GSI Threshold Exceedance Analysis',
    description: 'Analyzes how often and when grid stress exceeds critical thresholds.',
  },
  GSI_HOURLY_DISTRIBUTION: {
    title: 'Hourly GSI Distribution',
    description: 'Shows the distribution of grid stress values across ensemble scenarios for each hour.',
  },

  // Load & Temperature Queries
  PEAK_LOAD_FORECAST: {
    title: 'Peak Load Forecast',
    description: 'Forecasts the maximum electricity demand expected during the specified period.',
    unit: 'MW',
  },
  LOAD_FORECAST_TIMESERIES: {
    title: 'Load Forecast Time Series',
    description: 'Hourly electricity demand forecast showing expected load patterns over time.',
    unit: 'MW',
  },
  TEMPERATURE_FORECAST: {
    title: 'Temperature Forecast',
    description: 'Population-weighted temperature forecast for the specified zone.',
    unit: '°C',
  },
  LOAD_TEMPERATURE_CORRELATION: {
    title: 'Load-Temperature Correlation',
    description: 'Shows the relationship between temperature and electricity demand.',
  },

  // Renewables Queries
  WIND_GENERATION_FORECAST: {
    title: 'Wind Generation Forecast',
    description: 'Forecasted wind power generation based on ensemble weather scenarios.',
    unit: 'MW',
  },
  SOLAR_GENERATION_FORECAST: {
    title: 'Solar Generation Forecast',
    description: 'Forecasted solar power generation based on irradiance and weather conditions.',
    unit: 'MW',
  },
  P50_RENEWABLE_GEN_PER_ZONE: {
    title: 'P50 Renewable Generation by Zone',
    description: 'Median (50th percentile) renewable generation forecast for each load zone. P50 represents the most likely outcome.',
    unit: 'MW',
  },
  RENEWABLE_CAPACITY_FACTOR: {
    title: 'Renewable Capacity Factor',
    description: 'Shows what percentage of installed renewable capacity is expected to generate.',
    unit: '%',
  },

  // Zonal Queries
  ZONAL_LOAD_COMPARISON: {
    title: 'Zonal Load Comparison',
    description: 'Compares electricity demand across different ERCOT load zones.',
    unit: 'MW',
  },
  ZONAL_NET_DEMAND: {
    title: 'Zonal Net Demand',
    description: 'Net demand (load minus renewables) by zone, showing controllable generation needs.',
    unit: 'MW',
  },

  // Advanced Queries
  NET_DEMAND_FORECAST: {
    title: 'Net Demand Forecast',
    description: 'Load minus renewable generation, representing demand that must be met by dispatchable resources.',
    unit: 'MW',
  },
  TAIL_RISK_ANALYSIS: {
    title: 'Tail Risk Analysis',
    description: 'Analyzes extreme scenarios (P90, P95, P99) to understand worst-case outcomes.',
  },
};

export function QueryExplanation({ queryId, params, data }: QueryExplanationProps) {
  const explanation = queryId ? QUERY_EXPLANATIONS[queryId] : null;

  // Calculate data summary statistics
  const dataSummary = (() => {
    if (!data || data.length === 0) return null;

    const columns = Object.keys(data[0]);
    const numericColumns = columns.filter(col => typeof data[0][col] === 'number');
    
    if (numericColumns.length === 0) return null;

    const mainColumn = numericColumns[0];
    const values = data.map(row => row[mainColumn] as number).filter(v => v !== null && v !== undefined);
    
    if (values.length === 0) return null;

    const min = Math.min(...values);
    const max = Math.max(...values);
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    
    return {
      column: mainColumn,
      min,
      max,
      avg,
      count: data.length,
    };
  })();

  const formatValue = (value: number): string => {
    if (Math.abs(value) >= 1000000) return `${(value / 1000000).toFixed(2)}M`;
    if (Math.abs(value) >= 1000) return `${(value / 1000).toFixed(1)}K`;
    if (Math.abs(value) < 1) return value.toFixed(4);
    return value.toFixed(1);
  };

  const formatColumnName = (name: string): string => {
    return name
      .replace(/_/g, ' ')
      .replace(/([a-z])([A-Z])/g, '$1 $2')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const formatParamValue = (_key: string, value: unknown): string => {
    if (typeof value === 'string' && value.includes('T')) {
      try {
        const date = new Date(value);
        return date.toLocaleString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        });
      } catch {
        return String(value);
      }
    }
    return String(value);
  };

  return (
    <div className="space-y-3">
      {/* Query Explanation */}
      {explanation && (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
          <div className="flex items-start gap-2">
            <Info className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-semibold text-blue-300">{explanation.title}</h4>
              <p className="text-xs text-slate-400 mt-1">{explanation.description}</p>
              {explanation.unit && (
                <p className="text-xs text-slate-500 mt-1">Unit: {explanation.unit}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Parameters Used */}
      {params && Object.keys(params).length > 0 && (
        <div className="bg-slate-800/50 rounded-lg p-3">
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Query Parameters</h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {Object.entries(params).map(([key, value]) => (
              <div key={key} className="flex flex-col">
                <span className="text-slate-500">{formatColumnName(key)}</span>
                <span className="text-slate-200 font-medium">{formatParamValue(key, value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Data Summary */}
      {dataSummary && (
        <div className="bg-slate-800/50 rounded-lg p-3">
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Data Summary</h4>
          <div className="grid grid-cols-4 gap-3 text-xs">
            <div className="flex flex-col items-center p-2 bg-slate-900/50 rounded">
              <BarChart2 className="w-4 h-4 text-slate-400 mb-1" />
              <span className="text-slate-500">Records</span>
              <span className="text-slate-200 font-bold">{dataSummary.count.toLocaleString()}</span>
            </div>
            <div className="flex flex-col items-center p-2 bg-slate-900/50 rounded">
              <TrendingDown className="w-4 h-4 text-green-400 mb-1" />
              <span className="text-slate-500">Min</span>
              <span className="text-green-400 font-bold">{formatValue(dataSummary.min)}</span>
            </div>
            <div className="flex flex-col items-center p-2 bg-slate-900/50 rounded">
              <TrendingUp className="w-4 h-4 text-red-400 mb-1" />
              <span className="text-slate-500">Max</span>
              <span className="text-red-400 font-bold">{formatValue(dataSummary.max)}</span>
            </div>
            <div className="flex flex-col items-center p-2 bg-slate-900/50 rounded">
              <BarChart2 className="w-4 h-4 text-blue-400 mb-1" />
              <span className="text-slate-500">Average</span>
              <span className="text-blue-400 font-bold">{formatValue(dataSummary.avg)}</span>
            </div>
          </div>
          <p className="text-xs text-slate-500 mt-2 text-center">
            Statistics for: {formatColumnName(dataSummary.column)}
          </p>
        </div>
      )}
    </div>
  );
}
