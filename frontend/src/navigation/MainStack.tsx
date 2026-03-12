import React from 'react';
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import ConversationsScreen from '../screens/ConversationsScreen';
import ChatOverviewScreen from '../screens/ChatOverviewScreen';
import ChatScreen from '../screens/ChatScreen';
import { SettingsPage } from "../screens/Settings";

export type MainStackParamList = {
  Conversations: undefined;
  ChatOverview: undefined;
  Chat: {
    sessionId: string;
    week: number;
    sessionNumber: number;
    conversationId?: string;
    readOnly?: boolean;
  };
  Settings: undefined;
};

const Stack = createNativeStackNavigator();

export default function MainStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Conversations" component={ConversationsScreen} />
      <Stack.Screen name="ChatOverview" component={ChatOverviewScreen} />
      <Stack.Screen name="Chat" component={ChatScreen} />
      <Stack.Screen name="Settings" component={SettingsPage} />
    </Stack.Navigator>
  );
}
