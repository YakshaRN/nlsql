interface DataTableProps {
  data: Record<string, unknown>[];
}

export function DataTable({ data }: DataTableProps) {
  if (!data || data.length === 0) {
    return <p className="text-slate-400 text-sm">No data to display</p>;
  }

  const columns = Object.keys(data[0]);
  const maxRows = 50;
  const displayData = data.slice(0, maxRows);

  const formatValue = (value: unknown): string => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'number') {
      if (Number.isInteger(value)) return value.toLocaleString();
      return value.toLocaleString(undefined, { maximumFractionDigits: 4 });
    }
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  };

  const formatHeader = (header: string): string => {
    return header
      .replace(/_/g, ' ')
      .replace(/([a-z])([A-Z])/g, '$1 $2')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <div className="overflow-x-auto max-h-96">
      <table className="w-full text-sm text-left">
        <thead className="text-xs uppercase bg-slate-800 text-slate-300 sticky top-0">
          <tr>
            {columns.map((col) => (
              <th key={col} className="px-4 py-3 font-semibold whitespace-nowrap">
                {formatHeader(col)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700">
          {displayData.map((row, idx) => (
            <tr key={idx} className="hover:bg-slate-800/50 transition-colors">
              {columns.map((col) => (
                <td key={col} className="px-4 py-2.5 text-slate-200 whitespace-nowrap">
                  {formatValue(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {data.length > maxRows && (
        <p className="text-xs text-slate-500 mt-3 text-center">
          Showing {maxRows} of {data.length} rows
        </p>
      )}
    </div>
  );
}
