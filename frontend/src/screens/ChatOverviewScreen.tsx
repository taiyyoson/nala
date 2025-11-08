import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { MainStackParamList } from '../navigation/MainStack';
import { useAuth } from '../contexts/AuthContext';
import AsyncStorage from '@react-native-async-storage/async-storage';

type ChatOverviewScreenNavigationProp = NativeStackNavigationProp<
  MainStackParamList,
  'ChatOverview'
>;

type Props = {
  navigation: ChatOverviewScreenNavigationProp;
};

export default function ChatOverviewScreen({ navigation }: Props) {
  const { logout } = useAuth();
  const [availableWeeks, setAvailableWeeks] = useState<number>(1);

  useEffect(() => {
    const checkAvailableWeeks = async () => {
      try {
        const storedDate = await AsyncStorage.getItem('programStartDate');
        if (!storedDate) return;

        const startDate = new Date(storedDate);
        const today = new Date();
        const diffInDays = Math.floor((today.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));

        // Unlock a new session every 7 days (1 week)
        const weeksUnlocked = Math.min(Math.floor(diffInDays / 7) + 1, 4);
        setAvailableWeeks(weeksUnlocked);
      } catch (error) {
        console.error('Error checking available weeks:', error);
      }
    };

    checkAvailableWeeks();
  }, []);

  const weeks = [
    { id: 1, title: 'Session 1' },
    { id: 2, title: 'Session 2' },
    { id: 3, title: 'Session 3' },
    { id: 4, title: 'Session 4' },
  ];

  const totalWeeks = 4;
  const progress = ((availableWeeks / totalWeeks) * 100) - 25;

  const handleLogout = async () => {
    try {
      await logout();
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={handleLogout} activeOpacity={0.7}>
          <Text style={styles.backArrow}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Coaching Program</Text>
        <View style={styles.placeholder} />
      </View>

      {/* Progress Section */}
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.progressSection}>
          <View style={styles.progressHeader}>
            <Text style={styles.progressText}>Week {availableWeeks} of {totalWeeks}</Text>
            <Text style={styles.progressPercentage}>{progress}%</Text>
          </View>
          <View style={styles.progressBarContainer}>
            <View style={[styles.progressBarFill, { width: `${progress}%` }]} />
          </View>
        </View>

        {/* Weekly Sessions */}
        <View style={styles.weeksContainer}>
          {weeks.map((week) => {
            const isAvailable = week.id <= availableWeeks;
            return (
              <TouchableOpacity
                key={week.id}
                style={[styles.weekCard, !isAvailable && styles.weekCardLocked]}
                onPress={() => isAvailable && navigation.navigate('Chat')}
                disabled={!isAvailable}
                activeOpacity={0.7}
              >
                <Text style={[styles.weekTitle, !isAvailable && styles.weekTitleLocked]}>
                  {week.title}
                </Text>
                {isAvailable ? (
                  <Text style={styles.arrowIcon}>→</Text>
                ) : (
                  <Text style={styles.lockIcon}>🔒</Text>
                )}
              </TouchableOpacity>
            );
          })}
        </View>
      </ScrollView>

      {/* Bottom Navigation */}
      <View style={styles.bottomNav}>
        <TouchableOpacity style={styles.navButton} activeOpacity={0.7}>
          <View style={styles.navButtonActive}>
            <Text style={styles.navIconActive}>💬</Text>
            <Text style={styles.navLabelActive}>Chat</Text>
          </View>
        </TouchableOpacity>
        <TouchableOpacity style={styles.navButton} activeOpacity={0.7}>
          <Text style={styles.navIcon}>⚙️</Text>
          <Text style={styles.navLabel}>Settings</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F9F7' },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 20, paddingTop: 60, paddingBottom: 20, backgroundColor: 'rgb(72, 147, 95)',
  },
  backButton: { width: 40, height: 40, justifyContent: 'center' },
  backArrow: { fontSize: 24, color: '#FFF', fontWeight: '600' },
  headerTitle: { fontSize: 18, fontWeight: '600', color: '#FFF' },
  placeholder: { width: 40 },
  content: { flex: 1, paddingHorizontal: 20 },
  progressSection: { marginTop: 24, marginBottom: 32 },
  progressHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  progressText: { fontSize: 16, color: '#666', fontWeight: '500' },
  progressPercentage: { fontSize: 18, color: '#48935F', fontWeight: '700' },
  progressBarContainer: { height: 8, backgroundColor: '#E5E7EB', borderRadius: 4, overflow: 'hidden' },
  progressBarFill: { height: '100%', backgroundColor: '#D3688C', borderRadius: 4 },
  weeksContainer: { gap: 16 },
  weekCard: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    backgroundColor: '#FFFFFF', paddingVertical: 20, paddingHorizontal: 24,
    borderRadius: 16, borderWidth: 2, borderColor: 'rgb(154, 205, 191)',
    shadowColor: 'rgb(72, 147, 95)', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1, shadowRadius: 4, elevation: 2,
  },
  weekCardLocked: { backgroundColor: '#F8F9FA', borderColor: '#E0E0E0' },
  weekTitle: { fontSize: 18, fontWeight: '600', color: 'rgb(72, 147, 95)' },
  weekTitleLocked: { color: '#D1D5DB' },
  arrowIcon: { fontSize: 20, color: '#F8BA20', fontWeight: '600' },
  lockIcon: { fontSize: 18 },
  bottomNav: {
    flexDirection: 'row', backgroundColor: '#FFFFFF', paddingVertical: 12, paddingHorizontal: 40,
    paddingBottom: 32, borderTopWidth: 1, borderTopColor: 'rgb(154, 205, 191)', gap: 40,
  },
  navButton: { flex: 1, alignItems: 'center' },
  navButtonActive: {
    backgroundColor: 'rgba(154, 205, 191, 0.2)', paddingVertical: 8, paddingHorizontal: 24,
    borderRadius: 12, flexDirection: 'row', alignItems: 'center', gap: 8,
  },
  navIcon: { fontSize: 20, marginBottom: 4 },
  navIconActive: { fontSize: 18 },
  navLabel: { fontSize: 13, color: '#9CA3AF', fontWeight: '500' },
  navLabelActive: { fontSize: 13, color: 'rgb(72, 147, 95)', fontWeight: '600' },
});
