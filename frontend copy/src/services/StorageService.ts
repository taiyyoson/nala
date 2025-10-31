// src/services/StorageService.ts
import AsyncStorage from '@react-native-async-storage/async-storage';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

const STORAGE_KEYS = {
  CONVERSATION: 'nala_conversation',
  USER_PREFERENCES: 'nala_user_preferences',
};

export class StorageService {
  static async saveConversation(messages: Message[]) {
    try {
      const conversationData = JSON.stringify(messages);
      await AsyncStorage.setItem(STORAGE_KEYS.CONVERSATION, conversationData);
    } catch (error) {
      console.error('Error saving conversation:', error);
      throw error;
    }
  }

  static async getConversation(): Promise<Message[]> {
    try {
      const conversationData = await AsyncStorage.getItem(STORAGE_KEYS.CONVERSATION);
      if (conversationData) {
        const messages = JSON.parse(conversationData);
        return messages.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp),
        }));
      }
      return [];
    } catch (error) {
      console.error('Error loading conversation:', error);
      return [];
    }
  }

  static async clearConversation() {
    try {
      await AsyncStorage.removeItem(STORAGE_KEYS.CONVERSATION);
    } catch (error) {
      console.error('Error clearing conversation:', error);
      throw error;
    }
  }

  static async saveUserPreferences(preferences: any) {
    try {
      const preferencesData = JSON.stringify(preferences);
      await AsyncStorage.setItem(STORAGE_KEYS.USER_PREFERENCES, preferencesData);
    } catch (error) {
      console.error('Error saving user preferences:', error);
      throw error;
    }
  }

  static async getUserPreferences() {
    try {
      const preferencesData = await AsyncStorage.getItem(STORAGE_KEYS.USER_PREFERENCES);
      return preferencesData ? JSON.parse(preferencesData) : {};
    } catch (error) {
      console.error('Error loading user preferences:', error);
      return {};
    }
  }
}