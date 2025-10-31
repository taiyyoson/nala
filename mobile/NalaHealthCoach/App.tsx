import React, { useEffect, useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { initializeApp } from 'firebase/app';
import { getAuth, onAuthStateChanged, User } from 'firebase/auth';

// Import your screens
import LoginScreen from './src/screens/LoginScreen';
import ChatScreen from './src/screens/ChatScreen';
import LoadingScreen from './src/screens/LoadingScreen';

// 🔥 FIREBASE CONFIGURATION
// ⚠️  REPLACE WITH YOUR ACTUAL FIREBASE CONFIG FROM FIREBASE CONSOLE
const firebaseConfig = {
  apiKey: "your-api-key-here",
  authDomain: "your-project.firebaseapp.com", 
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abcdefghijklmnop"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Listen for authentication state changes
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      console.log('Auth state changed:', user ? 'Logged in' : 'Logged out');
      setUser(user);
      setIsLoading(false);
    });

    // Cleanup subscription on unmount
    return unsubscribe;
  }, []);

  // Show loading screen while checking authentication
  if (isLoading) {
    return (
      <>
        <StatusBar style="auto" />
        <LoadingScreen />
      </>
    );
  }

  // Render the appropriate screen based on authentication state
  return (
    <>
      <StatusBar style="auto" />
      {user ? <ChatScreen /> : <LoginScreen />}
    </>
  );
}