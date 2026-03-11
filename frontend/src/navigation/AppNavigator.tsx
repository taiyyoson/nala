import React from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { AuthProvider, useAuth } from '../contexts/AuthContext';
import AuthStack from './AuthStack';
import MainStack from './MainStack';

// ⭐ Add this:
import { TextSizeProvider } from '../contexts/TextSizeContext';

function AppContent() {
  const { loggedInUser, hasCompletedOnboarding, loading } = useAuth();

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      {loggedInUser && hasCompletedOnboarding ? <MainStack /> : <AuthStack />}
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default function AppNavigator() {
  return (
    <AuthProvider>
      <TextSizeProvider>
        <AppContent />
      </TextSizeProvider>
    </AuthProvider>
  );
}
