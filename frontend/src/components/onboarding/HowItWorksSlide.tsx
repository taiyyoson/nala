import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Target, Calendar, TrendingUp } from 'lucide-react-native';
import Button from './Button';
import BackButton from './BackButton';

type Props = {
  goToNextSlide: () => void;
  goToPreviousSlide: () => void;
};

const howItWorksSteps = [
  {
    Icon: Target,
    title: 'Set a Clear Goal',
    description: 'Nala helps you define your SMART goals.',
    color: '#E297B4',
  },
  {
    Icon: Calendar,
    title: 'Weekly Coaching',
    description: 'Nala will be chatting with you once a week for about 10 minutes.',
    color: '#48935F',
  },
  {
    Icon: TrendingUp,
    title: 'Track Your Progress',
    description:
      'Nala will monitor your progress and problem solve with you when things are difficult.',
    color: '#F7C948',
  },
];

export default function HowItWorksSlide({ goToNextSlide, goToPreviousSlide }: Props) {
  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      {/* Header */}
      <View style={styles.header}>
        <BackButton onPress={goToPreviousSlide} />
        <Text style={styles.stepIndicator}>Step 1 of 3</Text>
        <View style={styles.placeholder} />
      </View>

      {/* Content */}
      <View style={styles.content}>
        <Text style={styles.headline}>How It Works</Text>

        <Text style={styles.description}>
          Nala is your digital health coach for a four-week program. Nala uses research-based
          strategies to help you build healthy habits and connects you to the right resources
          when needed.
        </Text>

        {howItWorksSteps.map((step, index) => (
          <View key={index} style={styles.stepCard}>
            <View
              style={[styles.iconContainer, { backgroundColor: `${step.color}33` }]}
            >
              <step.Icon size={24} color={step.color} strokeWidth={2} />
            </View>
            <View style={styles.stepContent}>
              <Text style={styles.stepTitle}>{step.title}</Text>
              <Text style={styles.stepDescription}>{step.description}</Text>
            </View>
          </View>
        ))}
      </View>

      {/* Footer */}
      <View style={styles.footerContainer}>
        <View style={styles.footer}>
          <Button
            title="Next: The 4-Week Plan"
            onPress={goToNextSlide}
            variant="primary"
            size="large"
          />
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#FFFFFF', // pure white
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
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 12,
    justifyContent: 'flex-start',
    backgroundColor: '#FFFFFF',
  },
  headline: {
    fontSize: 28,
    fontWeight: '700',
    color: '#000',
    marginBottom: 16,
  },
  description: {
    fontSize: 16,
    color: '#666',
    lineHeight: 24,
    marginBottom: 28,
  },
  stepCard: {
    flexDirection: 'row',
    gap: 16,
    backgroundColor: '#F9F9F9',
    borderRadius: 12,
    padding: 12,
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
  stepContent: {
    flex: 1,
  },
  stepTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
    marginBottom: 4,
  },
  stepDescription: {
    fontSize: 16,
    color: '#666',
    lineHeight: 22,
  },
  footerContainer: {
    backgroundColor: '#FFFFFF',
  },
  footer: {
    paddingHorizontal: 24,
    paddingBottom: 28,
    paddingTop: 16,
  },
});
