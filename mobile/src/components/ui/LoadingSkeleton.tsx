/**
 * LoadingSkeleton Component - Animated placeholder for loading states
 */

import React, { useEffect, useRef } from 'react';
import { View, Animated, StyleSheet, ViewStyle } from 'react-native';
import { useTheme } from '@/context/ThemeContext';

interface LoadingSkeletonProps {
  width?: number | string;
  height?: number;
  borderRadius?: number;
  style?: ViewStyle;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  width = '100%',
  height = 20,
  borderRadius,
  style,
}) => {
  const { theme } = useTheme();
  const animatedValue = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(animatedValue, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(animatedValue, {
          toValue: 0,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    );

    animation.start();

    return () => animation.stop();
  }, [animatedValue]);

  const opacity = animatedValue.interpolate({
    inputRange: [0, 1],
    outputRange: [0.3, 0.7],
  });

  const skeletonStyle: ViewStyle = {
    width,
    height,
    backgroundColor: theme.colors.border,
    borderRadius: borderRadius ?? theme.borderRadius.md,
  };

  return (
    <Animated.View
      style={[skeletonStyle, { opacity }, style]}
      accessibilityLabel="Loading"
      accessibilityRole="progressbar"
    />
  );
};

// Preset skeleton shapes
export const SkeletonText: React.FC<{ lines?: number; style?: ViewStyle }> = ({ lines = 3, style }) => {
  const { theme } = useTheme();
  return (
    <View style={style}>
      {Array.from({ length: lines }).map((_, index) => (
        <LoadingSkeleton
          key={index}
          height={16}
          width={index === lines - 1 ? '60%' : '100%'}
          style={{ marginBottom: theme.spacing.sm }}
        />
      ))}
    </View>
  );
};

export const SkeletonCard: React.FC<{ style?: ViewStyle }> = ({ style }) => {
  const { theme } = useTheme();
  return (
    <View
      style={[
        {
          backgroundColor: theme.colors.surface,
          padding: theme.spacing.md,
          borderRadius: theme.borderRadius.lg,
          ...theme.shadows.md,
        },
        style,
      ]}
    >
      <LoadingSkeleton height={24} width="40%" style={{ marginBottom: theme.spacing.md }} />
      <SkeletonText lines={3} />
    </View>
  );
};
