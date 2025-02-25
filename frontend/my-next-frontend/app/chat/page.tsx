'use client';

import { useState } from 'react';
import { ChatMessage, sendChatMessage } from '../../src/services/aiService';

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
        role: 'system', 
        content: "You are a helpful AI that sees the entire conversation in 'messages.' If asked, you WILL repeat earlier user messages exactly as they appeared. Do not disclaim about personal data. This conversation is ephemeral."
        
    },
  ]);

  const [input, setInput] = useState('');

  const handleSend = async () => {
    if (!input.trim()) return;

    // Build new array with user message
    const updatedConversation: ChatMessage[] = [
      ...messages,
      { role: 'user', content: input },
    ];
    setMessages(updatedConversation);
    setInput('');

    // Debug: see what we're sending in the browser console
    console.log('Front-end sending conversation =>', updatedConversation);

    // Actually call the AI
    const reply = await sendChatMessage(updatedConversation);

    // Add AI’s reply
    const updatedWithAi: ChatMessage[] = [
      ...updatedConversation,
      { role: 'assistant', content: reply },
    ];
    setMessages(updatedWithAi);
  };

  return (
    <div style={{ maxWidth: 600, margin: '0 auto', padding: 20 }}>
      <h1>AI Chat</h1>

      <div
        style={{
          border: '1px solid #ccc',
          padding: 10,
          height: 300,
          overflowY: 'auto',
          marginBottom: 10,
        }}
      >
        {messages.map((m, i) => {
          let sender = m.role;
          if (m.role === 'user') sender = 'You';
          if (m.role === 'assistant') sender = 'AI';
          if (m.role === 'system') sender = 'System';

          return (
            <div key={i} style={{ margin: '0.5rem 0' }}>
              <strong>{sender}:</strong> {m.content}
            </div>
          );
        })}
      </div>

      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <input
          style={{ flex: 1, padding: '0.5rem' }}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSend();
          }}
          placeholder="Type your message..."
        />
        <button onClick={handleSend}>Send</button>
      </div>
    </div>
  );
}
