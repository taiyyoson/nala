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
  ActivityIndicator,
} from "react-native";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { RouteProp } from "@react-navigation/native";
import { MainStackParamList } from "../navigation/MainStack";
import { API_BASE } from "../services/ApiService";
import { getAuth } from "firebase/auth";

type ChatScreenNavigationProp = NativeStackNavigationProp<
  MainStackParamList,
  "Chat"
>;

type ChatScreenRouteProp = RouteProp<MainStackParamList, "Chat">;

type Props = {
  navigation: ChatScreenNavigationProp;
  route: ChatScreenRouteProp;
};

type Message = {
  id: number;
  sender: "nala" | "user";
  text: string;
  timestamp: Date;
  isLoading?: boolean;
};

function TypingIndicator() {
  const dot1 = useRef(new Animated.Value(0)).current;
  const dot2 = useRef(new Animated.Value(0)).current;
  const dot3 = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    [dot1, dot2, dot3].forEach((dot, i) => {
      Animated.loop(
        Animated.sequence([
          Animated.timing(dot, { toValue: 1, duration: 400, delay: i * 200, useNativeDriver: true }),
          Animated.timing(dot, { toValue: 0, duration: 400, useNativeDriver: true }),
        ])
      ).start();
    });
  }, []);

  return (
    <View style={styles.typingContainer}>
      {[dot1, dot2, dot3].map((dot, i) => (
        <Animated.View
          key={i}
          style={[
            styles.dot,
            {
              opacity: dot.interpolate({ inputRange: [0, 1], outputRange: [0.3, 1] }),
              transform: [
                { translateY: dot.interpolate({ inputRange: [0, 1], outputRange: [0, -4] }) },
              ],
            },
          ]}
        />
      ))}
    </View>
  );
}

