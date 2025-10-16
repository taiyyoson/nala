import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';

type Props = {
  goToNextSlide: () => void;
  goToPreviousSlide: () => void;
};

export default function HowItWorksSlide({ goToNextSlide, goToPreviousSlide }: Props) {
  const features = [
    { icon: '🎯', title: 'Set a Clear Goal', desc: 'NALA helps you define your SMART goals.' },
    { icon: '📅', title: 'Weekly Coaching', desc: 'Regular check-ins and personalized guidance.' },
    { icon: '📈', title: 'Track Your Progress', desc: 'See tangible progress and stay motivated.' },
  ];

  return (
    <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <TouchableOpacity onPress={goToPreviousSlide}><Text style={styles.back}>←</Text></TouchableOpacity>
        <Text style={styles.step}>Step 2 of 3</Text>
        <View style={{ width: 40 }} />
      </View>

      <Text style={styles.title}>How It Works</Text>
      <Text style={styles.subtitle}>
      NALA will use strategies to help you achieve healthy behavior, that come from research and are tailored just for you.

      </Text>

      {features.map((f, i) => (
        <View key={i} style={styles.feature}>
          <Text style={styles.icon}>{f.icon}</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.featureTitle}>{f.title}</Text>
            <Text style={styles.featureDesc}>{f.desc}</Text>
          </View>
        </View>
      ))}

      <TouchableOpacity style={styles.button} onPress={goToNextSlide}>

        <Text style={styles.buttonText}>Next: The 4-Week Plan</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, padding: 24 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  back: { fontSize: 24 },
  step: { color: '#9ACDAF', fontWeight: '600' },
  title: { fontSize: 28, fontWeight: '700', marginBottom: 12 },
  subtitle: { fontSize: 16, color: '#666', marginBottom: 20 },
  feature: { flexDirection: 'row', marginBottom: 24, alignItems: 'flex-start', gap: 12 },
  icon: { fontSize: 24 },
  featureTitle: { fontSize: 16, fontWeight: '600', marginBottom: 7, },
  featureDesc: { fontSize: 14, color: '#666' },
  button: { backgroundColor: '#D3688C', padding: 16, borderRadius: 14, alignItems: 'center', marginTop: 260 },
  buttonText: { color: 'white', fontWeight: '600', fontSize: 16 },
});
