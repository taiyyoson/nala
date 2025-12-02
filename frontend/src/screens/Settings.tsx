import React from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  Linking,
} from "react-native";
import {
  ArrowLeft,
  LogOut,
  Key,
  Mail,
  Phone,
  AlertCircle,
} from "lucide-react-native";
import { auth } from "../config/firebaseConfig";
import { sendPasswordResetEmail, signOut } from "firebase/auth";
import { useNavigation } from "@react-navigation/native";
import { useTextSize } from "../contexts/TextSizeContext";

export function SettingsPage() {
  const navigation = useNavigation();
  const user = auth.currentUser;
  const email = user?.email || "No email found";
  const initial = email ? email.charAt(0).toUpperCase() : "?";

  const { size, setSize } = useTextSize();

  const handlePasswordReset = async () => {
    try {
      await sendPasswordResetEmail(auth, email);
      Alert.alert("Password Reset", `A password reset link has been sent to ${email}`);
    } catch {
      Alert.alert("Error", "Unable to send reset email");
    }
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
      Alert.alert("Logged Out", "You have been signed out.");
    } catch {
      Alert.alert("Error", "Could not log out.");
    }
  };

  return (
    <View style={styles.container}>
      {/* HEADER */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.headerIconButton} onPress={() => navigation.goBack()}>
          <Text style={styles.backArrow}>←</Text>
        </TouchableOpacity>

        <Text style={styles.headerTitle}>Settings</Text>

        <View style={{ width: 35 }} />
      </View>

      <ScrollView contentContainerStyle={styles.contentContainer}>
        {/* PROFILE CARD */}
        <View style={styles.profileCard}>
          <View style={styles.initialCircle}>
            <Text style={styles.initialText}>{initial}</Text>
          </View>
          <View>
            <Text style={styles.nameText}>{email}</Text>
            <Text style={styles.emailText}>Logged in with Firebase</Text>
          </View>
        </View>

        {/* TEXT SIZE SETTINGS */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Text Size</Text>
          <View style={styles.textSizeRow}>
            <TouchableOpacity
              style={[styles.sizeOption, size === "small" && styles.selectedOption]}
              onPress={() => setSize("small")}
            >
              <Text style={styles.sizeOptionText}>Small</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.sizeOption, size === "medium" && styles.selectedOption]}
              onPress={() => setSize("medium")}
            >
              <Text style={styles.sizeOptionText}>Medium</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.sizeOption, size === "large" && styles.selectedOption]}
              onPress={() => setSize("large")}
            >
              <Text style={styles.sizeOptionText}>Large</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* SUPPORT & RESOURCES */}
        <View style={styles.supportCard}>
          <Text style={styles.supportTitle}>Support & Resources</Text>
          <Text style={styles.supportSubtitle}>Get help when you need it</Text>

          <TouchableOpacity
            style={styles.supportRow}
            onPress={() => Linking.openURL("mailto:chatbot.nala@gmail.com")}
          >
            <Mail size={20} color="#6B7280" />
            <View style={{ marginLeft: 12 }}>
              <Text style={styles.supportLabel}>Contact Support</Text>
              <Text style={styles.supportDetail}>chatbot.nala@gmail.com</Text>
            </View>
          </TouchableOpacity>

          <View style={styles.separator} />

          <View style={styles.crisisRow}>
            <AlertCircle size={20} color="#E297B4" />
            <View style={{ flex: 1, marginLeft: 12 }}>
              <Text style={styles.supportLabel}>Crisis Resources</Text>
              <Text style={styles.supportDescription}>
                If you're experiencing a crisis, help is available 24/7.
              </Text>

              <View style={styles.crisisList}>
                <TouchableOpacity style={styles.crisisItem}>
                  <Phone size={14} color="#6B7280" />
                  <View style={styles.crisisTextGroup}>
                    <Text style={styles.crisisTitle}>National Crisis Line</Text>
                    <Text style={styles.crisisNumber}>988</Text>
                  </View>
                </TouchableOpacity>

                <TouchableOpacity style={styles.crisisItem}>
                  <Phone size={14} color="#6B7280" />
                  <View style={styles.crisisTextGroup}>
                    <Text style={styles.crisisTitle}>USF Counseling Center</Text>
                    <Text style={styles.crisisNumber}>(855) 531-0761</Text>
                  </View>
                </TouchableOpacity>

                <TouchableOpacity style={styles.crisisItem}>
                  <Phone size={14} color="#6B7280" />
                  <View style={styles.crisisTextGroup}>
                    <Text style={styles.crisisTitle}>Crisis Text Line</Text>
                    <Text style={styles.crisisNumber}>Text HOME to 741741</Text>
                  </View>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </View>

        {/* RESET PASSWORD */}
        <View style={styles.card}>
          <TouchableOpacity style={styles.actionButton} onPress={handlePasswordReset}>
            <Key size={20} color="#6B7280" />
            <Text style={styles.actionText}>Reset Password</Text>
          </TouchableOpacity>
        </View>

        {/* LOGOUT */}
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <LogOut size={20} color="#B91C1C" />
          <Text style={styles.logoutText}>Log Out</Text>
        </TouchableOpacity>

        <Text style={styles.footerText}>Nala Health Coaching © 2025</Text>
      </ScrollView>
    </View>
  );
}