export default function ChatScreen({ navigation, route }: Props) {
  const { sessionId, week } = route.params;
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);

  const [conversationId, setConversationId] = useState<string>("");
  const [sessionComplete, setSessionComplete] = useState(false);
  const [loadingCompletionStatus, setLoadingCompletionStatus] = useState(true);

  const userId = getAuth().currentUser?.uid;
  const hasInitialized = useRef(false);
  const scrollViewRef = useRef<ScrollView>(null);

  // 👉 Check real completion status
  useEffect(() => {
    const fetchCompletionStatus = async () => {
      try {
        console.log("📊 Fetching completion status from:", `${API_BASE}/session/progress/${userId}`);
        
        const res = await fetch(`${API_BASE}/session/progress/${userId}`);
        const data = await res.json();
        
        console.log("📥 Raw session_progress response:", data);
    
        const matchingSessions = data.filter((s: any) => s.session_number === week);
        console.log(`🔍 Sessions matching week ${week}:`, matchingSessions);
    
        const sessionCompleted = matchingSessions.some((s: any) => s.completed_at);
        console.log(
          sessionCompleted
            ? `✅ Session ${week} is marked complete`
            : `⚠️ Session ${week} is NOT complete`
        );
    
        if (sessionCompleted) {
          setSessionComplete(true);
        }
      } catch (err) {
        console.error("❌ Error checking session completion:", err);
      } finally {
        setLoadingCompletionStatus(false);
      }
    };

    fetchCompletionStatus();
  }, [week]);

  // 👉 Only trigger greeting if NOT completed
  useEffect(() => {
    if (hasInitialized.current) return;
    hasInitialized.current = true;

    const init = async () => {
      try {
        const res = await fetch(`${API_BASE}/health`);
        const isConnected = res.ok;
        setBackendConnected(isConnected);

        if (isConnected && !sessionComplete) {
          sendInitialGreeting("[START_SESSION]");
        }
      } catch {
        setBackendConnected(false);
      }
    };
    init();
  }, [sessionComplete]);

  // 🔹 (Placeholder for history fetch — once backend gives endpoint)
  useEffect(() => {
    if (sessionComplete) {
      console.log("🔐 Session is completed — would fetch history here instead of greeting.");
      // TODO: when backend endpoint exists:
      // fetchChatHistory();
    }
  }, [sessionComplete]);

  const sendInitialGreeting = async (message = "[START_SESSION]") => {
    try {
      setIsLoading(true);
      const placeholder: Message = {
        id: Date.now(),
        sender: "nala",
        text: "",
        timestamp: new Date(),
        isLoading: true,
      };
      setMessages([placeholder]);

      const res = await fetch(`${API_BASE}/chat/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          user_id: userId,
          session_number: week,
          conversation_id: conversationId || undefined,
        }),
      });

      const data = await res.json();
      if (data.conversation_id) setConversationId(data.conversation_id);

      setMessages([{ ...placeholder, text: data.response, isLoading: false }]);
    } finally {
      setIsLoading(false);
    }
  };

  const sendUserMessage = async () => {
    if (!input.trim() || isLoading || sessionComplete) return;

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
      const res = await fetch(`${API_BASE}/chat/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          user_id: userId,
          conversation_id: conversationId || undefined,
          session_number: week,
        }),
      });

      const data = await res.json();
      if (data.conversation_id) setConversationId(data.conversation_id);
      if (data.session_complete) {
        setSessionComplete(true);
        setTimeout(() => navigation.replace("ChatOverview"), 2000);
      }
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === nalaPlaceholder.id
            ? { ...msg, text: data.response, isLoading: false }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  if (loadingCompletionStatus) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#4A8B6F" />
        <Text>Checking session status...</Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === "ios" ? "padding" : "height"}>
      {/* 🔹 Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
          <Text style={styles.backArrow}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Week {week} Session</Text>
      </View>

      {/* 🔹 Banner if locked */}
      {sessionComplete && (
        <View style={styles.sessionCompleteBanner}>
          <Text style={styles.sessionCompleteText}>🎉 Session completed — chat locked.</Text>
        </View>
      )}

      {/* 🔹 Messages */}
      <ScrollView ref={scrollViewRef} style={styles.messagesContainer} contentContainerStyle={styles.messagesContent}>
        {messages.map((m) => (
          <View key={m.id} style={[styles.messageWrapper, m.sender === "user" ? styles.userMessageWrapper : styles.nalaMessageWrapper]}>
            <View style={[styles.messageBubble, m.sender === "user" ? styles.userBubble : styles.nalaBubble]}>
              <Text style={[styles.senderName, m.sender === "user" ? styles.userSenderName : styles.nalaSenderName]}>
                {m.sender === "user" ? "You" : "Nala"}
              </Text>
              {m.isLoading ? (
                <TypingIndicator />
              ) : (
                <Text style={[styles.messageText, m.sender === "user" && styles.userMessageText]}>{m.text}</Text>
              )}
            </View>
          </View>
        ))}
      </ScrollView>

      {/* 🔒 Disable input if locked */}
      {sessionComplete ? (
        <View style={styles.lockedContainer}>
          <Text style={styles.lockedText}>🔒 Chat is locked for this completed session.</Text>
        </View>
      ) : (
        <View style={styles.inputArea}>
          <TextInput
            style={styles.input}
            placeholder="Type your message..."
            value={input}
            onChangeText={setInput}
            editable={!isLoading}
          />
          <TouchableOpacity
            style={[styles.sendButton, (!input.trim() || isLoading) && styles.sendButtonDisabled]}
            disabled={!input.trim() || isLoading}
            onPress={sendUserMessage}
          >
            <Text style={styles.sendButtonText}>→</Text>
          </TouchableOpacity>
        </View>
      )}
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  lockedContainer: {
    padding: 20,
    alignItems: "center",
    borderTopWidth: 1,
    borderColor: "#ddd",
    backgroundColor: "#f2f2f2",
  },
  lockedText: {
    fontSize: 14,
    color: "#666",
    fontStyle: "italic",
  },
  sessionCompleteBanner: {
    backgroundColor: "#E8F5E9",
    padding: 12,
    alignItems: "center",
    borderBottomWidth: 1,
    borderColor: "#C8E6C9",
  },
  sessionCompleteText: {
    color: "#2E7D32",
    fontWeight: "600",
    fontSize: 14,
  },
  container: { flex: 1, backgroundColor: "#F9FAFB" },
  centered: { flex: 1, justifyContent: "center", alignItems: "center" },
  header: {
    backgroundColor: "#4A8B6F",
    paddingTop: Platform.OS === "ios" ? 55 : 30,
    paddingBottom: 18,
    paddingHorizontal: 20,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
    flexDirection: "row",
    alignItems: "center",
  },
  headerTitle: {
    left: 0,
    right: 0,
    position: "absolute",
    top: 65,
    textAlign: "center",
    fontSize: 20,
    fontWeight: "700",
    color: "#fff",
  },
  backButton: {
    padding: 10,
    zIndex: 10,
  },
  backArrow: {
    fontSize: 28,
    color: "#fff",
    fontWeight: "600",
  },
  messagesContainer: { flex: 1 },
  messagesContent: { padding: 14 },
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
  senderName: { fontWeight: "bold", fontSize: 14 },
  userSenderName: { color: "#fff" },
  nalaSenderName: { color: "#2E7D32" },
  messageText: { fontSize: 16, color: "#333" },
  userMessageText: { color: "#fff" },
  typingContainer: {
    flexDirection: "row",
    paddingVertical: 6,
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
    padding: 25,
    backgroundColor: "#fff",
   	borderTopWidth: 1,
    borderTopColor: "#ddd",
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#C8E6C9",
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: "#F9FAFB",
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
  sendButtonText: { color: "#fff", fontSize: 20 },
});
