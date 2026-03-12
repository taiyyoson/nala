import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Alert,
} from "react-native";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { MainStackParamList } from "../navigation/MainStack";
import { getAuth } from "firebase/auth";
import { ApiService } from "../services/ApiService";
import { CheckCircle2, Calendar, MessageCircleQuestionMark } from "lucide-react-native";
import { useTextSize } from "../contexts/TextSizeContext";

type Nav = NativeStackNavigationProp<MainStackParamList, "ChatOverview">;
type Props = { navigation: Nav };

interface SessionProgress {
  session_number: number;
  completed_at?: string | null;
  unlocked_at?: string | null;
}

interface Conversation {
  id: string;
  session_number: number;
  updated_at: string;
}

const SESSIONS = [
  { id: 1, title: "Getting to know you" },
  { id: 2, title: "Building habits" },
  { id: 3, title: "Overcoming challenges" },
  { id: 4, title: "Reviewing progress" },
];

export default function ChatOverviewScreen({ navigation }: Props) {
  const { size } = useTextSize();
  const fontScale = size === "small" ? 14 : size === "medium" ? 16 : 20;

  const [progress, setProgress] = useState<SessionProgress[]>([]);
  const [conversationMap, setConversationMap] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const uid = getAuth().currentUser?.uid;
      if (!uid) throw new Error("Not logged in");

      const [progressData, convData] = await Promise.all([
        ApiService.getUserProgress(uid),
        ApiService.getConversations(),
      ]);

      setProgress(progressData ?? []);

      // Map: session_number → most recent conversation ID
      const convs: Conversation[] = convData.conversations ?? [];
      const map: Record<number, string> = {};
      convs.forEach((c) => {
        if (
          !map[c.session_number] ||
          new Date(c.updated_at) >
            new Date(
              convs.find((x) => x.id === map[c.session_number])?.updated_at ?? 0
            )
        ) {
          map[c.session_number] = c.id;
        }
      });
      setConversationMap(map);
    } catch (error) {
      console.error("Failed to fetch data:", error);
      Alert.alert("Error", "Couldn't load your session progress.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Re-fetch when screen comes into focus
  useEffect(() => {
    const unsubscribe = navigation.addListener("focus", () => {
      fetchData();
    });
    return unsubscribe;
  }, [navigation, fetchData]);

  const isSessionComplete = (num: number): boolean =>
    !!progress.find((p) => p.session_number === num && p.completed_at);

  const handleSessionPress = (sessionId: number) => {
    const completed = isSessionComplete(sessionId);
    const convId = conversationMap[sessionId];

    if (completed && convId) {
      // View past chat read-only
      navigation.navigate("Chat", {
        sessionId: sessionId.toString(),
        week: sessionId,
        sessionNumber: sessionId,
        conversationId: convId,
        readOnly: true,
      });
    } else {
      // Start or continue this session
      navigation.navigate("Chat", {
        sessionId: sessionId.toString(),
        week: sessionId,
        sessionNumber: sessionId,
        conversationId: convId,
      });
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color="#4A8B6F" size="large" />
        <Text style={{ marginTop: 8, color: "#555" }}>
          Loading your progress...
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          onPress={() => navigation.navigate("Conversations")}
          style={styles.headerIconButton}
          activeOpacity={0.7}
        >
          <Text style={styles.backArrow}>←</Text>
        </TouchableOpacity>

        <View>
          <Text style={[styles.headerTitle, { fontSize: fontScale + 4 }]}>
            Your Journey
          </Text>
          <Text style={[styles.headerSubtitle, { fontSize: fontScale - 2 }]}>
            4-week wellness coaching program
          </Text>
        </View>

        <TouchableOpacity
          onPress={() => navigation.navigate("Settings")}
          style={styles.headerIconButton}
        >
          <MessageCircleQuestionMark color="#fff" size={22} />
        </TouchableOpacity>
      </View>

      {/* Sessions */}
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {SESSIONS.map((session) => {
          const completed = isSessionComplete(session.id);
          const hasConversation = !!conversationMap[session.id];
          const cardColor = completed ? "#4A8B6F" : "#BF5F83";

          return (
            <TouchableOpacity
              key={session.id}
              style={[styles.sessionCard, { backgroundColor: cardColor }]}
              activeOpacity={0.9}
              onPress={() => handleSessionPress(session.id)}
            >
              {/* Top-right icon */}
              <View style={styles.iconContainer}>
                {completed ? (
                  <CheckCircle2 color="#FFF" size={22} />
                ) : (
                  <Calendar color="#FFF" size={22} />
                )}
              </View>

              {/* Week badge */}
              <View style={styles.weekBadge}>
                <Text
                  style={[styles.weekBadgeText, { fontSize: fontScale - 2 }]}
                >
                  Week {session.id}
                </Text>
              </View>

              {/* Title */}
              <Text
                style={[
                  styles.sessionDescription,
                  { fontSize: fontScale, fontWeight: "500" },
                ]}
              >
                {completed ? "Completed" : session.title}
              </Text>

              {/* Footer */}
              {completed && hasConversation ? (
                <View style={styles.sessionFooter}>
                  <Text style={[styles.sessionFooterText, { fontSize: fontScale - 4 }]}>
                    Tap to view chat
                  </Text>
                </View>
              ) : !completed ? (
                <View style={styles.sessionFooter}>
                  <Calendar size={14} color="rgba(255,255,255,0.8)" />
                  <Text style={[styles.sessionFooterText, { fontSize: fontScale - 4 }]}>
                    10-min check-in
                  </Text>
                </View>
              ) : null}
            </TouchableOpacity>
          );
        })}

        {/* Encouragement */}
        <View style={styles.motivationCard}>
          <Text style={[styles.motivationText, { fontSize: fontScale - 2 }]}>
            {progress.filter((p) => p.completed_at).length === 4
              ? "Amazing work! You've completed all sessions."
              : "Keep it up! Complete your next session."}
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F5F9F7" },
  header: {
    backgroundColor: "#4A8B6F",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingTop: 60,
    paddingBottom: 24,
    paddingHorizontal: 24,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
  },
  headerTitle: { color: "#FFF", fontSize: 22, fontWeight: "700" },
  headerSubtitle: { color: "rgba(255,255,255,0.8)", fontSize: 13 },
  backArrow: { fontSize: 24, color: "#FFF", fontWeight: "600" },
  headerIconButton: { padding: 8, borderRadius: 20 },
  scrollContent: { padding: 20, gap: 16, paddingBottom: 60 },
  sessionCard: {
    borderRadius: 24,
    padding: 16,
    minHeight: 120,
    justifyContent: "flex-start",
    shadowColor: "#000",
    shadowOpacity: 0.1,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 6,
    elevation: 3,
  },
  iconContainer: { position: "absolute", top: 16, right: 16 },
  weekBadge: {
    alignSelf: "flex-start",
    borderRadius: 16,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginBottom: 8,
    backgroundColor: "rgba(255,255,255,0.3)",
  },
  weekBadgeText: { color: "#FFF", fontWeight: "500" },
  sessionDescription: { color: "#FFF", marginBottom: 8 },
  sessionFooter: { flexDirection: "row", alignItems: "center", gap: 6 },
  sessionFooterText: { color: "rgba(255,255,255,0.8)", fontSize: 12 },
  motivationCard: {
    backgroundColor: "#FEF3E2",
    borderRadius: 16,
    padding: 16,
    marginTop: 8,
  },
  motivationText: { color: "#4A4A4A", fontSize: 13, textAlign: "center" },
  centered: { flex: 1, justifyContent: "center", alignItems: "center" },
});
