import React from 'react';
import { View, Text, StyleSheet, Image } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Button from './Button';

type Props = {
  goToNextSlide: () => void;
  goToPreviousSlide: () => void;
};

export default function WelcomeSlide({ goToNextSlide }: Props) {
  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <View style={styles.content}>
        {/* Logo */}
        <View style={styles.logoContainer}>
          <Image
            source={require('../../../assets/nala-logo.png')}
            style={styles.logo}
            resizeMode="contain"
          />
        </View>

        {/* Text Content */}
        <View style={styles.textContainer}>
          <Text style={styles.headline}>Welcome to NALA</Text>
          <Text style={styles.subtitle}>
          Your Digital health coach awaits.
          </Text>
        </View>
      </View>

      {/* Bottom Button */}
      <View style={styles.footer}>
        <Button
          title="Get Started"
          onPress={goToNextSlide}
          variant="secondary"
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
    paddingHorizontal: 24,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoContainer: {
    marginBottom: 48,
  },
  logo: {
    width: 160,
    height: 160,
  },
  textContainer: {
    alignItems: 'center',
    paddingHorizontal: 16,
  },
  headline: {
    fontSize: 28,
    fontWeight: '600',
    color: '#000',
    textAlign: 'center',
    marginBottom: 16,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 24,
    maxWidth: 320,
  },
  footer: {
    paddingBottom: 16,
  },
});