import React, { useState, useEffect } from "react";
import { 
  View, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  ScrollView, 
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator
} from "react-native";
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { MainStackParamList } from '../navigation/MainStack';

type ChatScreenNavigationProp = NativeStackNavigationProp<
  MainStackParamList,
  'Chat'
>;

type Props = {
  navigation: ChatScreenNavigationProp;
};

type Message = {
  id: number;
  sender: "nala" | "user";
  text: string;
  timestamp: Date;
};

// ✅ NEW: Updated response type to match backend
interface ChatResponse {
  response: string;
  conversation_id: string;
  message_id: string;
  timestamp: string;
  session_state?: string;
  session_data?: {
    current_goal?: string;
    smart_analysis?: any;
    confidence_level?: number;
    all_goals?: any[];
  };
  metadata?: any;
}

// ✅ UPDATED: chatAPI with all new parameters
const chatAPI = {
  sendMessage: async (
    message: string,
    userId: string,
    conversationId: string,
    conversationHistory: Message[]
  ): Promise<ChatResponse> => {
    try {
      console.log('Sending message to backend:', message);
      console.log('Conversation ID:', conversationId);
      console.log('User ID:', userId);
      
      // ✅ NEW: Format conversation history for backend
      const history = conversationHistory.map(msg => ({
        role: msg.sender === 'user' ? 'user' : 'assistant',
        content: msg.text,
      }));
      
      const response = await fetch('http://localhost:8000/api/v1/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: message,
          user_id: userId,  // ✅ NEW
          conversation_id: conversationId || undefined,  // ✅ NEW
          session_number: 1  // ✅ NEW: Tells backend to use Session 1 flow
        })
      });
      
      console.log('Backend response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Backend response data:', data);
      console.log('✅ Session state:', data.session_state);  // ✅ NEW: Log session state
      
      if (data.session_data?.current_goal) {
        console.log('🎯 Current goal:', data.session_data.current_goal);
      }
      
      return data;
    } catch (error) {
      console.error('Error sending message:', error);
      return {
        response: "I'm having trouble connecting to the backend. Make sure it's running on port 8000.",
        conversation_id: conversationId,
        message_id: "",
        timestamp: new Date().toISOString(),
        session_state: "error"
      };
    }
  },

  testConnection: async (): Promise<boolean> => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/health');
      return response.ok;
    } catch (error) {
      console.error('Backend health check failed:', error);
      return false;
    }
  },

  // ✅ NEW: Get session status for debugging
  getSessionStatus: async (conversationId: string) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/chat/session-status/${conversationId}`
      );
      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error('Failed to get session status:', error);
      return null;
    }
  },

  // ✅ NEW: Reset session for testing
  resetSession: async (conversationId: string) => {
    try {
      await fetch(
        `http://localhost:8000/api/v1/chat/reset-session/${conversationId}`,
        { method: 'POST' }
      );
      console.log('✅ Session reset');
    } catch (error) {
      console.error('Failed to reset session:', error);
    }
  }
};

