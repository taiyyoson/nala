import React, { useState, useEffect } from "react";

type Message = {
  id: number;               //id needed?
  sender: "nala" | "user"; // replace with username 
  text: string;
  timestamp: Date;
};

// API service to communicate with FastAPI backend
const chatAPI = {
  sendMessage: async (message: string): Promise<string> => {
    try {
      console.log('Sending message to backend:', message);
      
      const response = await fetch('http://localhost:8000/api/v1/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
      });
      
      console.log('Backend response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Backend response data:', data);
      
      return data.response || data.message || "Sorry, I didn't understand that.";
    } catch (error) {
      console.error('Error sending message:', error);
      return "I'm having trouble connecting to the backend. Make sure it's running on port 8000.";
    }
  },

  // Test backend health
  testConnection: async (): Promise<boolean> => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/health');
      return response.ok;
    } catch (error) {
      console.error('Backend health check failed:', error);
      return false;
    }
  }
};

export default function Week1CoachingChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);

  useEffect(() => {
    // Test backend connection on component mount
    testBackendConnection();
  }, []);

  const testBackendConnection = async () => {
    console.log('Testing backend connection...');
    const isConnected = await chatAPI.testConnection();
    setBackendConnected(isConnected);
    
    if (isConnected) {
      console.log('Backend connected! Sending initial greeting...');
      // Send initial greeting
      sendInitialGreeting();
    } else {
      console.log('Backend not connected. Make sure to run: python dev.py');
    }
  };

  const sendInitialGreeting = async () => {
    setIsLoading(true);
    
    const response = await chatAPI.sendMessage("hello");
    
    const nalaMessage: Message = {
      id: Date.now(),
      sender: "nala",
      text: response,
      timestamp: new Date()
    };

    setMessages([nalaMessage]);
    setIsLoading(false);
  };

  const sendUserMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now(),
      sender: "user",
      text: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const messageText = input.trim();
    setInput("");
    setIsLoading(true);

    const response = await chatAPI.sendMessage(messageText);

    const nalaMessage: Message = {
      id: Date.now() + 1,
      sender: "nala",
      text: response,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, nalaMessage]);
    setIsLoading(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      sendUserMessage();
    }
  };

  return (
    <div className="chat-container">
      {/* Header */}
      <div className="header">
        <h1>NALA Health Coach</h1>
        <p>Week 1 Session</p>
        {backendConnected === null && <p>Testing connection...</p>}
        {backendConnected === false && (
          <p style={{color: 'red'}}>
            Backend not connected. Run: python dev.py
          </p>
        )}
        {backendConnected === true && (
          <p style={{color: 'green'}}>Connected to backend</p>
        )}
      </div>

      {/* Messages */}
      <div className="messages">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.sender}`}>
            <div className={`message-bubble ${message.sender}`}>
              <strong>{message.sender === 'user' ? 'You' : 'NALA'}:</strong>
              <p>{message.text}</p>
              <small>{message.timestamp.toLocaleTimeString()}</small>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="message nala">
            <div className="message-bubble nala">
              <p>NALA is typing...</p>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="input-area">
        <input
          type="text"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          disabled={isLoading || backendConnected === false}
        />
        <button 
          onClick={sendUserMessage}
          disabled={isLoading || !input.trim() || backendConnected === false}
        >
          Send
        </button>
      </div>

      {/* Debug Info */}
      <div style={{padding: '8px', fontSize: '12px', background: '#f8f8f8'}}>
        <p>Backend Status: {backendConnected ? '✅ Connected' : '❌ Disconnected'}</p>
        <p>Messages: {messages.length}</p>
        <p>Loading: {isLoading ? 'Yes' : 'No'}</p>
      </div>
    </div>
  );
}