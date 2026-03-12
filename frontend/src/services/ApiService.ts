// src/services/ApiService.ts

import { getAuth } from "firebase/auth";

// Toggle between local and deployed backend
const USE_DEPLOYED = true; // Set to false for local development
const BASE_URL = USE_DEPLOYED
  ? "https://nala-backend-serv.onrender.com"
  : "http://127.0.0.1:8000";
export const API_BASE = `${BASE_URL}/api/v1`;

export class ApiService {

  private static async getAuthHeaders(): Promise<Record<string, string>> {
    const currentUser = getAuth().currentUser;
    if (!currentUser) {
      throw new Error("User not authenticated");
    }
    const token = await currentUser.getIdToken();
    return {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    };
  }

  static async checkHealth() {
    try {
      const response = await fetch(`${API_BASE}/health`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error("❌ Health check failed:", error);
      throw error;
    }
  }


  static async sendMessage(
    message: string,
    userId?: string,
    sessionNumber?: number,
    conversationId?: string
  ) {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${API_BASE}/chat/message`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          message,
          user_id: userId,
          session_number: sessionNumber,
          conversation_id: conversationId,
        }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error("❌ Chat message failed:", error);
      throw error;
    }
  }

  /* ----------------------------------------
     SESSION DATA ENDPOINTS
  ---------------------------------------- */
  static async getSessionData(userId: string, sessionNumber: number) {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(
        `${API_BASE}/session/data/${userId}/${sessionNumber}`,
        { headers }
      );
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error("❌ Failed to fetch session data:", error);
      return null;
    }
  }

  static async getLatestSession(userId: string) {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${API_BASE}/session/latest/${userId}`, {
        headers,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error("❌ Failed to fetch latest session:", error);
      return null;
    }
  }


  static async getUserStatus(userId: string) {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${API_BASE}/user/status/${userId}`, {
        headers,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error("❌ Failed to fetch user status:", error);
      return null;
    }
  }

  static async completeOnboarding(userId: string) {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${API_BASE}/user/onboarding`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          onboarding_completed: true,
        }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error("❌ Failed to complete onboarding:", error);
      throw error;
    }
  }
  /* ----------------------------------------
    SESSION PROGRESS ENDPOINTS
---------------------------------------- */
static async markSessionComplete(userId: string, sessionNumber: number) {
  const url = `${API_BASE}/session/complete?session_number=${sessionNumber}`;
  console.log("✅ Marking session complete:", url);

  try {
    const headers = await this.getAuthHeaders();
    const response = await fetch(url, {
      method: "POST",
      headers,
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error("❌ Failed to mark session complete:", error);
    throw error;
  }
}

static async getUserProgress(userId: string) {
  const url = `${API_BASE}/session/progress/${userId}`;
  console.log("📊 Fetching user progress:", url);

  try {
    const headers = await this.getAuthHeaders();
    const response = await fetch(url, { headers });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error("❌ Failed to fetch user progress:", error);
    return [];
  }
}

  /* ----------------------------------------
     CONVERSATION ENDPOINTS
  ---------------------------------------- */
  static async getConversations() {
    const headers = await this.getAuthHeaders();
    const response = await fetch(`${API_BASE}/chat/conversations`, { headers });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  }

  static async getConversation(conversationId: string) {
    const headers = await this.getAuthHeaders();
    const response = await fetch(`${API_BASE}/chat/conversation/${conversationId}`, { headers });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  }

  static async deleteConversation(conversationId: string) {
    const headers = await this.getAuthHeaders();
    const response = await fetch(`${API_BASE}/chat/conversation/${conversationId}`, {
      method: "DELETE",
      headers,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  }
}