export default function ChatScreen({ navigation }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);
  
  // ✅ NEW: Track conversation ID
  const [conversationId, setConversationId] = useState<string>("");
  
  // ✅ NEW: Track session state
  const [sessionState, setSessionState] = useState<string>("greetings");
  
  // ✅ NEW: Debug panel
  const [showDebug, setShowDebug] = useState(false);
  const [sessionDebug, setSessionDebug] = useState<any>(null);
  
  // ✅ NEW: Get user ID (replace with actual auth when ready)
  const userId = "default_user"; // TODO: Replace with actual Firebase user ID

  useEffect(() => {
    testBackendConnection();
  }, []);

  const testBackendConnection = async () => {
    console.log('Testing backend connection...');
    const isConnected = await chatAPI.testConnection();
    setBackendConnected(isConnected);
    
    if (isConnected) {
      console.log('✅ Backend connected! Sending initial greeting...');
      sendInitialGreeting();
    } else {
      console.log('❌ Backend not connected. Make sure to run: python dev.py');
    }
  };

  const sendInitialGreeting = async () => {
    setIsLoading(true);
    
    // ✅ UPDATED: Pass all required parameters
    const response = await chatAPI.sendMessage(
      "hello",
      userId,
      conversationId,
      []
    );
    
    // ✅ NEW: Store conversation ID from response
    if (response.conversation_id) {
      setConversationId(response.conversation_id);
      console.log('📝 Conversation ID:', response.conversation_id);
    }
    
    const nalaMessage: Message = {
      id: Date.now(),
      sender: "nala",
      text: response.response,
      timestamp: new Date()
    };

    setMessages([nalaMessage]);
    
    // ✅ NEW: Update session state
    if (response.session_state) {
      setSessionState(response.session_state);
    }
    
    setIsLoading(false);
  };

  const sendUserMessage = async () => {
    if (!input.trim() || isLoading) return;

    const messageText = input.trim();
    setInput("");  // ✅ Clear input immediately

    const userMessage: Message = {
      id: Date.now(),
      sender: "user",
      text: messageText,
      timestamp: new Date()
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setIsLoading(true);

    // ✅ UPDATED: Pass conversation ID and full history
    const response = await chatAPI.sendMessage(
      messageText,
      userId,
      conversationId,
      updatedMessages  // ✅ CHANGED: Pass updated messages with user's message
    );

    // ✅ NEW: Update conversation ID if it changed
    if (response.conversation_id && response.conversation_id !== conversationId) {
      setConversationId(response.conversation_id);
      console.log('📝 Updated Conversation ID:', response.conversation_id);
    }

    const nalaMessage: Message = {
      id: Date.now() + 1,
      sender: "nala",
      text: response.response,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, nalaMessage]);
    
    // ✅ NEW: Update session state
    if (response.session_state) {
      setSessionState(response.session_state);
      console.log('🔄 Session state changed to:', response.session_state);
    }
    
    setIsLoading(false);
  };

  const handleKeyPress = (e: any) => {
    if (e.nativeEvent.key === 'Enter' && !e.nativeEvent.shiftKey) {
      e.preventDefault();
      sendUserMessage();
    }
  };

  // ✅ NEW: Check session status for debugging
  const checkSessionStatus = async () => {
    if (!conversationId) {
      console.log('❌ No conversation ID yet');
      return;
    }
    const status = await chatAPI.getSessionStatus(conversationId);
    setSessionDebug(status);
    setShowDebug(true);
    console.log('📊 Session Status:', status);
  };

  // ✅ NEW: Reset session for testing
  const handleResetSession = async () => {
    if (!conversationId) return;
    await chatAPI.resetSession(conversationId);
    setMessages([]);
    setSessionState("greetings");
    setShowDebug(false);
    setConversationId("");
    sendInitialGreeting();
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <TouchableOpacity 
            style={styles.backButton}
            onPress={() => navigation.goBack()}
          >
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>
          <View style={styles.headerTitles}>
            <Text style={styles.title}>Week 1 Session</Text>
            {/* ✅ NEW: Show session state */}
            <Text style={styles.sessionState}>State: {sessionState}</Text>
          </View>
          {/* ✅ NEW: Debug button */}
          <TouchableOpacity 
            style={styles.debugButton}
            onPress={checkSessionStatus}
          >
            <Text style={styles.debugButtonText}>🔍</Text>
          </TouchableOpacity>
        </View>
        {backendConnected === null && (
          <Text style={styles.statusText}>Testing connection...</Text>
        )}
        {backendConnected === false && (
          <Text style={[styles.statusText, styles.errorText]}>
            ⚠️ Backend not connected
          </Text>
        )}
        {backendConnected === true && (
          <Text style={[styles.statusText, styles.successText]}>
            ✓ Connected
          </Text>
        )}
      </View>

      {/* ✅ NEW: Debug Panel */}
      {showDebug && sessionDebug && (
        <View style={styles.debugPanel}>
          <TouchableOpacity onPress={() => setShowDebug(false)}>
            <Text style={styles.closeDebug}>✕ Close</Text>
          </TouchableOpacity>
          <Text style={styles.debugText}>
            State: {sessionDebug.current_state || 'N/A'}
          </Text>
          <Text style={styles.debugText}>
            Turns: {sessionDebug.turn_count || 0}
          </Text>
          <Text style={styles.debugText}>
            Goal: {sessionDebug.current_goal || 'None'}
          </Text>
          {sessionDebug.smart_analysis && (
            <>
              <Text style={styles.debugText}>
                SMART: {sessionDebug.smart_analysis.is_smart ? '✓ Yes' : '✗ No'}
              </Text>
              {!sessionDebug.smart_analysis.is_smart && (
                <Text style={styles.debugText}>
                  Missing: {sessionDebug.smart_analysis.missing_criteria?.join(', ') || 'Unknown'}
                </Text>
              )}
            </>
          )}
          {sessionDebug.confidence_level && (
            <Text style={styles.debugText}>
              Confidence: {sessionDebug.confidence_level}/10
            </Text>
          )}
          <TouchableOpacity 
            style={styles.resetButton}
            onPress={handleResetSession}
          >
            <Text style={styles.resetButtonText}>🔄 Reset Session</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Messages */}
      <ScrollView 
        style={styles.messagesContainer}
        contentContainerStyle={styles.messagesContent}
      >
        {messages.map((message) => (
          <View 
            key={message.id} 
            style={[
              styles.messageWrapper,
              message.sender === 'user' ? styles.userMessageWrapper : styles.nalaMessageWrapper
            ]}
          >
            <View style={[
              styles.messageBubble,
              message.sender === 'user' ? styles.userBubble : styles.nalaBubble
            ]}>
              <Text style={[
                styles.senderName,
                message.sender === 'user' ? styles.userSenderName : styles.nalaSenderName
              ]}>
                {message.sender === 'user' ? 'You' : 'NALA'}
              </Text>
              <Text style={[
                styles.messageText,
                message.sender === 'user' && styles.userMessageText
              ]}>
                {message.text}
              </Text>
              <Text style={[
                styles.timestamp,
                message.sender === 'user' && styles.userTimestamp
              ]}>
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </Text>
            </View>
          </View>
        ))}
        
        {isLoading && (
          <View style={[styles.messageWrapper, styles.nalaMessageWrapper]}>
            <View style={[styles.messageBubble, styles.nalaBubble]}>
              <ActivityIndicator size="small" color="rgb(72, 147, 95)" />
              <Text style={styles.messageText}>NALA is typing...</Text>
            </View>
          </View>
        )}
      </ScrollView>

      {/* Input Area */}
      <View style={styles.inputArea}>
        <TextInput
          style={styles.input}
          placeholder="Type your message..."
          placeholderTextColor="#999"
          value={input}
          onChangeText={setInput}
          onSubmitEditing={sendUserMessage}   
          onKeyPress={handleKeyPress}           
          editable={!isLoading && backendConnected !== false}
          returnKeyType="send"
          multiline={true}              
          scrollEnabled={false}         
          blurOnSubmit={false}
          enablesReturnKeyAutomatically={true} 
        />
        <TouchableOpacity 
          style={[
            styles.sendButton,
            (isLoading || !input.trim() || backendConnected === false) && styles.sendButtonDisabled
          ]}
          onPress={sendUserMessage}
          disabled={isLoading || !input.trim() || backendConnected === false}
        >
          <Text style={styles.sendButtonText}>→</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB', 
  },
  header: {
    backgroundColor: '#2E7D32',
    paddingTop: Platform.OS === 'ios' ? 50 : 20,
    paddingBottom: 20,
    paddingHorizontal: 20,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
  },
  headerTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  backArrow: {
    fontSize: 28,
    color: '#fff',
    fontWeight: '600',
  },
  headerTitles: {
    marginTop: 20,
    flex: 1,
    alignItems: 'center',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 2,
  },
  // ✅ NEW: Session state style
  sessionState: {
    fontSize: 10,
    color: '#C8E6C9',
    fontStyle: 'italic',
  },
  // ✅ NEW: Debug button style
  debugButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  debugButtonText: {
    fontSize: 20,
  },
  headerSpacer: {
    width: 40,
  },
  statusText: {
    fontSize: 12,
    marginTop: 4,
    color: '#E8F5E9',
    textAlign: 'center',
  },
  errorText: {
    color: '#FBC02D',
  },
  successText: {
    color: '#C8E6C9',
  },
  // ✅ NEW: Debug panel styles
  debugPanel: {
    backgroundColor: '#FFF9E6',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#FFD700',
  },
  closeDebug: {
    textAlign: 'right',
    color: '#FF6B35',
    fontWeight: 'bold',
    marginBottom: 8,
  },
  debugText: {
    fontSize: 12,
    color: '#333',
    marginBottom: 4,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  resetButton: {
    backgroundColor: '#FF6B35',
    padding: 8,
    borderRadius: 8,
    marginTop: 8,
  },
  resetButtonText: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
    flexGrow: 1,
  },
  messageWrapper: {
    marginBottom: 12,
    flexDirection: 'row',
  },
  userMessageWrapper: {
    justifyContent: 'flex-end',
  },
  nalaMessageWrapper: {
    justifyContent: 'flex-start',
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
  },
  userBubble: {
    backgroundColor: '#2E7D32', 
  },
  nalaBubble: {
    backgroundColor: '#E8F5E9', 
    borderWidth: 1,
    borderColor: '#C8E6C9',
  },
  senderName: {
    fontWeight: 'bold',
    fontSize: 12,
    marginBottom: 4,
  },
  userSenderName: {
    color: 'rgba(255, 255, 255, 0.9)',
  },
  nalaSenderName: {
    color: '#2E7D32',
  },
  messageText: {
    fontSize: 16,
    color: '#333',
    marginBottom: 4,
  },
  userMessageText: {
    color: '#fff',
  },
  timestamp: {
    fontSize: 10,
    color: '#4F4F4F',
    marginTop: 4,
  },
  userTimestamp: {
    color: 'rgba(255, 255, 255, 0.7)',
  },
  inputArea: {
    flexDirection: 'row',
    padding: 10,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
    alignItems: 'flex-end',
    paddingBottom: 30,
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#C8E6C9',
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: Platform.OS === 'ios' ? 12 : 8,
    fontSize: 16,
    backgroundColor: '#F9FAFB',
    color: '#333',
    minHeight: 44,
    maxHeight: 120,
  },
  sendButton: {
    backgroundColor: '#4CAF50',
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  sendButtonDisabled: {
    backgroundColor: '#C8E6C9',
  },
  sendButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 20,
  },
});
