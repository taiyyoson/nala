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

export default function ChatScreen({ navigation }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);

  useEffect(() => {
    testBackendConnection();
  }, []);

  const testBackendConnection = async () => {
    console.log('Testing backend connection...');
    const isConnected = await chatAPI.testConnection();
    setBackendConnected(isConnected);
    
    if (isConnected) {
      console.log('Backend connected! Sending initial greeting...');
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
          </View>
          <View style={styles.headerSpacer} />
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
          editable={!isLoading && backendConnected !== false}
          returnKeyType="send"
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
    backgroundColor: '#F5F9F7',
  },
  header: {
    backgroundColor: 'rgb(72, 147, 95)',
    paddingTop: Platform.OS === 'ios' ? 50 : 20,
    paddingBottom: 20,
    paddingHorizontal: 20,
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
  headerSpacer: {
    width: 40,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 2,
  },
  subtitle: {
    fontSize: 14,
    color: '#fff',
    opacity: 0.9,
  },
  statusText: {
    fontSize: 12,
    marginTop: 4,
    color: '#fff',
    textAlign: 'center',
  },
  errorText: {
    color: 'rgb(248, 186, 32)',
  },
  successText: {
    color: 'rgba(255, 255, 255, 0.9)',
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
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
    backgroundColor: '#48935F',
  },
  nalaBubble: {
    backgroundColor: '#9ACDBF',
    borderWidth: 2,
    borderColor: 'rgb(154, 205, 191)',
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
    color: '#48935F',
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
    color: '#0B3D00',
    marginTop: 4,
  },
  userTimestamp: {
    color: 'rgba(255, 255, 255, 0.7)',
  },
  inputArea: {
    flexDirection: 'row',
    padding: 12,
    backgroundColor: '#fff',
    borderTopWidth: 2,
    borderTopColor: 'rgb(154, 205, 191)',
    gap: 8,
    marginBottom: 30,
  },
  input: {
    flex: 1,
    borderWidth: 2,
    borderColor: 'rgb(154, 205, 191)',
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 16,
    backgroundColor: '#F5F9F7',
    color: '#333',
  },
  sendButton: {
    backgroundColor: 'rgb(211, 104, 140)',
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#ccc',
  },
  sendButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 20,
  },
});