// src/components/onboarding/WelcomeSlide.tsx
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image } from 'react-native';

interface Props {
  currentSlide: number;
  goToNextSlide: () => void;
  goToPreviousSlide: () => void;
}

export default function WelcomeSlide({ goToNextSlide }: Props) {
  return (
    <View style={styles.container}>
          <Image
          source={require('../../screens/images/logo.png')} 
          style={styles.logoImage}
          resizeMode="contain"
        />
      <Text style={styles.title}>Welcome to NALA</Text>
      <Text style={styles.text}>
      Nala is a digital health coach that will help you develop lifestyle and behavior change skills. Nala will help you to set goals for health and wellness, check in on your progress, and 
      problem solve with you when things are difficult. Nala’s goal is to help you to increase your confidence to achieve your goals. 

      </Text>
      <TouchableOpacity style={styles.button} onPress={goToNextSlide}>
        <Text style={styles.buttonText}>Next</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 32 },
  title: { fontSize: 32, fontWeight: '700', color: '#48935F', marginBottom: 12 },
  text: { textAlign: 'center', color: '#555', marginBottom: 24, },
  button: { backgroundColor: '#48935F', padding: 14, borderRadius: 12, marginTop: 150, },
  buttonText: { color: '#fff', fontWeight: '600' },  logoImage: {
    width: 100, 
    height: 100,
    marginBottom: 20, 
  },
});
