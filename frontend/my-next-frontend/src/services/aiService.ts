// src/services/aiService.ts

/**
 * The 'role' must match what LM Studio expects: "system" | "user" | "assistant"
 */

export interface ChatMessage {
    role: 'system' | 'user' | 'assistant';
    content: string;
  }
  
  export interface AiResponse {
    status: string;
    response: string; // text returned from your Flask /api/task
  }
  
  export async function sendChatMessage(conversation: ChatMessage[]): Promise<string> {
    const apiBase = process.env.NEXT_PUBLIC_AI_API_URL ?? '';
  
    try {
      const res = await fetch(`${apiBase}/api/task`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation }),
      });
  
      if (!res.ok) {
        return `Error: HTTP ${res.status} ${res.statusText}`;
      }
  
      const data: AiResponse = await res.json();
      if (data.status === 'success') {
        return data.response;
      } else {
        return `AI API returned error status: ${data.status}`;
      }
    } catch (error: any) {
      console.error('Error calling AI API:', error);
      return `Error calling AI API: ${error.message}`;
    }
  }
  