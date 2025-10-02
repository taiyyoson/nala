import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/AppNavigator';

type ChatOverviewScreenNavigationProp = NativeStackNavigationProp<
  RootStackParamList,
  'ChatOverview'
>;

type Props = {
  navigation: ChatOverviewScreenNavigationProp;
};

export default function ChatOverviewScreen({ navigation }: Props) {
  const weeks = [
    { id: 1, title: 'Week 1', available: true },
    { id: 2, title: 'Week 2', available: false },
    { id: 3, title: 'Week 3', available: false },
    { id: 4, title: 'Week 4', available: false },
  ];

  const currentWeek = 1;
  const totalWeeks = 4;
  const progress = (currentWeek / totalWeeks) * 100;

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton}>
          <Text style={styles.backArrow}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Coaching Program</Text>
        <View style={styles.placeholder} />
      </View>

      {/* Progress Section */}
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.progressSection}>
          <View style={styles.progressHeader}>
            <Text style={styles.progressText}>Week {currentWeek} of {totalWeeks}</Text>
            <Text style={styles.progressPercentage}>{progress}%</Text>
          </View>
          <View style={styles.progressBarContainer}>
            <View style={[styles.progressBarFill, { width: `${progress}%` }]} />
          </View>
        </View>

        {/* Weekly Sessions */}
        <View style={styles.weeksContainer}>
          {weeks.map((week) => (
            <TouchableOpacity
              key={week.id}
              style={[
                styles.weekCard,
                !week.available && styles.weekCardLocked
              ]}
              onPress={() => week.available && navigation.navigate('Chat')}
              disabled={!week.available}
              activeOpacity={0.7}
            >
              <Text style={[
                styles.weekTitle,
                !week.available && styles.weekTitleLocked
              ]}>
                {week.title}
              </Text>
              {week.available ? (
                <Text style={styles.arrowIcon}>→</Text>
              ) : (
                <Text style={styles.lockIcon}>🔒</Text>
              )}
            </TouchableOpacity>
          ))}
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
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
    backgroundColor: '#F8F9FA',
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
  },
  backArrow: {
    fontSize: 24,
    color: '#000',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  placeholder: {
    width: 40,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  progressSection: {
    marginBottom: 32,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  progressText: {
    fontSize: 16,
    color: '#6B7280',
    fontWeight: '500',
  },
  progressPercentage: {
    fontSize: 18,
    color: '#3B82F6',
    fontWeight: '700',
  },
  progressBarContainer: {
    height: 8,
    backgroundColor: '#E5E7EB',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#3B82F6',
    borderRadius: 4,
  },
  weeksContainer: {
    gap: 16,
  },
  weekCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    paddingVertical: 20,
    paddingHorizontal: 24,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  weekCardLocked: {
    backgroundColor: '#F8F9FA',
  },
  weekTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  weekTitleLocked: {
    color: '#D1D5DB',
  },
  arrowIcon: {
    fontSize: 20,
    color: '#3B82F6',
    fontWeight: '600',
  },
  lockIcon: {
    fontSize: 18,
  },
  bottomNav: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    paddingVertical: 12,
    paddingHorizontal: 40,
    paddingBottom: 32,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
    gap: 40,
  },
  navButton: {
    flex: 1,
    alignItems: 'center',
  },
  navButtonActive: {
    backgroundColor: '#E0F2FE',
    paddingVertical: 8,
    paddingHorizontal: 24,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  navIcon: {
    fontSize: 20,
    marginBottom: 4,
  },
  navIconActive: {
    fontSize: 18,
  },
  navLabel: {
    fontSize: 13,
    color: '#9CA3AF',
    fontWeight: '500',
  },
  navLabelActive: {
    fontSize: 13,
    color: '#3B82F6',
    fontWeight: '600',
  },
});