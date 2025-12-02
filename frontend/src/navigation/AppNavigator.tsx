import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { AuthProvider, useAuth } from '../contexts/AuthContext';
import AuthStack from './AuthStack';
import MainStack from './MainStack';

// ⭐ Add this:
import { TextSizeProvider } from '../contexts/TextSizeContext';

function AppContent() {
  const { loggedInUser, hasCompletedOnboarding } = useAuth();

  return (
    <NavigationContainer>
      {loggedInUser && hasCompletedOnboarding ? <MainStack /> : <AuthStack />}
    </NavigationContainer>
  );
}

export default function AppNavigator() {
  return (
    <AuthProvider>
      <TextSizeProvider>
        <AppContent />
      </TextSizeProvider>
    </AuthProvider>
  );
}
