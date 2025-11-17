// src/services/ApiService.ts

const BASE_URL = "http://127.0.0.1:8000";
export const API_BASE = `${BASE_URL}/api/v1`;

export class ApiService {

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


  static async sendMessage(message: string) {
    try {
      const response = await fetch(`${API_BASE}/chat/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error("❌ Chat message failed:", error);
      throw error;
    }
  }


  static async getUserStatus(userId: string) {
    try {
      const response = await fetch(`${API_BASE}/user/status/${userId}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error("❌ Failed to fetch user status:", error);
      return null;
    }
  }

  static async completeOnboarding(userId: string) {
    try {
      const response = await fetch(`${API_BASE}/user/onboarding`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
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
  const url = `${API_BASE}/session/complete?user_id=${userId}&session_number=${sessionNumber}`;
  console.log("✅ Marking session complete:", url);

  try {
    const response = await fetch(url, {
      method: "POST",
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
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error("❌ Failed to fetch user progress:", error);
    return [];
  }
}
}
