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
import { useTextSize } from "../contexts/TextSizeContext";

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

  // ⭐ TEXT SIZE
  const { size } = useTextSize();
  const fontScale = size === "small" ? 14 : size === "medium" ? 16 : 20;

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

  // Fetch completion status
  useEffect(() => {
    const fetchCompletionStatus = async () => {
      try {
        const res = await fetch(`${API_BASE}/session/progress/${userId}`);
        const data = await res.json();

        const matching = data.filter((s: any) => s.session_number === week);
        const isCompleted = matching.some((s: any) => s.completed_at);

        setSessionComplete(isCompleted);
      } catch (err) {
        console.error(err);
      } finally {
        setLoadingCompletionStatus(false);
      }
    };

    fetchCompletionStatus();
  }, [week]);

  // Initial greeting
  useEffect(() => {
    if (hasInitialized.current) return;
    hasInitialized.current = true;

    const init = async () => {
      try {
        const res = await fetch(`${API_BASE}/health`);
        const ok = res.ok;
        setBackendConnected(ok);

        if (ok && !sessionComplete) {
          sendInitialGreeting("[START_SESSION]");
        }
      } catch {
        setBackendConnected(false);
      }
    };
    init();
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

    const loadingMsg: Message = {
      id: Date.now() + 1,
      sender: "nala",
      text: "",
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages((prev) => [...prev, userMsg, loadingMsg]);
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
        setTimeout(() => navigation.replace("ChatOverview"), 1800);
      }

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === loadingMsg.id
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
        <Text style={{ fontSize: fontScale }}>Checking session status...</Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      {/* HEADER */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
          <Text style={[styles.backArrow, { fontSize: fontScale + 6 }]}>←</Text>
        </TouchableOpacity>

        <Text style={[styles.headerTitle, { fontSize: fontScale + 2 }]}>
          Week {week} Session
        </Text>
      </View>

      {/* COMPLETION BANNER */}
      {sessionComplete && (
        <View style={styles.sessionCompleteBanner}>
          <Text style={[styles.sessionCompleteText, { fontSize: fontScale }]}>
            🎉 Session completed — chat locked.
          </Text>
        </View>
      )}

      {/* MESSAGES */}
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
              {/* Sender label */}
              <Text
                style={[
                  styles.senderName,
                  m.sender === "user"
                    ? styles.userSenderName
                    : styles.nalaSenderName,
                  { fontSize: fontScale - 2 },
                ]}
              >
                {m.sender === "user" ? "You" : "Nala"}
              </Text>

              {/* Text or typing indicator */}
              {m.isLoading ? (
                <TypingIndicator />
              ) : (
                <Text
                  style={[
                    styles.messageText,
                    m.sender === "user" && styles.userMessageText,
                    { fontSize: fontScale },
                  ]}
                >
                  {m.text}
                </Text>
              )}
            </View>
          </View>
        ))}
      </ScrollView>

      {/* INPUT AREA */}
      {sessionComplete ? (
        <View style={styles.lockedContainer}>
          <Text style={[styles.lockedText, { fontSize: fontScale }]}>
            🔒 Chat is locked for this completed session.
          </Text>
        </View>
      ) : (
        <View style={styles.inputArea}>
          <TextInput
            style={[styles.input, { fontSize: fontScale }]}
            placeholder="Type your message..."
            value={input}
            onChangeText={setInput}
            editable={!isLoading}
          />

          <TouchableOpacity
            style={[
              styles.sendButton,
              (!input.trim() || isLoading) && styles.sendButtonDisabled,
            ]}
            disabled={!input.trim() || isLoading}
            onPress={sendUserMessage}
          >
            <Text style={[styles.sendButtonText, { fontSize: fontScale + 2 }]}>
              →
            </Text>
          </TouchableOpacity>
        </View>
      )}
    </KeyboardAvoidingView>
  );
}

/* STYLES — unchanged except fontScale is added dynamically */
const styles = StyleSheet.create({
  lockedContainer: {
    padding: 20,
    alignItems: "center",
    borderTopWidth: 1,
    borderColor: "#ddd",
    backgroundColor: "#f2f2f2",
  },
  lockedText: { color: "#666", fontStyle: "italic" },
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
  },
  container: { flex: 1, backgroundColor: "#F5F9F7" },
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
    fontWeight: "700",
    color: "#fff",
  },
  backButton: { padding: 10, zIndex: 10 },
  backArrow: { color: "#fff", fontWeight: "600" },

  messagesContainer: { flex: 1 },
  messagesContent: { padding: 14 },

  messageWrapper: { marginBottom: 12, flexDirection: "row" },
  userMessageWrapper: { justifyContent: "flex-end" },
  nalaMessageWrapper: { justifyContent: "flex-start" },

  messageBubble: { maxWidth: "80%", padding: 12, borderRadius: 16 },
  userBubble: { backgroundColor: "#2E7D32" },
  nalaBubble: { backgroundColor: "#E8F5E9", borderWidth: 1, borderColor: "#C8E6C9" },

  senderName: { fontWeight: "bold" },
  userSenderName: { color: "#fff" },
  nalaSenderName: { color: "#2E7D32" },

  messageText: { color: "#333" },
  userMessageText: { color: "#fff" },

  typingContainer: { flexDirection: "row", paddingVertical: 6 },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: "#4A8B6F", marginHorizontal: 3 },

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
  sendButtonText: { color: "#fff" },
});
