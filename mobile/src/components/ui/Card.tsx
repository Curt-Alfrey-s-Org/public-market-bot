/**
 * Card Component - Container with shadow, padding, optional header/footer
 */

import React, { ReactNode } from 'react';
import { View, Text, StyleSheet, ViewStyle, TextStyle } from 'react-native';
import { useTheme } from '@/context/ThemeContext';

interface CardProps {
  children: ReactNode;
  header?: string | ReactNode;
  footer?: ReactNode;
  style?: ViewStyle;
  headerStyle?: TextStyle;
  noPadding?: boolean;
  noShadow?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  header,
  footer,
  style,
  headerStyle,
  noPadding = false,
  noShadow = false,
}) => {
  const { theme } = useTheme();

  const cardStyle: ViewStyle = {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.lg,
    padding: noPadding ? 0 : theme.spacing.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    ...(!noShadow && theme.shadows.md),
  };

  const defaultHeaderStyle: TextStyle = {
    fontSize: theme.typography.fontSizes.lg,
    fontWeight: theme.typography.fontWeights.semibold,
    color: theme.colors.text,
    marginBottom: theme.spacing.md,
  };

  return (
    <View style={[cardStyle, style]}>
      {header && (
        <View style={noPadding ? { padding: theme.spacing.md, paddingBottom: 0 } : undefined}>
          {typeof header === 'string' ? (
            <Text style={[defaultHeaderStyle, headerStyle]}>{header}</Text>
          ) : (
            header
          )}
        </View>
      )}
      {children}
      {footer && (
        <View style={noPadding ? { padding: theme.spacing.md, paddingTop: 0 } : undefined}>
          {footer}
        </View>
      )}
    </View>
  );
};
