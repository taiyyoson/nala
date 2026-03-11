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
import { useTextSize } from "../contexts/TextSizeContext";

type ConversationsScreenNavigationProp = NativeStackNavigationProp<
  MainStackParamList,
  "Conversations"
>;

type Props = {
  navigation: ConversationsScreenNavigationProp;
};

interface Conversation {
  id: string;
  title: string | null;
  session_number: number;
  message_count: number;
  created_at: string;
  updated_at: string;
}

// Groups conversations 1-4 matching the 4-session program
const WEEKS = [1, 2, 3, 4] as const;

const WEEK_LABELS: Record<number, string> = {
  1: "Week 1 — Getting to know you",
  2: "Week 2 — Building habits",
  3: "Week 3 — Overcoming challenges",
  4: "Week 4 — Reviewing progress",
};

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function ConversationsScreen({ navigation }: Props) {
  const { size } = useTextSize();
  const fontScale = size === "small" ? 14 : size === "medium" ? 16 : 20;

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  // Track which week sections are expanded (all open by default)
  const [expandedWeeks, setExpandedWeeks] = useState<Set<number>>(
    new Set(WEEKS)
  );

  const fetchConversations = useCallback(async () => {
    try {
      const data = await ApiService.getConversations();
      setConversations(data.conversations ?? []);
    } catch (err) {
      console.error("Failed to fetch conversations:", err);
      Alert.alert("Error", "Could not load your conversations. Please try again.");
    }
  }, []);

  useEffect(() => {
    fetchConversations().finally(() => setLoading(false));
  }, [fetchConversations]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchConversations();
    setRefreshing(false);
  }, [fetchConversations]);

  const toggleWeek = useCallback((week: number) => {
    setExpandedWeeks((prev) => {
      const next = new Set(prev);
      if (next.has(week)) {
        next.delete(week);
      } else {
        next.add(week);
      }
      return next;
    });
  }, []);

  const handleOpenConversation = useCallback(
    (conversation: Conversation) => {
      navigation.navigate("Chat", {
        sessionId: conversation.session_number.toString(),
        week: conversation.session_number,
        sessionNumber: conversation.session_number,
        conversationId: conversation.id,
        readOnly: true,
      });
    },
    [navigation]
  );

  const handleNewChat = useCallback(
    (week: number) => {
      navigation.navigate("Chat", {
        sessionId: week.toString(),
        week,
        sessionNumber: week,
      });
    },
    [navigation]
  );

  const handleDeleteConversation = useCallback(
    (conversation: Conversation) => {
      Alert.alert(
        "Delete Conversation",
        `Delete "${conversation.title ?? `Session ${conversation.session_number} Chat`}"? This cannot be undone.`,
        [
          { text: "Cancel", style: "cancel" },
          {
            text: "Delete",
            style: "destructive",
            onPress: async () => {
              try {
                await ApiService.deleteConversation(conversation.id);
                setConversations((prev) =>
                  prev.filter((c) => c.id !== conversation.id)
                );
              } catch (err) {
                console.error("Failed to delete conversation:", err);
                Alert.alert("Error", "Could not delete the conversation.");
              }
            },
          },
        ]
      );
    },
    []
  );

  const conversationsByWeek = useCallback(
    (week: number): Conversation[] =>
      conversations
        .filter((c) => c.session_number === week)
        .sort(
          (a, b) =>
            new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        ),
    [conversations]
  );

  // Each section header + its conversation cards are rendered as FlatList items
  // so we get pull-to-refresh and scroll for free without nesting ScrollViews.
  type ListItem =
    | { kind: "header"; week: number }
    | { kind: "conversation"; conversation: Conversation; week: number }
    | { kind: "empty"; week: number }
    | { kind: "newChat"; week: number };

  const listData: ListItem[] = WEEKS.flatMap((week) => {
    const items: ListItem[] = [{ kind: "header", week }];
    if (expandedWeeks.has(week)) {
      const weekConvos = conversationsByWeek(week);
      if (weekConvos.length === 0) {
        items.push({ kind: "empty", week });
      } else {
        weekConvos.forEach((c) =>
          items.push({ kind: "conversation", conversation: c, week })
        );
      }
      items.push({ kind: "newChat", week });
    }
    return items;
  });

  const renderItem = useCallback(
    ({ item }: { item: ListItem }) => {
      if (item.kind === "header") {
        const isExpanded = expandedWeeks.has(item.week);
        const count = conversationsByWeek(item.week).length;
        return (
          <TouchableOpacity
            style={styles.sectionHeader}
            onPress={() => toggleWeek(item.week)}
            activeOpacity={0.8}
            accessibilityRole="button"
            accessibilityLabel={`${WEEK_LABELS[item.week]}, ${count} conversation${count !== 1 ? "s" : ""}, ${isExpanded ? "expanded" : "collapsed"}`}
          >
            <View style={styles.sectionHeaderLeft}>
              <View style={styles.weekDot} />
              <Text style={[styles.sectionHeaderText, { fontSize: fontScale }]}>
                {WEEK_LABELS[item.week]}
              </Text>
            </View>
            <View style={styles.sectionHeaderRight}>
              {count > 0 && (
                <View style={styles.countBadge}>
                  <Text style={[styles.countBadgeText, { fontSize: fontScale - 4 }]}>
                    {count}
                  </Text>
                </View>
              )}
              <Text style={[styles.chevron, { fontSize: fontScale }]}>
                {isExpanded ? "∧" : "∨"}
              </Text>
            </View>
          </TouchableOpacity>
        );
      }

      if (item.kind === "empty") {
        return (
          <View style={styles.emptyState}>
            <Text style={[styles.emptyStateText, { fontSize: fontScale - 2 }]}>
              No conversations yet
            </Text>
          </View>
        );
      }

      if (item.kind === "newChat") {
        return (
          <TouchableOpacity
            style={styles.newChatButton}
            onPress={() => handleNewChat(item.week)}
            activeOpacity={0.8}
            accessibilityRole="button"
            accessibilityLabel={`Start new Week ${item.week} chat`}
          >
            <Text style={[styles.newChatButtonText, { fontSize: fontScale - 2 }]}>
              + New Chat
            </Text>
          </TouchableOpacity>
        );
      }

      // kind === "conversation"
      const { conversation } = item;
      const title = conversation.title ?? `Session ${conversation.session_number} Chat`;
      const dateLabel = formatDate(conversation.updated_at);
      const msgCount = conversation.message_count;

      return (
        <TouchableOpacity
          style={styles.conversationCard}
          onPress={() => handleOpenConversation(conversation)}
          onLongPress={() => handleDeleteConversation(conversation)}
          activeOpacity={0.85}
          accessibilityRole="button"
          accessibilityLabel={`${title}, ${dateLabel}, ${msgCount} message${msgCount !== 1 ? "s" : ""}. Long press to delete.`}
        >
          <View style={styles.conversationCardInner}>
            <View style={styles.conversationCardBody}>
              <Text
                style={[styles.conversationTitle, { fontSize: fontScale }]}
                numberOfLines={1}
              >
                {title}
              </Text>
              <Text style={[styles.conversationMeta, { fontSize: fontScale - 4 }]}>
                {dateLabel} · {msgCount} message{msgCount !== 1 ? "s" : ""}
              </Text>
            </View>
            <Text style={[styles.conversationChevron, { fontSize: fontScale }]}>
              ›
            </Text>
          </View>
          <View style={styles.readOnlyBadge}>
            <Text style={[styles.readOnlyBadgeText, { fontSize: fontScale - 5 }]}>
              Read only
            </Text>
          </View>
        </TouchableOpacity>
      );
    },
    [
      expandedWeeks,
      fontScale,
      toggleWeek,
      conversationsByWeek,
      handleOpenConversation,
      handleDeleteConversation,
      handleNewChat,
    ]
  );

  const keyExtractor = useCallback((item: ListItem, index: number) => {
    if (item.kind === "header") return `header-${item.week}`;
    if (item.kind === "empty") return `empty-${item.week}`;
    if (item.kind === "newChat") return `newChat-${item.week}`;
    return `conv-${item.conversation.id}`;
  }, []);

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#4A8B6F" />
        <Text style={[styles.loadingText, { fontSize: fontScale - 2 }]}>
          Loading conversations...
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
          onPress={() => navigation.navigate("ChatOverview")}
          accessibilityRole="button"
          accessibilityLabel="Go to overview"
        >
          <Text style={[styles.headerIcon, { fontSize: fontScale + 6 }]}>←</Text>
        </TouchableOpacity>

        <View style={styles.headerCenter}>
          <Text style={[styles.headerTitle, { fontSize: fontScale + 4 }]}>
            Your Conversations
          </Text>
          <Text style={[styles.headerSubtitle, { fontSize: fontScale - 4 }]}>
            {conversations.length} total
          </Text>
        </View>

        <TouchableOpacity
          style={styles.headerIconButton}
          onPress={() => navigation.navigate("Settings")}
          accessibilityRole="button"
          accessibilityLabel="Open settings"
        >
          <Text style={[styles.headerIcon, { fontSize: fontScale + 2 }]}>⚙</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={listData}
        keyExtractor={keyExtractor}
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
  centered: { flex: 1, justifyContent: "center", alignItems: "center", gap: 12 },
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
  headerIconButton: { padding: 8, borderRadius: 20, minWidth: 40, alignItems: "center" },
  headerIcon: { color: "#FFF", fontWeight: "600" },

  // List
  listContent: { paddingHorizontal: 16, paddingTop: 20, paddingBottom: 60 },

  // Section header (week row)
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "#E8F5E9",
    borderRadius: 14,
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginBottom: 6,
  },
  sectionHeaderLeft: { flexDirection: "row", alignItems: "center", flex: 1 },
  sectionHeaderRight: { flexDirection: "row", alignItems: "center", gap: 8 },
  weekDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: "#4A8B6F",
    marginRight: 10,
  },
  sectionHeaderText: { color: "#2E5D4B", fontWeight: "600" },
  chevron: { color: "#4A8B6F", fontWeight: "700" },
  countBadge: {
    backgroundColor: "#4A8B6F",
    borderRadius: 10,
    paddingHorizontal: 7,
    paddingVertical: 2,
  },
  countBadgeText: { color: "#FFF", fontWeight: "600" },

  // Conversation card
  conversationCard: {
    backgroundColor: "#FFF",
    borderRadius: 14,
    marginBottom: 8,
    marginLeft: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 2,
    borderLeftWidth: 3,
    borderLeftColor: "#4A8B6F",
  },
  conversationCardInner: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  conversationCardBody: { flex: 1, marginRight: 8 },
  conversationTitle: { color: "#1A3D2E", fontWeight: "600", marginBottom: 4 },
  conversationMeta: { color: "#6B8F7E" },
  conversationChevron: { color: "#4A8B6F", fontWeight: "700" },
  readOnlyBadge: {
    marginTop: 8,
    alignSelf: "flex-start",
    backgroundColor: "#E8F5E9",
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  readOnlyBadgeText: { color: "#4A8B6F", fontWeight: "500" },

  // Empty state
  emptyState: {
    marginLeft: 12,
    marginBottom: 8,
    paddingVertical: 12,
    alignItems: "center",
  },
  emptyStateText: { color: "#9BBCB0", fontStyle: "italic" },

  // New chat button
  newChatButton: {
    marginLeft: 12,
    marginBottom: 16,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: "#BF5F83",
    borderStyle: "dashed",
    paddingVertical: 10,
    alignItems: "center",
  },
  newChatButtonText: { color: "#BF5F83", fontWeight: "600" },
});
