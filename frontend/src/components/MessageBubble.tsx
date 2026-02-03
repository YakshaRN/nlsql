import { User, Bot, AlertCircle, HelpCircle, Database, ChevronDown, ChevronUp, Code, Copy, Check } from 'lucide-react';
import { useState } from 'react';
import type { Message } from '../types';
import { DataTable } from './DataTable';
import { DataChart } from './DataChart';
import { QueryExplanation } from './QueryExplanation';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const [showDetails, setShowDetails] = useState(false);
  const [showRawResponse, setShowRawResponse] = useState(false);
  const [showChart, setShowChart] = useState(true);
  const [copied, setCopied] = useState(false);
  const isUser = message.type === 'user';
  const response = message.response;

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getDecisionBadge = () => {
    if (!response) return null;

    const badges = {
      EXECUTE: { color: 'bg-green-500/20 text-green-400 border-green-500/30', icon: Database, label: 'Query Executed' },
      NEED_MORE_INFO: { color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30', icon: HelpCircle, label: 'More Info Needed' },
      OUT_OF_SCOPE: { color: 'bg-orange-500/20 text-orange-400 border-orange-500/30', icon: AlertCircle, label: 'Out of Scope' },
      ERROR: { color: 'bg-red-500/20 text-red-400 border-red-500/30', icon: AlertCircle, label: 'Error' },
    };

    const badge = badges[response.decision];
    const Icon = badge.icon;

    return (
      <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium border ${badge.color}`}>
        <Icon className="w-3 h-3" />
        {badge.label}
      </span>
    );
  };

  return (
    <div className={`flex gap-3 animate-fade-in ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center ${
        isUser ? 'bg-blue-600' : 'bg-gradient-to-br from-violet-600 to-blue-600'
      }`}>
        {isUser ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-white" />}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-[85%] ${isUser ? 'flex flex-col items-end' : ''}`}>
        <div className={`rounded-2xl px-4 py-3 ${
          isUser 
            ? 'bg-blue-600 text-white rounded-tr-sm' 
            : 'bg-slate-800 text-slate-100 rounded-tl-sm border border-slate-700'
        }`}>
          {/* User message or assistant response summary */}
          <p className="whitespace-pre-wrap">{message.content}</p>

          {/* Response badge and details */}
          {response && (
            <div className="mt-3 space-y-3">
              <div className="flex items-center gap-2 flex-wrap">
                {getDecisionBadge()}
                {response.query_id && (
                  <span className="text-xs text-slate-400 font-mono bg-slate-900/50 px-2 py-1 rounded">
                    {response.query_id}
                  </span>
                )}
              </div>

              {/* Query Explanation - always show for EXECUTE */}
              {response.decision === 'EXECUTE' && (
                <QueryExplanation 
                  queryId={response.query_id} 
                  params={response.params}
                  data={response.data}
                />
              )}

              {/* Data display */}
              {response.decision === 'EXECUTE' && response.data && response.data.length > 0 && (
                <div className="space-y-3">
                  {/* Chart/Table toggle */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => setShowChart(true)}
                      className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                        showChart ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      }`}
                    >
                      Chart
                    </button>
                    <button
                      onClick={() => setShowChart(false)}
                      className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                        !showChart ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      }`}
                    >
                      Table
                    </button>
                  </div>

                  {/* Chart or Table */}
                  <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700">
                    {showChart ? (
                      <DataChart data={response.data} queryId={response.query_id} />
                    ) : (
                      <DataTable data={response.data} />
                    )}
                  </div>
                </div>
              )}

              {/* Toggle buttons for SQL and Raw Response */}
              <div className="flex flex-wrap gap-2">
                {response.sql && (
                  <button
                    onClick={() => setShowDetails(!showDetails)}
                    className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-300 transition-colors bg-slate-900/50 px-2 py-1 rounded"
                  >
                    {showDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    {showDetails ? 'Hide' : 'Show'} SQL & Params
                  </button>
                )}
                {response.data && response.data.length > 0 && (
                  <button
                    onClick={() => setShowRawResponse(!showRawResponse)}
                    className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-300 transition-colors bg-slate-900/50 px-2 py-1 rounded"
                  >
                    <Code className="w-4 h-4" />
                    {showRawResponse ? 'Hide' : 'Show'} JSON Data
                  </button>
                )}
              </div>

              {/* SQL and params details */}
              {showDetails && response.sql && (
                <div className="space-y-2 text-xs">
                  <div className="bg-slate-900 rounded-lg p-3 overflow-x-auto">
                    <p className="text-slate-400 mb-2 font-medium">SQL Query:</p>
                    <pre className="text-green-400 font-mono whitespace-pre-wrap">{response.sql}</pre>
                  </div>
                  {response.params && Object.keys(response.params).length > 0 && (
                    <div className="bg-slate-900 rounded-lg p-3">
                      <p className="text-slate-400 mb-2 font-medium">Parameters:</p>
                      <pre className="text-blue-400 font-mono">{JSON.stringify(response.params, null, 2)}</pre>
                    </div>
                  )}
                </div>
              )}

              {/* Raw Data Response */}
              {showRawResponse && response.data && (
                <div className="text-xs">
                  <div className="bg-slate-900 rounded-lg p-3 overflow-x-auto max-h-96">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-slate-400 font-medium">Query Data ({response.data.length} records):</p>
                      <button
                        onClick={() => copyToClipboard(JSON.stringify(response.data, null, 2))}
                        className="flex items-center gap-1 text-slate-400 hover:text-slate-300 transition-colors"
                      >
                        {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                        {copied ? 'Copied!' : 'Copy'}
                      </button>
                    </div>
                    <pre className="text-amber-400 font-mono whitespace-pre-wrap">{JSON.stringify(response.data, null, 2)}</pre>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Timestamp */}
        <span className="text-xs text-slate-500 mt-1.5 px-1">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
}
