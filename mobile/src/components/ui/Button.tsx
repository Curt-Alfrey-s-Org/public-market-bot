/**
 * Button Component - Customizable button with variants, sizes, and loading state
 */

import React from 'react';
import {
  TouchableOpacity,
  Text,
  ActivityIndicator,
  StyleSheet,
  TouchableOpacityProps,
  ViewStyle,
  TextStyle,
} from 'react-native';
import { useTheme } from '@/context/ThemeContext';

export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends Omit<TouchableOpacityProps, 'style'> {
  title: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  fullWidth?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

export const Button: React.FC<ButtonProps> = ({
  title,
  variant = 'primary',
  size = 'md',
  loading = false,
  fullWidth = false,
  disabled,
  style,
  textStyle,
  ...props
}) => {
  const { theme } = useTheme();

  const getButtonStyle = (): ViewStyle => {
    const baseStyle: ViewStyle = {
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: theme.borderRadius.md,
      flexDirection: 'row',
    };

    // Size styles
    const sizeStyles: Record<ButtonSize, ViewStyle> = {
      sm: { paddingVertical: theme.spacing.xs, paddingHorizontal: theme.spacing.md },
      md: { paddingVertical: theme.spacing.sm, paddingHorizontal: theme.spacing.lg },
      lg: { paddingVertical: theme.spacing.md, paddingHorizontal: theme.spacing.xl },
    };

    // Variant styles
    const variantStyles: Record<ButtonVariant, ViewStyle> = {
      primary: {
        backgroundColor: theme.colors.primary,
      },
      secondary: {
        backgroundColor: theme.colors.surface,
        borderWidth: 1,
        borderColor: theme.colors.border,
      },
      danger: {
        backgroundColor: theme.colors.error,
      },
      ghost: {
        backgroundColor: 'transparent',
      },
    };

    const finalStyle = {
      ...baseStyle,
      ...sizeStyles[size],
      ...variantStyles[variant],
    };

    if (fullWidth) {
      finalStyle.width = '100%';
    }

    if (disabled || loading) {
      finalStyle.opacity = 0.5;
    }

    return finalStyle;
  };

  const getTextStyle = (): TextStyle => {
    const sizeStyles: Record<ButtonSize, TextStyle> = {
      sm: { fontSize: theme.typography.fontSizes.sm },
      md: { fontSize: theme.typography.fontSizes.md },
      lg: { fontSize: theme.typography.fontSizes.lg },
    };

    const variantStyles: Record<ButtonVariant, TextStyle> = {
      primary: { color: '#ffffff', fontWeight: theme.typography.fontWeights.semibold },
      secondary: { color: theme.colors.text, fontWeight: theme.typography.fontWeights.medium },
      danger: { color: '#ffffff', fontWeight: theme.typography.fontWeights.semibold },
      ghost: { color: theme.colors.primary, fontWeight: theme.typography.fontWeights.medium },
    };

    return {
      ...sizeStyles[size],
      ...variantStyles[variant],
    };
  };

  return (
    <TouchableOpacity
      style={[getButtonStyle(), style]}
      disabled={disabled || loading}
      accessibilityRole="button"
      accessibilityLabel={title}
      accessibilityState={{ disabled: disabled || loading }}
      {...props}
    >
      {loading ? (
        <ActivityIndicator
          color={variant === 'secondary' ? theme.colors.primary : '#ffffff'}
          size="small"
        />
      ) : (
        <Text style={[getTextStyle(), textStyle]}>{title}</Text>
      )}
    </TouchableOpacity>
  );
};
