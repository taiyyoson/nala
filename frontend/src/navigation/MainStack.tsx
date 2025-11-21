import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import ChatOverviewScreen from '../screens/ChatOverviewScreen';
import ChatScreen from '../screens/ChatScreen';

export type MainStackParamList = {
  ChatOverview: undefined;
  Chat: {
    sessionId: string;
    week: number;
    sessionNumber: number; // 🟢 Added for session-aware ChatScreen
  };
};

const Stack = createNativeStackNavigator<MainStackParamList>();

export default function MainStack() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
      }}
    >
      <Stack.Screen name="ChatOverview" component={ChatOverviewScreen} />
      <Stack.Screen name="Chat" component={ChatScreen} />
    </Stack.Navigator>
  );
}
