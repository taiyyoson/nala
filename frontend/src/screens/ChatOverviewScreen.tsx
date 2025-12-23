import React, { useEffect, useState } from "react";
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
import { useAuth } from "../contexts/AuthContext";
import { getAuth } from "firebase/auth";
import { ApiService } from "../services/ApiService";
import {
  // Lock, // 🔒 session locking UI disabled
  CheckCircle2,
  Calendar,
  MessageCircleQuestionMark,
} from "lucide-react-native";
import { useTextSize } from "../contexts/TextSizeContext";

type ChatOverviewScreenNavigationProp = NativeStackNavigationProp<
  MainStackParamList,
  "ChatOverview"
>;

type Props = {
  navigation: ChatOverviewScreenNavigationProp;
};

interface SessionProgress {
  session_number: number;
  completed_at?: string | null;
  unlocked_at?: string | null;
}

export default function ChatOverviewScreen({ navigation }: Props) {
  const { logout } = useAuth();
  const [progress, setProgress] = useState<SessionProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const { size } = useTextSize();
  const fontScale = size === "small" ? 14 : size === "medium" ? 16 : 20;

  const sessions = [
    { id: 1, title: "Getting to know you" },
    { id: 2, title: "Building habits" },
    { id: 3, title: "Overcoming challenges" },
    { id: 4, title: "Reviewing progress" },
  ];

  // Fetch real progress from backend
  useEffect(() => {
    const fetchProgress = async () => {
      try {
        const user = getAuth().currentUser;
        if (!user) throw new Error("User not logged in");

        console.log("📊 Fetching session progress for:", user.uid);

        const data = await ApiService.getUserProgress(user.uid);
        console.log("🔎 Raw progress data:", JSON.stringify(data, null, 2));

        setProgress(data);
      } catch (error) {
        console.error("❌ Failed to fetch progress:", error);
        Alert.alert("Error", "Couldn't load your session progress.");
      } finally {
        setLoading(false);
      }
    };

    fetchProgress();
  }, []);

  // -------------------------------
  // 🔒 SESSION LOCKING (DISABLED)
  // -------------------------------
  // We turned off timer + locking for testing/demoing so users can move session-to-session
  // even if backend progress fails to load (e.g., Render cold start).
  //
  // const isSessionUnlocked = (sessionNumber: number): boolean => {
  //   if (sessionNumber === 1) return true;
  //   const current = progress.find((p) => p.session_number === sessionNumber);
  //   if (current?.unlocked_at) return new Date() >= new Date(current.unlocked_at);
  //   const prev = progress.find((p) => p.session_number === sessionNumber - 1);
  //   return !!prev?.completed_at;
  // };
  //
  // const getUnlockCountdown = (sessionNumber: number): string | null => {
  //   return "Locked";
  // };

  // COMPLETION ONLY
  const isSessionComplete = (sessionNumber: number): boolean => {
    return !!progress.find(
      (p) => p.session_number === sessionNumber && p.completed_at
    );
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (err) {
      console.error("Logout failed:", err);
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
          onPress={handleLogout}
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

      {/* Scrollable Sessions */}
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {sessions.map((session) => {
          // const unlocked = isSessionUnlocked(session.id); // 🔒 disabled
          const completed = isSessionComplete(session.id);

          // 🔓 TEMP: treat all sessions as unlocked
          const cardColor = completed ? "#4A8B6F" : "#BF5F83";

          return (
            <TouchableOpacity
              key={session.id}
              style={[styles.sessionCard, { backgroundColor: cardColor }]}
              activeOpacity={0.9}
              onPress={() =>
                navigation.navigate("Chat", {
                  sessionId: session.id.toString(),
                  week: session.id,
                  sessionNumber: session.id,
                })
              }
            >
              {/* Top-right icon */}
              <View style={styles.iconContainer}>
                {completed ? (
                  <CheckCircle2 color="#FFF" size={22} />
                ) : (
                  <Calendar color="#FFF" size={22} />
                )}
              </View>

              {/* Week Badge */}
              <View
                style={[
                  styles.weekBadge,
                  { backgroundColor: "rgba(255,255,255,0.3)" },
                ]}
              >
                <Text
                  style={[
                    styles.weekBadgeText,
                    { color: "#FFF", fontSize: fontScale - 2 },
                  ]}
                >
                  Week {session.id}
                </Text>
              </View>

              {/* Title */}
              <Text
                style={[
                  styles.sessionDescription,
                  {
                    color: "#FFF",
                    fontSize: fontScale,
                    fontWeight: "500",
                  },
                ]}
              >
                {completed ? "Completed" : session.title}
              </Text>

              {/* Footer */}
              {!completed && (
                <View style={styles.sessionFooter}>
                  <Calendar size={14} color="rgba(255,255,255,0.8)" />
                  <Text
                    style={[
                      styles.sessionFooterText,
                      { fontSize: fontScale - 4 },
                    ]}
                  >
                    10-min check-in
                  </Text>
                </View>
              )}
            </TouchableOpacity>
          );
        })}

        {/* Encouragement Card */}
        <View style={styles.motivationCard}>
          <Text style={[styles.motivationText, { fontSize: fontScale - 2 }]}>
            💪 Keep it up! Complete your next session.
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}

// Styles
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
  },
  weekBadgeText: { fontSize: 12, fontWeight: "500" },
  sessionDescription: { marginBottom: 8 },
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
