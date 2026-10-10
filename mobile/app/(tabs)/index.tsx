import React from 'react';
import { View, Text, StyleSheet, RefreshControl, ScrollView } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { botService } from '@/api/services/bot';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import { useToast } from '@/context/ToastContext';
import { Card, Button, Badge, LoadingSkeleton, SkeletonCard } from '@/components/ui';

export default function DashboardScreen() {
  const { logout } = useAuth();
  const { theme } = useTheme();
  const { showToast } = useToast();
  const { data: botStatus, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['botStatus'],
    queryFn: () => botService.getStatus(),
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  const handleStartBot = async () => {
    try {
      await botService.start();
      showToast('Bot started successfully', 'success');
      refetch();
    } catch (error) {
      showToast('Failed to start bot', 'error');
      console.error('Error starting bot:', error);
    }
  };

  const handleStopBot = async () => {
    try {
      await botService.stop();
      showToast('Bot stopped successfully', 'success');
      refetch();
    } catch (error) {
      showToast('Failed to stop bot', 'error');
      console.error('Error stopping bot:', error);
    }
  };

  if (isLoading) {
    return (
      <ScrollView style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <View style={[styles.header, { backgroundColor: theme.colors.surface }]}>
          <LoadingSkeleton width={200} height={24} />
          <LoadingSkeleton width={60} height={20} />
        </View>
        <View style={{ padding: theme.spacing.md }}>
          <SkeletonCard style={{ marginBottom: theme.spacing.md }} />
          <SkeletonCard style={{ marginBottom: theme.spacing.md }} />
        </View>
      </ScrollView>
    );
  }

  const isRunning = botStatus?.status === 'running';
  const statusVariant = isRunning ? 'success' : 'error';

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      refreshControl={
        <RefreshControl refreshing={isRefetching} onRefresh={refetch} />
      }
    >
      <View style={[styles.header, { backgroundColor: theme.colors.surface }]}>
        <Text style={[styles.title, { color: theme.colors.text }]}>Market Bot Dashboard</Text>
        <Button
          title="Logout"
          variant="ghost"
          size="sm"
          onPress={logout}
        />
      </View>

      <View style={{ padding: theme.spacing.md }}>
        <Card style={{ marginBottom: theme.spacing.md }}>
          <Text style={[styles.cardTitle, { color: theme.colors.text }]}>Bot Status</Text>
          <View style={styles.statusContainer}>
            <Badge
              label={botStatus?.status?.toUpperCase() || 'UNKNOWN'}
              variant={statusVariant}
              size="md"
            />
          </View>
          <Text style={[styles.modeText, { color: theme.colors.textSecondary }]}>
            Mode: {botStatus?.mode || 'N/A'}
          </Text>
        </Card>

        <Card header="Statistics" style={{ marginBottom: theme.spacing.md }}>
          <View style={[styles.statRow, { borderBottomColor: theme.colors.border }]}>
            <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
              Active Positions:
            </Text>
            <Text style={[styles.statValue, { color: theme.colors.text }]}>
              {botStatus?.active_positions || 0}
            </Text>
          </View>
          <View style={[styles.statRow, { borderBottomColor: theme.colors.border }]}>
            <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
              Pending Orders:
            </Text>
            <Text style={[styles.statValue, { color: theme.colors.text }]}>
              {botStatus?.pending_orders || 0}
            </Text>
          </View>
          <View style={[styles.statRow, { borderBottomColor: theme.colors.border }]}>
            <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
              Available Capital:
            </Text>
            <Text style={[styles.statValue, { color: theme.colors.text }]}>
              ${botStatus?.capital_available?.toFixed(2) || '0.00'}
            </Text>
          </View>
          <View style={[styles.statRow, { borderBottomColor: 'transparent' }]}>
            <Text style={[styles.statLabel, { color: theme.colors.textSecondary }]}>
              Invested:
            </Text>
            <Text style={[styles.statValue, { color: theme.colors.text }]}>
              ${botStatus?.capital_invested?.toFixed(2) || '0.00'}
            </Text>
          </View>
        </Card>

        <View style={styles.controlsContainer}>
          <Button
            title="Start Bot"
            variant="primary"
            size="md"
            onPress={handleStartBot}
            disabled={isRunning}
            style={[styles.controlButton, { backgroundColor: theme.colors.success }]}
          />
          <Button
            title="Stop Bot"
            variant="danger"
            size="md"
            onPress={handleStopBot}
            disabled={!isRunning}
            style={styles.controlButton}
          />
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  statusContainer: {
    marginBottom: 12,
  },
  modeText: {
    fontSize: 14,
  },
  statRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  statLabel: {
    fontSize: 14,
  },
  statValue: {
    fontSize: 14,
    fontWeight: '600',
  },
  controlsContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  controlButton: {
    flex: 1,
  },
});

