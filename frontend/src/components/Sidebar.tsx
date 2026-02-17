import { Zap, Database, Wind, Thermometer, BarChart3, MessageSquarePlus, Info } from 'lucide-react';

interface SidebarProps {
  onNewChat: () => void;
  onExampleClick: (question: string) => void;
}

const exampleQueries = [
  {
    category: 'Grid Stress (GSI)',
    icon: Zap,
    color: 'text-red-400',
    questions: [
      'What is the probability that ERCOT grid stress exceeds 0.8 tomorrow?',
      'Show me the GSI forecast range (P10/P50/P90) for the next 7 days',
    ],
  },
  {
    category: 'Load & Temperature',
    icon: Thermometer,
    color: 'text-orange-400',
    questions: [
      'What is the expected temperature in Houston for the next 3 days?',
      'Compare peak demand across all zones for tomorrow afternoon',
    ],
  },
  {
    category: 'Renewables',
    icon: Wind,
    color: 'text-green-400',
    questions: [
      'Show me the wind generation forecast range for West Texas this week',
      'What is the solar capacity factor forecast for tomorrow?',
    ],
  },
  {
    category: 'Zonal Analysis',
    icon: Database,
    color: 'text-blue-400',
    questions: [
      'Compare wind generation between West and South zones for the next 3 days',
      'What is the peak load forecast for Houston vs North zone?',
    ],
  },
];

export function Sidebar({ onNewChat, onExampleClick }: SidebarProps) {
  return (
    <aside className="w-72 bg-slate-900 border-r border-slate-800 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-violet-600 rounded-xl flex items-center justify-center">
            <BarChart3 className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-white text-lg">ERCOT NLSQL</h1>
            <p className="text-xs text-slate-400">Energy Forecast Assistant</p>
          </div>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium transition-colors"
        >
          <MessageSquarePlus className="w-5 h-5" />
          New Conversation
        </button>
      </div>

      {/* Example Queries */}
      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-2">
          Example Questions
        </p>
        
        {exampleQueries.map((category) => {
          const Icon = category.icon;
          return (
            <div key={category.category} className="space-y-1.5">
              <div className={`flex items-center gap-2 px-2 ${category.color}`}>
                <Icon className="w-4 h-4" />
                <span className="text-xs font-medium">{category.category}</span>
              </div>
              {category.questions.map((question, idx) => (
                <button
                  key={idx}
                  onClick={() => onExampleClick(question)}
                  className="w-full text-left px-3 py-2 text-sm text-slate-300 hover:bg-slate-800 rounded-lg transition-colors line-clamp-2"
                >
                  {question}
                </button>
              ))}
            </div>
          );
        })}
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800">
        <div className="flex items-start gap-2 text-xs text-slate-500">
          <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <p>
            Ask natural language questions about ERCOT energy forecasts. 
            The system will translate your query to SQL.
          </p>
        </div>
      </div>
    </aside>
  );
}
