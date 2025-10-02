import React, { useEffect } from 'react';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/AppNavigator';

type LoadingScreenNavigationProp = NativeStackNavigationProp <
  RootStackParamList,
  'Loading'
>;

type Props = {
  navigation: LoadingScreenNavigationProp;
};

export default function LoadingScreen({ navigation }: Props) {
  console.log('🔵 LoadingScreen rendering');

  useEffect(() => {
    console.log('🟢 LoadingScreen mounted');
    console.log('📍 Navigation state:', JSON.stringify(navigation.getState(), null, 2));
    
    const timer = setTimeout(() => {
      console.log('⏰ Timer fired - attempting navigation');
      navigation.replace('ChatOverview');
      console.log('✅ Replace called');
      
      // Check if navigation actually happened
      setTimeout(() => {
        console.log('📍 After navigation state:', JSON.stringify(navigation.getState(), null, 2));
      }, 100);
    }, 2000);

    return () => {
      console.log('🔴 LoadingScreen unmounting, clearing timer');
      clearTimeout(timer);
    };
  }, [navigation]);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>NALA</Text>
      <Text style={styles.subtitle}>Health Coach</Text>
      <ActivityIndicator size="large" color="#2563eb" style={styles.loader} />
      <Text style={styles.text}>Loading your health journey...</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#4A90E2',
  },
  title: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 24,
    color: '#fff',
    opacity: 0.9,
    marginBottom: 40,
  },
  loader: {
    marginBottom: 16,
  },
  text: {
    marginTop: 16,
    fontSize: 16,
    color: '#fff',
    opacity: 0.8,
  },
});