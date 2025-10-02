import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import LoadingScreen from '../screens/LoadingScreen';
import ChatOverviewScreen from '../screens/ChatOverviewScreen';
import ChatScreen from '../screens/ChatScreen';

export type RootStackParamList = {
  Loading: undefined;
  ChatOverview: undefined;
  Chat: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator 
        initialRouteName="Loading"
        screenOptions={{
          headerShown: false,
        }}
      >
        <Stack.Screen 
          name="Loading" 
          component={LoadingScreen}
        />
        <Stack.Screen 
          name="ChatOverview" 
          component={ChatOverviewScreen}
        />
        <Stack.Screen 
          name="Chat" 
          component={ChatScreen}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}