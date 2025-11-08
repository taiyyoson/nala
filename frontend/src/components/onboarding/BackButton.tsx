import React from 'react';
import {
  TouchableOpacity,
  StyleSheet,
  ViewStyle,
} from 'react-native';
import { ArrowLeft } from 'lucide-react-native';

interface BackButtonProps {
  onPress: () => void;
  color?: string;
  size?: number;
  style?: ViewStyle;
}

export default function BackButton({
  onPress,
  color = '#000000',
  size = 24,
  style,
}: BackButtonProps) {
  return (
    <TouchableOpacity
      style={[styles.button, style]}
      onPress={onPress}
      activeOpacity={0.6}
      hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
    >
      <ArrowLeft size={size} color={color} strokeWidth={2} />
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 20,
  },
});