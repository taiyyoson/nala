import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';

type Props = {
  goToNextSlide: () => void;
  goToPreviousSlide: () => void;
};

export default function DetailsSlide({ goToNextSlide, goToPreviousSlide }: Props) {
  const weeks = [
    { icon: '🌱', title: 'Session 1: Setting Your Foundation', desc: 'I will help you to identify one goal you want to achieve in the next 4 weeks.' },
    { icon: '🚀', title: 'Session 2: Building Momentum', desc: 'We’ll assess your progress on meeting your goal, with both successes and challenges.' },
    { icon: '🎯', title: 'Session 3: Staying on Track', desc: 'Maintain motivation and adapt your plan.' },
    { icon: '🏆', title: 'Session 4: Finishing Strong', desc: 'We’ll reflect on your progress and make a                long-term plan for healthy behavior.' },
  ];

  return (
    <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <TouchableOpacity onPress={goToPreviousSlide}><Text style={styles.back}>←</Text></TouchableOpacity>
        <Text style={styles.step}>Step 3 of 3</Text>
        <View style={{ width: 40 }} />
      </View>

      <Text style={styles.title}>Details of Next 4 Weeks</Text>

      {weeks.map((w, i) => (
        <View key={i} style={styles.week}>
          <Text style={styles.icon}>{w.icon}</Text>
          <View>
            <Text style={styles.weekTitle}>{w.title}</Text>
            <Text style={styles.weekDesc}>{w.desc}</Text>
          </View>
        </View>
      ))}

      <TouchableOpacity style={styles.button} onPress={goToNextSlide}>
        <Text style={styles.buttonText}>Let's Get Started</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, padding: 24 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  back: { fontSize: 24 },
  step: { color: '#9ACDAF', fontWeight: '600' },
  title: { fontSize: 28, fontWeight: '700', marginBottom: 25 },
  week: { flexDirection: 'row', marginBottom: 24, gap: 12 },
  icon: { fontSize: 24 },
  weekTitle: { fontSize: 16, fontWeight: '600', marginBottom: 10, },
  weekDesc: { fontSize: 14, color: '#666' },
  button: { backgroundColor: '#F8BA20', padding: 16, borderRadius: 14, alignItems: 'center', marginTop: 200 },
  buttonText: { color: '#1a1a1a', fontWeight: '700', fontSize: 16 },
});
