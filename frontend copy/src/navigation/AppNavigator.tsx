import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { AuthProvider, useAuth } from '../contexts/AuthContext';
import AuthStack from './AuthStack';
import MainStack from './MainStack';

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
      <AppContent />
    </AuthProvider>
  );
}