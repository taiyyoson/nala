import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Sprout, Rocket, Target, Trophy } from 'lucide-react-native';
import Button from './Button';
import BackButton from './BackButton';

type Props = {
  goToNextSlide: () => void;
  goToPreviousSlide: () => void;
};

const weeklyPlan = [
  {
    Icon: Sprout,
    title: 'Session 1: Setting Your Foundation',
    description:
      'Nala will help you to identify one major health goal you want to achieve in the next 4 weeks.',
    color: '#48935F',
  },
  {
    Icon: Rocket,
    title: 'Session 2: Building Momentum',
    description: 'Nala will celebrate your successes and problem solve your challenges.',
    color: '#F7C948',
  },
  {
    Icon: Target,
    title: 'Session 3: Staying on Track',
    description:
      'Nala will help you maintain your motivation and adapt your plan for success to achieve your goals.',
    color: '#E297B4',
  },
  {
    Icon: Trophy,
    title: 'Session 4: Finishing Strong',
    description:
      'Nala will reflect on your progress and make a long-term plan for healthy behavior.',
    color: '#90CDB5',
  },
];

export default function DetailsSlide({ goToNextSlide, goToPreviousSlide }: Props) {
  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      {/* Header */}
      <View style={styles.header}>
        <BackButton onPress={goToPreviousSlide} />
        <Text style={styles.stepIndicator}>Step 2 of 3</Text>
        <View style={styles.placeholder} />
      </View>

      {/* Content */}
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.headline}>Details of Next 4 Weeks</Text>

        {/* Weekly Plan */}
        <View style={styles.sessionsContainer}>
          {weeklyPlan.map((session, index) => (
            <View key={index} style={styles.sessionCard}>
              <View
                style={[styles.iconContainer, { backgroundColor: `${session.color}33` }]}
              >
                <session.Icon size={24} color={session.color} />
              </View>
              <View style={styles.sessionContent}>
                <Text style={styles.sessionTitle}>{session.title}</Text>
                <Text style={styles.sessionDescription}>{session.description}</Text>
              </View>
            </View>
          ))}
        </View>
      </ScrollView>

      {/* Footer */}
      <View style={styles.footer}>
        <Button
          title="Next: Privacy "
          onPress={goToNextSlide}
          variant="primary"
          size="large"
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 4,       
    paddingBottom: 15,
    marginTop: -55,       
  },
  stepIndicator: {
    fontSize: 14,
    color: '#48935F',
    fontWeight: '500',
  },
  placeholder: {
    width: 40,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 24,
    paddingBottom: 4,
  },
  headline: {
    fontSize: 28,
    fontWeight: '600',
    color: '#000',
    marginBottom: 16,
  },
  sessionsContainer: {
    gap: 24,
    marginTop: 16,
  },
  sessionCard: {
    flexDirection: 'row',
    gap: 16,
    backgroundColor: '#F9F9F9',
    borderRadius: 12,
    padding: 7,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
  },
  
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sessionContent: {
    flex: 1,
  },
  sessionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
    marginBottom: 6,
  },
  sessionDescription: {
    fontSize: 16,
    color: '#666',
    lineHeight: 22,
  },
  footer: {
    paddingHorizontal: 24,
    paddingBottom: 16,
    gap: 16,
  },
});
