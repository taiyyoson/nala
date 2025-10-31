import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import ChatOverviewScreen from '../screens/ChatOverviewScreen';
import ChatScreen from '../screens/ChatScreen';

export type MainStackParamList = {
  ChatOverview: undefined;
  Chat: undefined;
};

const Stack = createNativeStackNavigator<MainStackParamList>();

// This stack is for authenticated users only
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