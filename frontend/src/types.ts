export interface QueryRequest {
  question: string;
  session_id: string | null;
}

export interface QueryResponse {
  decision: 'EXECUTE' | 'NEED_MORE_INFO' | 'OUT_OF_SCOPE' | 'SYSTEM_INFO' | 'CANNOT_ANSWER' | 'ERROR';
  data: Record<string, unknown>[] | null;
  summary: string | null;
  message: string | null;
  clarification_question: string | null;
  query_id: string | null;
  sql: string | null;
  params: Record<string, unknown> | null;
  explanation: string | null;
  assumptions: string | null;
  info_type: string | null;
  similarity_score: number | null;
  confidence: string | null;
}

export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  response?: QueryResponse;
}
