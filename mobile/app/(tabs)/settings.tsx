import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Switch, TouchableOpacity, Modal, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '@/context/ThemeContext';
import { useAuth } from '@/context/AuthContext';
import { Card, Button } from '@/components/ui';
import Constants from 'expo-constants';

export default function SettingsScreen() {
  const { theme, themeMode, setThemeMode, toggleTheme } = useTheme();
  const { state, logout } = useAuth();
  const [showLogoutModal, setShowLogoutModal] = useState(false);

  const isDarkMode = theme.isDark;
  const apiUrl = Constants.expoConfig?.extra?.apiUrl || 'Not configured';
  const user = state.user;

  const handleLogout = async () => {
    setShowLogoutModal(false);
    try {
      await logout();
    } catch (error) {
      Alert.alert('Error', 'Failed to logout. Please try again.');
    }
  };

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={[styles.header, { backgroundColor: theme.colors.surface, borderBottomColor: theme.colors.border }]}>
        <Text style={[styles.title, { color: theme.colors.text }]}>Settings</Text>
      </View>

      <View style={{ padding: theme.spacing.md }}>
        {/* Profile Section */}
        <Card header="Profile" style={{ marginBottom: theme.spacing.md }}>
          <View style={styles.profileContainer}>
            <View style={[styles.avatarContainer, { backgroundColor: theme.colors.primary + '20' }]}>
              <Ionicons name="person" size={40} color={theme.colors.primary} />
            </View>
            <View style={styles.profileInfo}>
              <Text style={[styles.profileName, { color: theme.colors.text }]}>
                {user?.username || 'User'}
              </Text>
              {user?.email && (
                <Text style={[styles.profileEmail, { color: theme.colors.textSecondary }]}>
                  {user.email}
                </Text>
              )}
              <Text style={[styles.profileDetail, { color: theme.colors.textSecondary }]}>
                Member since {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              </Text>
            </View>
          </View>
        </Card>

        {/* Theme Settings */}
        <Card header="Appearance" style={{ marginBottom: theme.spacing.md }}>
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={[styles.settingLabel, { color: theme.colors.text }]}>
                Dark Mode
              </Text>
              <Text style={[styles.settingDescription, { color: theme.colors.textSecondary }]}>
                {themeMode === 'system' 
                  ? 'Following system preference'
                  : isDarkMode 
                    ? 'Dark theme enabled'
                    : 'Light theme enabled'}
              </Text>
            </View>
            <Switch
              value={isDarkMode}
              onValueChange={toggleTheme}
              trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
              thumbColor="#ffffff"
            />
          </View>
        </Card>

        {/* Notifications (Placeholder) */}
        <Card header="Notifications" style={{ marginBottom: theme.spacing.md }}>
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={[styles.settingLabel, { color: theme.colors.text }]}>
                Trade Alerts
              </Text>
              <Text style={[styles.settingDescription, { color: theme.colors.textSecondary }]}>
                Notify when trades are executed
              </Text>
            </View>
            <Switch
              value={false}
              onValueChange={() => {}}
              trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
              thumbColor="#ffffff"
              disabled
            />
          </View>
          <View style={[styles.divider, { backgroundColor: theme.colors.border }]} />
          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={[styles.settingLabel, { color: theme.colors.text }]}>
                Bot Status Updates
              </Text>
              <Text style={[styles.settingDescription, { color: theme.colors.textSecondary }]}>
                Notify when bot status changes
              </Text>
            </View>
            <Switch
              value={false}
              onValueChange={() => {}}
              trackColor={{ false: theme.colors.border, true: theme.colors.primary }}
              thumbColor="#ffffff"
              disabled
            />
          </View>
        </Card>

        {/* About Section */}
        <Card header="About" style={{ marginBottom: theme.spacing.md }}>
          <View style={styles.infoRow}>
            <Text style={[styles.infoLabel, { color: theme.colors.textSecondary }]}>
              Version
            </Text>
            <Text style={[styles.infoValue, { color: theme.colors.text }]}>
              1.0.0
            </Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={[styles.infoLabel, { color: theme.colors.textSecondary }]}>
              Build
            </Text>
            <Text style={[styles.infoValue, { color: theme.colors.text }]}>
              Phase 3-C
            </Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={[styles.infoLabel, { color: theme.colors.textSecondary }]}>
              API URL
            </Text>
            <Text style={[styles.infoValue, { color: theme.colors.text }]} numberOfLines={1}>
              {apiUrl}
            </Text>
          </View>
        </Card>

        {/* Logout Button */}
        <Button
          label="Logout"
          onPress={() => setShowLogoutModal(true)}
          variant="error"
          icon={<Ionicons name="log-out-outline" size={20} color="#ffffff" />}
          style={{ marginBottom: theme.spacing.lg }}
        />
      </View>

      {/* Logout Confirmation Modal */}
      <Modal
        visible={showLogoutModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowLogoutModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { backgroundColor: theme.colors.surface }]}>
            <View style={[styles.modalIconContainer, { backgroundColor: theme.colors.error + '20' }]}>
              <Ionicons name="log-out-outline" size={32} color={theme.colors.error} />
            </View>
            <Text style={[styles.modalTitle, { color: theme.colors.text }]}>
              Logout
            </Text>
            <Text style={[styles.modalMessage, { color: theme.colors.textSecondary }]}>
              Are you sure you want to logout? You'll need to login again to access your account.
            </Text>
            <View style={styles.modalButtons}>
              <Button
                label="Cancel"
                onPress={() => setShowLogoutModal(false)}
                variant="outline"
                style={styles.modalButton}
              />
              <Button
                label="Logout"
                onPress={handleLogout}
                variant="error"
                style={styles.modalButton}
              />
            </View>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    padding: 20,
    borderBottomWidth: 1,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  profileContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatarContainer: {
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  profileInfo: {
    flex: 1,
  },
  profileName: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  profileEmail: {
    fontSize: 14,
    marginBottom: 2,
  },
  profileDetail: {
    fontSize: 12,
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  settingInfo: {
    flex: 1,
    marginRight: 16,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  settingDescription: {
    fontSize: 14,
  },
  divider: {
    height: 1,
    marginVertical: 12,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  infoLabel: {
    fontSize: 14,
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '600',
    maxWidth: '60%',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    width: '100%',
    maxWidth: 400,
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
  },
  modalIconContainer: {
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  modalMessage: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 20,
  },
  modalButtons: {
    flexDirection: 'row',
    width: '100%',
    gap: 12,
  },
  modalButton: {
    flex: 1,
  },
});
