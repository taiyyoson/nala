// src/services/ApiService.ts
const API_BASE_URL = 'http://localhost:8000/api/v1/chat/message';

export class ApiService {
  static async testConnection() {
    try {
      console.log(`🔍 Testing connection to: ${API_BASE_URL.replace('/api/v1', '')}/api/v1/health`);
      const response = await fetch(`${API_BASE_URL.replace('/api/v1', '')}/api/v1/health`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      console.log('✅ Backend connection successful:', result);
      return result;
    } catch (error) {
      console.error('❌ Backend connection failed:', error);
      console.error('📍 Attempted URL:', `${API_BASE_URL.replace('/api/v1', '')}/api/v1/health`);
      throw error;
    }
  }

  static async sendMessage(message: string) {
    try {
      const response = await fetch(API_BASE_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  static async getConversation(conversationId: string) {
    try {
      const response = await fetch(`${API_BASE_URL.replace('/message', '')}/conversation/${conversationId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  static async checkHealth() {
    try {
      const response = await fetch(`${API_BASE_URL.replace('/api/v1/chat/message', '')}/api/v1/health`);
      return await response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }
}