import React, { useState, useEffect, useCallback } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
  Alert,
  Platform,
} from "react-native";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { MainStackParamList } from "../navigation/MainStack";
import { ApiService } from "../services/ApiService";
import { useAuth } from "../contexts/AuthContext";
import { useTextSize } from "../contexts/TextSizeContext";
import { getAuth } from "firebase/auth";

type Nav = NativeStackNavigationProp<MainStackParamList, "Conversations">;
type Props = { navigation: Nav };

interface Conversation {
  id: string;
  title: string | null;
  session_number: number;
  message_count: number;
  created_at: string;
  updated_at: string;
}

interface SessionProgress {
  session_number: number;
  completed_at?: string | null;
  unlocked_at?: string | null;
}

const SESSION_TITLES: Record<number, string> = {
  1: "Getting to know you",
  2: "Building habits",
  3: "Overcoming challenges",
  4: "Reviewing progress",
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function ConversationsScreen({ navigation }: Props) {
  const { logout } = useAuth();
  const { size } = useTextSize();
  const fontScale = size === "small" ? 14 : size === "medium" ? 16 : 20;

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [progress, setProgress] = useState<SessionProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const uid = getAuth().currentUser?.uid;
      const [convData, progressData] = await Promise.all([
        ApiService.getConversations(),
        uid ? ApiService.getUserProgress(uid) : Promise.resolve([]),
      ]);
      setConversations(convData.conversations ?? []);
      setProgress(progressData ?? []);
    } catch (err) {
      console.error("Failed to load data:", err);
      Alert.alert("Error", "Could not load your data. Pull to refresh.");
    }
  }, []);

  useEffect(() => {
    fetchData().finally(() => setLoading(false));
  }, [fetchData]);

  // Re-fetch when screen comes into focus (e.g. after completing a session)
  useEffect(() => {
    const unsubscribe = navigation.addListener("focus", () => {
      fetchData();
    });
    return unsubscribe;
  }, [navigation, fetchData]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  }, [fetchData]);

  // Compute journey status
  const completedSessions = progress.filter((p) => p.completed_at).length;
  const nextSession = completedSessions < 4 ? completedSessions + 1 : null;
  const journeyComplete = completedSessions === 4;

  // Get the most recent conversation per session (for viewing past chats)
  const latestConversationBySession = useCallback(
    (sessionNum: number): Conversation | undefined =>
      conversations
        .filter((c) => c.session_number === sessionNum)
        .sort(
          (a, b) =>
            new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        )[0],
    [conversations]
  );

  const isSessionComplete = (sessionNum: number): boolean =>
    !!progress.find((p) => p.session_number === sessionNum && p.completed_at);

  const handleContinueJourney = () => {
    navigation.navigate("ChatOverview");
  };

  const handleViewSession = (sessionNum: number) => {
    const conv = latestConversationBySession(sessionNum);
    if (conv) {
      navigation.navigate("Chat", {
        sessionId: sessionNum.toString(),
        week: sessionNum,
        sessionNumber: sessionNum,
        conversationId: conv.id,
        readOnly: true,
      });
    }
  };

  const handleDeleteConversation = (conv: Conversation) => {
    Alert.alert(
      "Delete Conversation",
      `Delete this Week ${conv.session_number} chat? This cannot be undone.`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            try {
              await ApiService.deleteConversation(conv.id);
              setConversations((prev) => prev.filter((c) => c.id !== conv.id));
            } catch {
              Alert.alert("Error", "Could not delete the conversation.");
            }
          },
        },
      ]
    );
  };

  // Build list data: journey card + past session entries
  type ListItem =
    | { kind: "journey" }
    | { kind: "sectionHeader" }
    | { kind: "session"; sessionNumber: number; conversation: Conversation }
    | { kind: "empty" };

  const listData: ListItem[] = [{ kind: "journey" }];

  // Add past sessions section if any conversations exist
  const sessionsWithChats = [1, 2, 3, 4].filter(
    (n) => latestConversationBySession(n) !== undefined
  );

  if (sessionsWithChats.length > 0) {
    listData.push({ kind: "sectionHeader" });
    sessionsWithChats.forEach((n) => {
      const conv = latestConversationBySession(n)!;
      listData.push({ kind: "session", sessionNumber: n, conversation: conv });
    });
  } else if (!loading) {
    listData.push({ kind: "sectionHeader" });
    listData.push({ kind: "empty" });
  }

  const renderItem = ({ item }: { item: ListItem }) => {
    if (item.kind === "journey") {
      return (
        <View style={styles.journeyCard}>
          <Text style={[styles.journeyTitle, { fontSize: fontScale + 4 }]}>
            Your Wellness Journey
          </Text>
          <Text style={[styles.journeySubtitle, { fontSize: fontScale - 2 }]}>
            {journeyComplete
              ? "All 4 sessions complete!"
              : `${completedSessions} of 4 sessions complete`}
          </Text>

          {/* Progress dots */}
          <View style={styles.progressDots}>
            {[1, 2, 3, 4].map((n) => (
              <View
                key={n}
                style={[
                  styles.progressDot,
                  isSessionComplete(n)
                    ? styles.progressDotComplete
                    : n === nextSession
                      ? styles.progressDotActive
                      : styles.progressDotPending,
                ]}
              >
                <Text style={styles.progressDotText}>{n}</Text>
              </View>
            ))}
          </View>

          {/* Progress bar */}
          <View style={styles.progressBarBg}>
            <View
              style={[
                styles.progressBarFill,
                { width: `${(completedSessions / 4) * 100}%` },
              ]}
            />
          </View>

          <TouchableOpacity
            style={styles.continueButton}
            onPress={handleContinueJourney}
            activeOpacity={0.85}
          >
            <Text style={[styles.continueButtonText, { fontSize: fontScale }]}>
              {completedSessions === 0
                ? "Start Your Journey"
                : journeyComplete
                  ? "View Sessions"
                  : "Continue"}
            </Text>
          </TouchableOpacity>
        </View>
      );
    }

    if (item.kind === "sectionHeader") {
      return (
        <Text style={[styles.sectionTitle, { fontSize: fontScale }]}>
          Past Sessions
        </Text>
      );
    }

    if (item.kind === "empty") {
      return (
        <View style={styles.emptyState}>
          <Text style={[styles.emptyText, { fontSize: fontScale - 2 }]}>
            No past sessions yet. Start your journey above!
          </Text>
        </View>
      );
    }

    // kind === "session"
    const { sessionNumber, conversation } = item;
    const completed = isSessionComplete(sessionNumber);
    return (
      <TouchableOpacity
        style={styles.sessionCard}
        onPress={() => handleViewSession(sessionNumber)}
        onLongPress={() => handleDeleteConversation(conversation)}
        activeOpacity={0.85}
      >
        <View style={styles.sessionCardLeft}>
          <View
            style={[
              styles.weekBadge,
              { backgroundColor: completed ? "#4A8B6F" : "#BF5F83" },
            ]}
          >
            <Text style={[styles.weekBadgeText, { fontSize: fontScale - 4 }]}>
              Week {sessionNumber}
            </Text>
          </View>
          <View style={styles.sessionCardBody}>
            <Text
              style={[styles.sessionCardTitle, { fontSize: fontScale }]}
              numberOfLines={1}
            >
              {SESSION_TITLES[sessionNumber]}
            </Text>
            <Text
              style={[styles.sessionCardMeta, { fontSize: fontScale - 4 }]}
            >
              {formatDate(conversation.updated_at)} ·{" "}
              {conversation.message_count} message
              {conversation.message_count !== 1 ? "s" : ""}
            </Text>
          </View>
        </View>
        <Text style={[styles.sessionChevron, { fontSize: fontScale + 2 }]}>
          ›
        </Text>
      </TouchableOpacity>
    );
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#4A8B6F" />
        <Text style={[styles.loadingText, { fontSize: fontScale - 2 }]}>
          Loading...
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.headerIconButton}
          onPress={logout}
          accessibilityLabel="Log out"
        >
          <Text style={styles.headerIcon}>←</Text>
        </TouchableOpacity>

        <View style={styles.headerCenter}>
          <Text style={[styles.headerTitle, { fontSize: fontScale + 4 }]}>
            Nala
          </Text>
          <Text style={[styles.headerSubtitle, { fontSize: fontScale - 4 }]}>
            Your wellness coach
          </Text>
        </View>

        <TouchableOpacity
          style={styles.headerIconButton}
          onPress={() => navigation.navigate("Settings")}
          accessibilityLabel="Open settings"
        >
          <Text style={styles.headerIcon}>⚙</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={listData}
        keyExtractor={(_, i) => i.toString()}
        renderItem={renderItem}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor="#4A8B6F"
            colors={["#4A8B6F"]}
          />
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F5F9F7" },
  centered: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    gap: 12,
  },
  loadingText: { color: "#555" },

  // Header
  header: {
    backgroundColor: "#4A8B6F",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingTop: Platform.OS === "ios" ? 60 : 32,
    paddingBottom: 20,
    paddingHorizontal: 20,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
  },
  headerCenter: { alignItems: "center", flex: 1 },
  headerTitle: { color: "#FFF", fontWeight: "700" },
  headerSubtitle: { color: "rgba(255,255,255,0.75)", marginTop: 2 },
  headerIconButton: {
    padding: 8,
    borderRadius: 20,
    minWidth: 40,
    alignItems: "center",
  },
  headerIcon: { color: "#FFF", fontSize: 22, fontWeight: "600" },

  listContent: { padding: 20, paddingBottom: 60 },

  // Journey card
  journeyCard: {
    backgroundColor: "#FFF",
    borderRadius: 20,
    padding: 24,
    marginBottom: 24,
    shadowColor: "#000",
    shadowOpacity: 0.08,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 12,
    elevation: 4,
    borderWidth: 1,
    borderColor: "#E8F5E9",
  },
  journeyTitle: { color: "#1A3D2E", fontWeight: "700", marginBottom: 4 },
  journeySubtitle: { color: "#6B8F7E", marginBottom: 16 },

  progressDots: {
    flexDirection: "row",
    justifyContent: "center",
    gap: 16,
    marginBottom: 12,
  },
  progressDot: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: "center",
    alignItems: "center",
  },
  progressDotComplete: { backgroundColor: "#4A8B6F" },
  progressDotActive: {
    backgroundColor: "#FFF",
    borderWidth: 2,
    borderColor: "#4A8B6F",
  },
  progressDotPending: { backgroundColor: "#E0E0E0" },
  progressDotText: { color: "#FFF", fontWeight: "700", fontSize: 14 },

  progressBarBg: {
    height: 6,
    backgroundColor: "#E8F5E9",
    borderRadius: 3,
    marginBottom: 20,
    overflow: "hidden",
  },
  progressBarFill: {
    height: "100%",
    backgroundColor: "#4A8B6F",
    borderRadius: 3,
  },

  continueButton: {
    backgroundColor: "#4A8B6F",
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: "center",
  },
  continueButtonText: { color: "#FFF", fontWeight: "700" },

  // Section
  sectionTitle: {
    color: "#2E5D4B",
    fontWeight: "700",
    marginBottom: 12,
  },

  // Session card
  sessionCard: {
    backgroundColor: "#FFF",
    borderRadius: 14,
    marginBottom: 10,
    paddingHorizontal: 16,
    paddingVertical: 14,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 2,
    borderLeftWidth: 3,
    borderLeftColor: "#4A8B6F",
  },
  sessionCardLeft: { flexDirection: "row", alignItems: "center", flex: 1 },
  weekBadge: {
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 4,
    marginRight: 12,
  },
  weekBadgeText: { color: "#FFF", fontWeight: "600" },
  sessionCardBody: { flex: 1 },
  sessionCardTitle: { color: "#1A3D2E", fontWeight: "600", marginBottom: 2 },
  sessionCardMeta: { color: "#6B8F7E" },
  sessionChevron: { color: "#4A8B6F", fontWeight: "700" },

  // Empty
  emptyState: { paddingVertical: 24, alignItems: "center" },
  emptyText: { color: "#9BBCB0", fontStyle: "italic", textAlign: "center" },
});
