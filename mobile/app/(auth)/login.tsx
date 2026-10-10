import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Controller } from 'react-hook-form';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import { useToast } from '@/context/ToastContext';
import { useForm } from '@/hooks/useForm';
import { loginSchema, LoginFormData } from '@/utils/validation';
import { Button, Input } from '@/components/ui';
import { FullPageLoader } from '@/components/FullPageLoader';

export default function LoginScreen() {
  const { state, login } = useAuth();
  const { theme } = useTheme();
  const { showToast } = useToast();

  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    schema: loginSchema,
    defaultValues: {
      username: '',
      password: '',
    },
  });

  useEffect(() => {
    if (state.error) {
      showToast(state.error, 'error');
    }
  }, [state.error]);

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data);
      showToast('Login successful!', 'success');
    } catch (error) {
      // Error handled by context and shown via useEffect
    }
  };

  // Show loading skeleton while checking stored token
  if (state.loading) {
    return <FullPageLoader message="Checking credentials..." />;
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={[styles.container, { backgroundColor: theme.colors.background }]}
    >
      <View style={styles.content}>
        <Text style={[styles.title, { color: theme.colors.text }]}>Market Bot</Text>
        <Text style={[styles.subtitle, { color: theme.colors.textSecondary }]}>
          Sign in to continue
        </Text>

        <Controller
          control={control}
          name="username"
          render={({ field: { onChange, onBlur, value } }) => (
            <Input
              label="Username"
              placeholder="Enter your username"
              value={value}
              onChangeText={onChange}
              onBlur={onBlur}
              error={errors.username?.message}
              leftIcon="person-outline"
              autoCapitalize="none"
              autoCorrect={false}
              editable={!isSubmitting}
            />
          )}
        />

        <Controller
          control={control}
          name="password"
          render={({ field: { onChange, onBlur, value } }) => (
            <Input
              label="Password"
              placeholder="Enter your password"
              value={value}
              onChangeText={onChange}
              onBlur={onBlur}
              error={errors.password?.message}
              leftIcon="lock-closed-outline"
              secureTextEntry
              autoCapitalize="none"
              editable={!isSubmitting}
            />
          )}
        />

        <Button
          title="Sign In"
          variant="primary"
          size="lg"
          fullWidth
          loading={isSubmitting}
          onPress={handleSubmit(onSubmit)}
          style={{ marginTop: theme.spacing.md }}
        />
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 40,
  },
});
