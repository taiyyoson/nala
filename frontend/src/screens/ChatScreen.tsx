import React, { useState, useEffect, useRef } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Animated,
} from "react-native";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { MainStackParamList } from "../navigation/MainStack";

type ChatScreenNavigationProp = NativeStackNavigationProp<
  MainStackParamList,
  "Chat"
>;

type Props = {
  navigation: ChatScreenNavigationProp;
};

type Message = {
  id: number;
  sender: "nala" | "user";
  text: string;
  timestamp: Date;
  isLoading?: boolean;
};

// simple typing indicator animation
function TypingIndicator() {
  const dot1 = useRef(new Animated.Value(0)).current;
  const dot2 = useRef(new Animated.Value(0)).current;
  const dot3 = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const animateDot = (dot: Animated.Value, delay: number) => {
      Animated.loop(
        Animated.sequence([
          Animated.timing(dot, {
            toValue: 1,
            duration: 400,
            delay,
            useNativeDriver: true,
          }),
          Animated.timing(dot, {
            toValue: 0,
            duration: 400,
            useNativeDriver: true,
          }),
        ])
      ).start();
    };
    animateDot(dot1, 0);
    animateDot(dot2, 200);
    animateDot(dot3, 400);
  }, []);

  return (
    <View style={styles.typingContainer}>
      {[dot1, dot2, dot3].map((dot, i) => (
        <Animated.View
          key={i}
          style={[
            styles.dot,
            {
              opacity: dot.interpolate({
                inputRange: [0, 1],
                outputRange: [0.3, 1],
              }),
              transform: [
                {
                  translateY: dot.interpolate({
                    inputRange: [0, 1],
                    outputRange: [0, -4],
                  }),
                },
              ],
            },
          ]}
        />
      ))}
    </View>
  );
}

const chatAPI = {
  sendMessage: async (
    message: string,
    userId: string,
    conversationId?: string
  ) => {
    const res = await fetch("http://localhost:8000/api/v1/chat/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        user_id: userId,
        conversation_id: conversationId || undefined,
        session_number: 1,
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  },

  testConnection: async (): Promise<boolean> => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/health");
      return res.ok;
    } catch {
      return false;
    }
  },
};

