/**
 * Input Component - TextInput wrapper with label, error message, and icons
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TextInputProps,
  StyleSheet,
  TouchableOpacity,
  ViewStyle,
  TextStyle,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '@/context/ThemeContext';

interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
  leftIcon?: keyof typeof Ionicons.glyphMap;
  rightIcon?: keyof typeof Ionicons.glyphMap;
  onRightIconPress?: () => void;
  containerStyle?: ViewStyle;
  inputStyle?: TextStyle;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  leftIcon,
  rightIcon,
  onRightIconPress,
  containerStyle,
  inputStyle,
  secureTextEntry,
  ...props
}) => {
  const { theme } = useTheme();
  const [isFocused, setIsFocused] = useState(false);
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);

  const isPassword = secureTextEntry;
  const actuallySecure = isPassword && !isPasswordVisible;

  const containerStyles: ViewStyle = {
    marginBottom: theme.spacing.md,
  };

  const labelStyle: TextStyle = {
    fontSize: theme.typography.fontSizes.sm,
    fontWeight: theme.typography.fontWeights.medium,
    color: theme.colors.text,
    marginBottom: theme.spacing.xs,
  };

  const inputContainerStyle: ViewStyle = {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.background,
    borderWidth: 1,
    borderColor: error ? theme.colors.error : isFocused ? theme.colors.primary : theme.colors.border,
    borderRadius: theme.borderRadius.md,
    paddingHorizontal: theme.spacing.md,
  };

  const textInputStyle: TextStyle = {
    flex: 1,
    paddingVertical: theme.spacing.sm,
    fontSize: theme.typography.fontSizes.md,
    color: theme.colors.text,
  };

  const errorStyle: TextStyle = {
    fontSize: theme.typography.fontSizes.xs,
    color: theme.colors.error,
    marginTop: theme.spacing.xs,
  };

  const iconColor = error ? theme.colors.error : isFocused ? theme.colors.primary : theme.colors.textSecondary;

  return (
    <View style={[containerStyles, containerStyle]}>
      {label && <Text style={labelStyle}>{label}</Text>}
      
      <View style={inputContainerStyle}>
        {leftIcon && (
          <Ionicons
            name={leftIcon}
            size={20}
            color={iconColor}
            style={{ marginRight: theme.spacing.sm }}
          />
        )}
        
        <TextInput
          style={[textInputStyle, inputStyle]}
          placeholderTextColor={theme.colors.textSecondary}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          secureTextEntry={actuallySecure}
          accessibilityLabel={label}
          {...props}
        />
        
        {isPassword ? (
          <TouchableOpacity
            onPress={() => setIsPasswordVisible(!isPasswordVisible)}
            accessibilityLabel={isPasswordVisible ? 'Hide password' : 'Show password'}
            accessibilityRole="button"
          >
            <Ionicons
              name={isPasswordVisible ? 'eye-off-outline' : 'eye-outline'}
              size={20}
              color={iconColor}
            />
          </TouchableOpacity>
        ) : rightIcon ? (
          <TouchableOpacity
            onPress={onRightIconPress}
            accessibilityLabel="Icon button"
            accessibilityRole="button"
          >
            <Ionicons name={rightIcon} size={20} color={iconColor} />
          </TouchableOpacity>
        ) : null}
      </View>
      
      {error && <Text style={errorStyle}>{error}</Text>}
    </View>
  );
};
