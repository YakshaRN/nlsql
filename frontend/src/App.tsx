import { useState, useEffect, useRef, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import type { Message, QueryResponse } from './types';
import { sendQuery } from './api';
import { Sidebar } from './components/Sidebar';
import { ChatInput } from './components/ChatInput';
import { MessageBubble } from './components/MessageBubble';
import { TypingIndicator } from './components/TypingIndicator';
import { BarChart3 } from 'lucide-react';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>(() => {
    const stored = localStorage.getItem('nlsql_session_id');
    return stored || uuidv4();
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    localStorage.setItem('nlsql_session_id', sessionId);
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const formatResponseContent = (response: QueryResponse): string => {
    switch (response.decision) {
      case 'EXECUTE':
        if (response.summary) {
          return response.summary;
        }
        return `Query executed successfully. Found ${response.data?.length || 0} records.`;
      
      case 'NEED_MORE_INFO':
        return response.clarification_question || 'I need more information to answer your question. Could you please provide more details?';
      
      case 'OUT_OF_SCOPE':
        return response.message || response.summary || "I'm sorry, but this question is outside the scope of what I can answer. I can help with ERCOT energy forecasting questions about GSI, load, temperature, wind, solar, and zonal data.";
      
      case 'ERROR':
        return response.summary || 'An error occurred while processing your request. Please try again.';
      
      default:
        return 'Received an unexpected response.';
    }
  };

  const handleSendMessage = useCallback(async (content: string) => {
    const userMessage: Message = {
      id: uuidv4(),
      type: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await sendQuery({
        question: content,
        session_id: sessionId,
      });

      const assistantMessage: Message = {
        id: uuidv4(),
        type: 'assistant',
        content: formatResponseContent(response),
        timestamp: new Date(),
        response,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: uuidv4(),
        type: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to connect to the server. Please ensure the backend is running.'}`,
        timestamp: new Date(),
        response: {
          decision: 'ERROR',
          data: null,
          summary: null,
          clarification_question: null,
          query_id: null,
          sql: null,
          params: null,
        },
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const handleNewChat = useCallback(() => {
    setMessages([]);
    setSessionId(uuidv4());
  }, []);

  const handleExampleClick = useCallback((question: string) => {
    if (!isLoading) {
      handleSendMessage(question);
    }
  }, [isLoading, handleSendMessage]);

  return (
    <div className="h-screen flex bg-slate-950 text-white">
      {/* Sidebar */}
      <Sidebar onNewChat={handleNewChat} onExampleClick={handleExampleClick} />

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col h-full">
        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            /* Welcome Screen */
            <div className="h-full flex flex-col items-center justify-center p-8 text-center">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-violet-600 rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-blue-500/20">
                <BarChart3 className="w-10 h-10 text-white" />
              </div>
              <h2 className="text-2xl font-bold mb-2">Welcome to ERCOT NLSQL</h2>
              <p className="text-slate-400 max-w-md mb-8">
                Ask questions about ERCOT energy forecasting data in natural language. 
                I'll translate your queries to SQL and return the results.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl">
                {[
                  'What is the peak probability of GSI exceeding 0.60 over the next 14 days?',
                  'Show me the expected load forecast for next week',
                  'What are the wind generation predictions for tomorrow?',
                  'Compare temperature forecasts across all zones',
                ].map((question, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleExampleClick(question)}
                    className="text-left p-4 bg-slate-800/50 hover:bg-slate-800 border border-slate-700 rounded-xl text-sm text-slate-300 transition-colors"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Messages List */
            <div className="max-w-4xl mx-auto p-6 space-y-6">
              {messages.map(message => (
                <MessageBubble key={message.id} message={message} />
              ))}
              {isLoading && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-slate-800 bg-slate-900/50 p-4">
          <div className="max-w-4xl mx-auto">
            <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