export default function ChatScreen({ navigation }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);
  const [conversationId, setConversationId] = useState<string>("");

  const userId = "default_user";
  const hasInitialized = useRef(false);
  const scrollViewRef = useRef<ScrollView>(null);

  useEffect(() => {
    if (hasInitialized.current) return;
    hasInitialized.current = true;

    const init = async () => {
      const isConnected = await chatAPI.testConnection();
      setBackendConnected(isConnected);
      if (isConnected) sendInitialGreeting();
    };
    init();
  }, []);

  useEffect(() => {
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);
  }, [messages]);

  const sendInitialGreeting = async () => {
    try {
      setIsLoading(true);
      const nalaPlaceholder: Message = {
        id: Date.now(),
        sender: "nala",
        text: "",
        timestamp: new Date(),
        isLoading: true,
      };
      setMessages([nalaPlaceholder]);

      const data = await chatAPI.sendMessage("[START_SESSION]", userId, conversationId);
      setConversationId(data.conversation_id);

      setMessages([
        {
          ...nalaPlaceholder,
          text: data.response,
          isLoading: false,
          timestamp: new Date(),
        },
      ]);
    } catch (err) {
      console.error("Error initializing greeting:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const sendUserMessage = async () => {
    if (!input.trim() || isLoading) return;

    const text = input.trim();
    setInput("");
    const userMsg: Message = {
      id: Date.now(),
      sender: "user",
      text,
      timestamp: new Date(),
    };
    const nalaPlaceholder: Message = {
      id: Date.now() + 1,
      sender: "nala",
      text: "",
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages((prev) => [...prev, userMsg, nalaPlaceholder]);
    setIsLoading(true);

    try {
      const data = await chatAPI.sendMessage(text, userId, conversationId);
      if (data.conversation_id && data.conversation_id !== conversationId) {
        setConversationId(data.conversation_id);
      }

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === nalaPlaceholder.id
            ? { ...msg, text: data.response, isLoading: false }
            : msg
        )
      );
    } catch (err) {
      console.error("Send message error:", err);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === nalaPlaceholder.id
            ? { ...msg, text: "Error connecting to NALA.", isLoading: false }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: any) => {
    if (e.nativeEvent.key === "Enter" && !e.nativeEvent.shiftKey) {
      e.preventDefault();
      sendUserMessage();
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      keyboardVerticalOffset={Platform.OS === "ios" ? 90 : 0}
    >
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.backArrow}>←</Text>
        </TouchableOpacity>
        <View style={styles.headerTitles}>
          <Text style={styles.title}>Week 1 Session</Text>
        </View>
      </View>

      {/* Messages */}
      <ScrollView
        ref={scrollViewRef}
        style={styles.messagesContainer}
        contentContainerStyle={styles.messagesContent}
      >
        {messages.map((m) => (
          <View
            key={m.id}
            style={[
              styles.messageWrapper,
              m.sender === "user"
                ? styles.userMessageWrapper
                : styles.nalaMessageWrapper,
            ]}
          >
            <View
              style={[
                styles.messageBubble,
                m.sender === "user" ? styles.userBubble : styles.nalaBubble,
              ]}
            >
              <Text
                style={[
                  styles.senderName,
                  m.sender === "user"
                    ? styles.userSenderName
                    : styles.nalaSenderName,
                ]}
              >
                {m.sender === "user" ? "You" : "NALA"}
              </Text>
              {m.isLoading ? (
                <TypingIndicator />
              ) : (
                <Text
                  style={[
                    styles.messageText,
                    m.sender === "user" && styles.userMessageText,
                  ]}
                >
                  {m.text}
                </Text>
              )}
              <Text
                style={[
                  styles.timestamp,
                  m.sender === "user" && styles.userTimestamp,
                ]}
              >
                {m.timestamp.toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </Text>
            </View>
          </View>
        ))}
      </ScrollView>

      {/* Input */}
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
          multiline
          scrollEnabled={false}
          blurOnSubmit={false}
        />
        <TouchableOpacity
          style={[
            styles.sendButton,
            (isLoading || !input.trim() || backendConnected === false) &&
              styles.sendButtonDisabled,
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
  container: { flex: 1, backgroundColor: "#F9FAFB" },
  header: {
    backgroundColor: "#2E7D32",
    paddingTop: Platform.OS === "ios" ? 50 : 20,
    paddingBottom: 20,
    paddingHorizontal: 20,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
    flexDirection: "row",
    alignItems: "center",
  },
  backButton: { marginRight: 10 },
  backArrow: { fontSize: 28, color: "#fff", fontWeight: "600" },
  headerTitles: { flex: 1, alignItems: "center" },
  title: { fontSize: 20, fontWeight: "bold", color: "#fff" },
  messagesContainer: { flex: 1 },
  messagesContent: { padding: 16, flexGrow: 1 },
  messageWrapper: { marginBottom: 12, flexDirection: "row" },
  userMessageWrapper: { justifyContent: "flex-end" },
  nalaMessageWrapper: { justifyContent: "flex-start" },
  messageBubble: { maxWidth: "80%", padding: 12, borderRadius: 16 },
  userBubble: { backgroundColor: "#2E7D32" },
  nalaBubble: {
    backgroundColor: "#E8F5E9",
    borderWidth: 1,
    borderColor: "#C8E6C9",
  },
  senderName: { fontWeight: "bold", fontSize: 12, marginBottom: 4 },
  userSenderName: { color: "rgba(255, 255, 255, 0.9)" },
  nalaSenderName: { color: "#2E7D32" },
  messageText: { fontSize: 16, color: "#333", marginBottom: 4 },
  userMessageText: { color: "#fff" },
  timestamp: { fontSize: 10, color: "#4F4F4F", marginTop: 4 },
  userTimestamp: { color: "rgba(255, 255, 255, 0.7)" },
  typingContainer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 6,
    paddingHorizontal: 10,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#4A8B6F",
    marginHorizontal: 3,
  },
  inputArea: {
    flexDirection: "row",
    padding: 10,
    backgroundColor: "#fff",
    borderTopWidth: 1,
    borderTopColor: "#E0E0E0",
    alignItems: "flex-end",
    paddingBottom: 30,
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#C8E6C9",
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: Platform.OS === "ios" ? 12 : 8,
    fontSize: 16,
    backgroundColor: "#F9FAFB",
    color: "#333",
    minHeight: 44,
    maxHeight: 120,
  },
  sendButton: {
    backgroundColor: "#4CAF50",
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: "center",
    alignItems: "center",
    marginLeft: 8,
  },
  sendButtonDisabled: { backgroundColor: "#C8E6C9" },
  sendButtonText: { color: "#fff", fontWeight: "bold", fontSize: 20 },
});
