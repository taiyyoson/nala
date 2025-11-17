import React from 'react';
import { View, Text, StyleSheet, ScrollView, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { CheckCircle2 } from 'lucide-react-native';
import Button from './Button';
import BackButton from './BackButton';
import { getAuth } from 'firebase/auth';
import { ApiService } from '../../services/ApiService';   

type Props = {
  goToNextSlide: () => void;
  goToPreviousSlide: () => void;
};

const consentPoints = [
  "Nala is a health coach, not a clinician or mental health professional",
  "Nala will redirect you to appropriate resources if needed",
  "This program is designed to support your wellness journey",
];

export default function ConsentSlide({ goToNextSlide, goToPreviousSlide }: Props) {
  const handleConsentContinue = async () => {
    try {
      const user = getAuth().currentUser;
      if (!user) {
        Alert.alert("Error", "No user found. Please log in again.");
        return;
      }

      await ApiService.completeOnboarding(user.uid);

      console.log("✅ Onboarding completion sent to backend.");
      goToNextSlide(); // Continue to chat or dashboard
    } catch (error) {
      console.error("❌ Failed to update onboarding:", error);
      Alert.alert("Error", "Something went wrong while saving onboarding progress.");
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      {/* Header */}
      <View style={styles.header}>
        <BackButton onPress={goToPreviousSlide} />
        <Text style={styles.stepIndicator}>Step 3 of 3</Text>
        <View style={styles.placeholder} />
      </View>

      {/* Content */}
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.headline}>Before We Begin</Text>

        <View style={styles.consentCard}>
          <Text style={styles.cardTitle}>Please note:</Text>
          <View style={styles.pointsContainer}>
            {consentPoints.map((point, index) => (
              <View key={index} style={styles.pointRow}>
                <CheckCircle2 size={20} color="#48935F" style={styles.checkIcon} />
                <Text style={styles.pointText}>{point}</Text>
              </View>
            ))}
          </View>
        </View>

        <View style={styles.infoBox}>
          <Text style={styles.infoText}>
            By continuing, you understand Nala's role and are ready to begin your wellness journey.
          </Text>
        </View>
      </ScrollView>

      {/* Footer */}
      <View style={styles.footer}>
        <Button
          title="Let's get started"
          onPress={handleConsentContinue}
          variant="primary"
          size="large"
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFFFFF' },
  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 16, paddingTop: 4, paddingBottom: 15, marginTop: -55,
  },
  stepIndicator: { fontSize: 14, color: '#48935F', fontWeight: '500' },
  placeholder: { width: 40 },
  scrollView: { flex: 1 },
  scrollContent: { paddingHorizontal: 24, paddingBottom: 24 },
  headline: { fontSize: 28, fontWeight: '600', color: '#000', marginBottom: 24 },
  consentCard: {
    backgroundColor: '#FFFFFF', borderRadius: 16, padding: 24, marginBottom: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.05,
    shadowRadius: 8, elevation: 3,
  },
  cardTitle: { fontSize: 16, fontWeight: '500', color: '#000', marginBottom: 16 },
  pointsContainer: { gap: 12 },
  pointRow: { flexDirection: 'row', gap: 12 },
  checkIcon: { marginTop: 2 },
  pointText: { flex: 1, fontSize: 16, color: '#000', lineHeight: 22 },
  infoBox: { backgroundColor: '#F7C94820', borderRadius: 16, padding: 16 },
  infoText: { fontSize: 16, color: '#000', lineHeight: 22 },
  footer: { paddingHorizontal: 24, paddingBottom: 16, gap: 16 },
});
