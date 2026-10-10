/**
 * Badge Component - Small colored label for status indicators
 */

import React from 'react';
import { View, Text, StyleSheet, ViewStyle, TextStyle } from 'react-native';
import { useTheme } from '@/context/ThemeContext';

export type BadgeVariant = 'success' | 'warning' | 'error' | 'info' | 'default';
export type BadgeSize = 'sm' | 'md' | 'lg';

interface BadgeProps {
  label: string;
  variant?: BadgeVariant;
  size?: BadgeSize;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

export const Badge: React.FC<BadgeProps> = ({
  label,
  variant = 'default',
  size = 'md',
  style,
  textStyle,
}) => {
  const { theme } = useTheme();

  const getBackgroundColor = (): string => {
    switch (variant) {
      case 'success':
        return theme.colors.success;
      case 'warning':
        return theme.colors.warning;
      case 'error':
        return theme.colors.error;
      case 'info':
        return theme.colors.info;
      case 'default':
      default:
        return theme.colors.secondary;
    }
  };

  const sizeStyles: Record<BadgeSize, { padding: number; fontSize: number }> = {
    sm: { padding: theme.spacing.xs / 2, fontSize: theme.typography.fontSizes.xs },
    md: { padding: theme.spacing.xs, fontSize: theme.typography.fontSizes.sm },
    lg: { padding: theme.spacing.sm, fontSize: theme.typography.fontSizes.md },
  };

  const badgeStyle: ViewStyle = {
    backgroundColor: getBackgroundColor(),
    paddingHorizontal: sizeStyles[size].padding * 2,
    paddingVertical: sizeStyles[size].padding,
    borderRadius: theme.borderRadius.full,
    alignSelf: 'flex-start',
  };

  const badgeTextStyle: TextStyle = {
    color: '#ffffff',
    fontSize: sizeStyles[size].fontSize,
    fontWeight: theme.typography.fontWeights.semibold,
    textTransform: 'uppercase',
  };

  return (
    <View style={[badgeStyle, style]} accessibilityRole="text" accessibilityLabel={label}>
      <Text style={[badgeTextStyle, textStyle]}>{label}</Text>
    </View>
  );
};
