import { Bot } from 'lucide-react';

export function TypingIndicator() {
  return (
    <div className="flex gap-3 animate-fade-in">
      <div className="flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center bg-gradient-to-br from-violet-600 to-blue-600">
        <Bot className="w-5 h-5 text-white" />
      </div>
      <div className="bg-slate-800 rounded-2xl rounded-tl-sm px-4 py-3 border border-slate-700">
        <div className="flex gap-1.5">
          <span className="w-2 h-2 bg-slate-400 rounded-full typing-dot"></span>
          <span className="w-2 h-2 bg-slate-400 rounded-full typing-dot"></span>
          <span className="w-2 h-2 bg-slate-400 rounded-full typing-dot"></span>
        </div>
      </div>
    </div>
  );
}
