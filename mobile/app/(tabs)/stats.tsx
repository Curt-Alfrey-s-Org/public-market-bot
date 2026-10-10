import React from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { statsService } from '@/api/services/stats';
import { useTheme } from '@/context/ThemeContext';
import { Card, SkeletonCard } from '@/components/ui';
import { ErrorBoundary } from '@/components/ErrorBoundary';

function StatsScreenContent() {
  const { theme } = useTheme();
  const { data: stats, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['stats'],
    queryFn: () => statsService.getStats(),
  });

  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <View style={[styles.header, { backgroundColor: theme.colors.surface }]}>
          <Text style={[styles.title, { color: theme.colors.text }]}>Analytics</Text>
        </View>
        <View style={{ padding: theme.spacing.md }}>
          <View style={styles.grid}>
            <SkeletonCard style={styles.gridItem} />
            <SkeletonCard style={styles.gridItem} />
            <SkeletonCard style={styles.gridItem} />
            <SkeletonCard style={styles.gridItem} />
          </View>
        </View>
      </View>
    );
  }

  if (!stats) {
    return (
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <View style={[styles.header, { backgroundColor: theme.colors.surface }]}>
          <Text style={[styles.title, { color: theme.colors.text }]}>Analytics</Text>
        </View>
        <View style={styles.emptyContainer}>
          <Ionicons name="stats-chart-outline" size={64} color={theme.colors.border} />
          <Text style={[styles.emptyText, { color: theme.colors.textSecondary }]}>
            No statistics available
          </Text>
          <Text style={[styles.emptySubtext, { color: theme.colors.textSecondary }]}>
            Start trading to see your analytics
          </Text>
        </View>
      </View>
    );
  }

  const isProfitable = stats.total_profit_loss > 0;
  const profitLossColor = isProfitable ? theme.colors.success : theme.colors.error;

  return (
    <ScrollView 
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      refreshControl={
        <RefreshControl refreshing={isRefetching} onRefresh={refetch} />
      }
    >
      <View style={[styles.header, { backgroundColor: theme.colors.surface, borderBottomColor: theme.colors.border }]}>
        <Text style={[styles.title, { color: theme.colors.text }]}>Analytics</Text>
        <Text style={[styles.subtitle, { color: theme.colors.textSecondary }]}>
          Trading performance overview
        </Text>
      </View>

      <View style={{ padding: theme.spacing.md }}>
        {/* Net P&L Card - Prominent */}
        <Card style={{ marginBottom: theme.spacing.md }}>
          <View style={styles.plContainer}>
            <View style={styles.plHeader}>
              <Ionicons 
                name={isProfitable ? 'trending-up' : 'trending-down'} 
                size={32} 
                color={profitLossColor} 
              />
              <Text style={[styles.plLabel, { color: theme.colors.textSecondary }]}>
                Net Profit/Loss
              </Text>
            </View>
            <Text style={[styles.plValue, { color: profitLossColor }]}>
              {isProfitable ? '+' : ''}${stats.total_profit_loss.toFixed(2)}
            </Text>
          </View>
        </Card>

        {/* Key Metrics Grid */}
        <View style={styles.grid}>
          <Card style={styles.gridItem} noPadding>
            <View style={[styles.metricCard, { padding: theme.spacing.md }]}>
              <View style={[styles.metricIconContainer, { backgroundColor: theme.colors.primary + '20' }]}>
                <Ionicons name="swap-horizontal" size={24} color={theme.colors.primary} />
              </View>
              <Text style={[styles.metricValue, { color: theme.colors.text }]}>
                {stats.total_trades}
              </Text>
              <Text style={[styles.metricLabel, { color: theme.colors.textSecondary }]}>
                Total Trades
              </Text>
            </View>
          </Card>

          <Card style={styles.gridItem} noPadding>
            <View style={[styles.metricCard, { padding: theme.spacing.md }]}>
              <View style={[styles.metricIconContainer, { backgroundColor: theme.colors.success + '20' }]}>
                <Ionicons name="trophy" size={24} color={theme.colors.success} />
              </View>
              <Text style={[styles.metricValue, { color: theme.colors.text }]}>
                {stats.win_rate.toFixed(1)}%
              </Text>
              <Text style={[styles.metricLabel, { color: theme.colors.textSecondary }]}>
                Win Rate
              </Text>
            </View>
          </Card>

          <Card style={styles.gridItem} noPadding>
            <View style={[styles.metricCard, { padding: theme.spacing.md }]}>
              <View style={[styles.metricIconContainer, { backgroundColor: theme.colors.info + '20' }]}>
                <Ionicons name="analytics" size={24} color={theme.colors.info} />
              </View>
              <Text style={[styles.metricValue, { color: theme.colors.text }]}>
                ${stats.avg_profit_per_trade.toFixed(2)}
              </Text>
              <Text style={[styles.metricLabel, { color: theme.colors.textSecondary }]}>
                Avg P&L
              </Text>
            </View>
          </Card>

          <Card style={styles.gridItem} noPadding>
            <View style={[styles.metricCard, { padding: theme.spacing.md }]}>
              <View style={[styles.metricIconContainer, { backgroundColor: theme.colors.warning + '20' }]}>
                <Ionicons name="shield-checkmark" size={24} color={theme.colors.warning} />
              </View>
              <Text style={[styles.metricValue, { color: theme.colors.text }]}>
                {stats.sharpe_ratio !== undefined ? stats.sharpe_ratio.toFixed(2) : 'N/A'}
              </Text>
              <Text style={[styles.metricLabel, { color: theme.colors.textSecondary }]}>
                Sharpe Ratio
              </Text>
            </View>
          </Card>
        </View>

        {/* Best & Worst Trades */}
        <Card header="Performance Extremes" style={{ marginBottom: theme.spacing.md }}>
          <View style={styles.extremeRow}>
            <View style={styles.extremeItem}>
              <View style={styles.extremeHeader}>
                <Ionicons name="arrow-up-circle" size={20} color={theme.colors.success} />
                <Text style={[styles.extremeLabel, { color: theme.colors.textSecondary }]}>
                  Best Trade
                </Text>
              </View>
              <Text style={[styles.extremeValue, { color: theme.colors.success }]}>
                +${stats.best_trade.toFixed(2)}
              </Text>
            </View>
            <View style={[styles.extremeDivider, { backgroundColor: theme.colors.border }]} />
            <View style={styles.extremeItem}>
              <View style={styles.extremeHeader}>
                <Ionicons name="arrow-down-circle" size={20} color={theme.colors.error} />
                <Text style={[styles.extremeLabel, { color: theme.colors.textSecondary }]}>
                  Worst Trade
                </Text>
              </View>
              <Text style={[styles.extremeValue, { color: theme.colors.error }]}>
                ${stats.worst_trade.toFixed(2)}
              </Text>
            </View>
          </View>
        </Card>

        {/* Max Drawdown */}
        {stats.max_drawdown !== undefined && (
          <Card header="Risk Metrics" style={{ marginBottom: theme.spacing.md }}>
            <View style={styles.detailRow}>
              <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>
                Maximum Drawdown
              </Text>
              <Text style={[styles.detailValue, { color: theme.colors.error }]}>
                {stats.max_drawdown.toFixed(2)}%
              </Text>
            </View>
          </Card>
        )}
      </View>
    </ScrollView>
  );
}

export default function StatsScreen() {
  return (
    <ErrorBoundary>
      <StatsScreenContent />
    </ErrorBoundary>
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
  subtitle: {
    fontSize: 14,
    marginTop: 4,
  },
  plContainer: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  plHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  plLabel: {
    fontSize: 16,
  },
  plValue: {
    fontSize: 40,
    fontWeight: 'bold',
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 12,
  },
  gridItem: {
    flex: 1,
    minWidth: '45%',
  },
  metricCard: {
    alignItems: 'center',
  },
  metricIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  metricValue: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  metricLabel: {
    fontSize: 12,
    textAlign: 'center',
  },
  extremeRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  extremeItem: {
    flex: 1,
    alignItems: 'center',
  },
  extremeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  extremeLabel: {
    fontSize: 14,
  },
  extremeValue: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  extremeDivider: {
    width: 1,
    height: 60,
    marginHorizontal: 16,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  detailLabel: {
    fontSize: 14,
  },
  detailValue: {
    fontSize: 16,
    fontWeight: '600',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    marginTop: 8,
    textAlign: 'center',
  },
});
