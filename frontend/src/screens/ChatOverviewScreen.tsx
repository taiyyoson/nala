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
import { Lock, CheckCircle2, Calendar, Settings } from "lucide-react-native";

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

  const sessions = [
    { id: 1, title: "Getting to know you" },
    { id: 2, title: "Building habits" },
    { id: 3, title: "Building habits" },
    { id: 4, title: "Reviewing progress" },
  ];

  // 🧩 Fetch real progress from backend
  useEffect(() => {
    const fetchProgress = async () => {
      try {
        const user = getAuth().currentUser;
        if (!user) throw new Error("User not logged in");

        console.log("📊 Fetching session progress for:", user.uid);
        const data = await ApiService.getUserProgress(user.uid);
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

  // 🟢 Determine if a session is unlocked
  const isSessionUnlocked = (sessionNumber: number): boolean => {
    if (sessionNumber === 1) return true;
    const record = progress.find((p) => p.session_number === sessionNumber - 1);
    if (!record || !record.unlocked_at) return false;

    const now = new Date();
    const unlockDate = new Date(record.unlocked_at);
    return now >= unlockDate;
  };

  // 🟢 Determine if a session is complete
  const isSessionComplete = (sessionNumber: number): boolean => {
    const record = progress.find((p) => p.session_number === sessionNumber);
    return record?.completed_at ? true : false;
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
        <Text style={{ marginTop: 8, color: "#555" }}>Loading your progress...</Text>
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
          <Text style={styles.headerTitle}>Your Journey</Text>
          <Text style={styles.headerSubtitle}>
            4-week wellness coaching program
          </Text>
        </View>
        <TouchableOpacity
          onPress={() => navigation.navigate("Settings")}
          style={styles.headerIconButton}
        >
          <Settings color="#fff" size={22} />
        </TouchableOpacity>
      </View>

      {/* Scrollable Sessions */}
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {sessions.map((session) => {
          const unlocked = isSessionUnlocked(session.id);
          const completed = isSessionComplete(session.id);

          let cardColor = "#E5E7EB"; // Default locked
          if (completed) cardColor = "#4A8B6F";
          else if (unlocked) cardColor = "#BF5F83";

          return (
            <TouchableOpacity
              key={session.id}
              style={[styles.sessionCard, { backgroundColor: cardColor }]}
              activeOpacity={unlocked ? 0.9 : 1}
              disabled={!unlocked}
              onPress={() => unlocked && navigation.navigate("Chat")}
            >
              <View style={styles.iconContainer}>
                {completed ? (
                  <CheckCircle2 color="#FFF" size={22} />
                ) : unlocked ? (
                  <Calendar color="#FFF" size={22} />
                ) : (
                  <Lock color="#6B7280" size={22} />
                )}
              </View>

              <View
                style={[
                  styles.weekBadge,
                  {
                    backgroundColor: unlocked
                      ? "rgba(255,255,255,0.3)"
                      : "rgba(0,0,0,0.1)",
                  },
                ]}
              >
                <Text
                  style={[
                    styles.weekBadgeText,
                    { color: unlocked ? "#FFF" : "#6B7280" },
                  ]}
                >
                  Week {session.id}
                </Text>
              </View>
              <Text
                style={[
                  styles.sessionDescription,
                  {
                    color: unlocked ? "#FFF" : "#6B7280",
                    fontWeight: "500", 
                    fontSize: 16,      
                  },
                ]}
              >
                {unlocked
                  ? session.title
                  : "Complete previous sessions to unlock"}
              </Text>


              {unlocked && !completed && (
                <View style={styles.sessionFooter}>
                  <Calendar size={14} color="rgba(255,255,255,0.8)" />
                  <Text style={styles.sessionFooterText}>10-min check-in</Text>
                </View>
              )}
            </TouchableOpacity>
          );
        })}

        {/* Encouragement Card */}
        <View style={styles.motivationCard}>
          <Text style={styles.motivationText}>
            💪 Keep it up! Complete your current session to unlock the next one.
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}

// ✅ Styles
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
  sessionTitle: { fontSize: 20, fontWeight: "700", marginBottom: 4 },
  sessionDescription: { fontSize: 14, marginBottom: 8 },
  sessionFooter: { flexDirection: "row", alignItems: "center", gap: 6 },
  sessionFooterText: { color: "rgba(255,255,255,0.8)", fontSize: 12 },
  motivationCard: {
    backgroundColor: "#FEF3E2",
    borderRadius: 16,
    padding: 16,
    marginTop: 8,
  },
  motivationText: {
    color: "#4A4A4A",
    fontSize: 13,
    textAlign: "center",
  },
  centered: { flex: 1, justifyContent: "center", alignItems: "center" },
});