/* ------------------------- STYLES -------------------------- */

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

  headerTitle: {
    fontSize: 20,
    fontWeight: "700",
    color: "#fff",
  },

  headerIconButton: { padding: 8, borderRadius: 999 },
  backArrow: { fontSize: 24, color: "#FFF", fontWeight: "600" },

  contentContainer: { padding: 16 },

  profileCard: {
    backgroundColor: "white",
    borderRadius: 16,
    padding: 16,
    flexDirection: "row",
    alignItems: "center",
    gap: 16,
    marginBottom: 16,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 5,
    elevation: 2,
  },

  initialCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: "#90CDB5",
    justifyContent: "center",
    alignItems: "center",
  },

  initialText: { color: "white", fontSize: 24, fontWeight: "bold" },
  nameText: { fontSize: 16, fontWeight: "600", color: "#111827" },
  emailText: { fontSize: 14, color: "#6B7280" },

  /* ----- TEXT SIZE ----- */
  cardTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 8,
  },

  textSizeRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingHorizontal: 4,
  },

  sizeOption: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 12,
    backgroundColor: "#F3F4F6",
  },

  selectedOption: {
    backgroundColor: "#4A8B6F",
  },

  sizeOptionText: {
    color: "#111827",
    fontWeight: "500",
  },

  /* SUPPORT */
  supportCard: {
    backgroundColor: "white",
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 5,
    elevation: 2,
  },

  supportTitle: { fontSize: 16, fontWeight: "600", color: "#111" },
  supportSubtitle: { fontSize: 12, color: "#6B7280", marginBottom: 12 },
  supportRow: { flexDirection: "row", alignItems: "center", paddingVertical: 12 },
  supportLabel: { fontSize: 14, color: "#111" },
  supportDetail: { fontSize: 12, color: "#6B7280" },

  separator: {
    height: 1,
    backgroundColor: "#E5E7EB",
    marginVertical: 12,
  },

  crisisRow: { flexDirection: "row", gap: 12 },
  supportDescription: { fontSize: 12, color: "#6B7280", marginTop: 4 },
  crisisList: { marginTop: 8, gap: 12 },
  crisisItem: { flexDirection: "row", alignItems: "center", gap: 8 },
  crisisTextGroup: { flexDirection: "column" },
  crisisTitle: { fontSize: 13, color: "#111" },
  crisisNumber: { fontSize: 12, color: "#6B7280" },

  /* BUTTONS */
  actionButton: {
    paddingVertical: 16,
    paddingHorizontal: 16,
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },

  actionText: { fontSize: 14, color: "#111" },

  logoutButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#FECACA",
    backgroundColor: "#FEF2F2",
    marginBottom: 16,
    gap: 8,
  },

  logoutText: { color: "#B91C1C", fontSize: 14, fontWeight: "600" },

  footerText: {
    textAlign: "center",
    fontSize: 12,
    color: "#9CA3AF",
    marginTop: 16,
    marginBottom: 32,
  },
  card: {
    backgroundColor: "white",
    borderRadius: 16,
    marginBottom: 16,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 5,
    elevation: 2,
    padding: 16
  },
  
});
