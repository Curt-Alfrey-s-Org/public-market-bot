import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { tradesService } from '@/api/services/trades';
import { useTheme } from '@/context/ThemeContext';
import { Card, Badge, SkeletonCard } from '@/components/ui';
import { ErrorBoundary } from '@/components/ErrorBoundary';

function TradeDetailContent() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { theme } = useTheme();

  const { data: trade, isLoading, error } = useQuery({
    queryKey: ['trade', id],
    queryFn: () => tradesService.getTrade(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <View style={[styles.header, { backgroundColor: theme.colors.surface }]}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <Ionicons name="arrow-back" size={24} color={theme.colors.text} />
          </TouchableOpacity>
          <Text style={[styles.title, { color: theme.colors.text }]}>Trade Detail</Text>
        </View>
        <View style={{ padding: theme.spacing.md }}>
          <SkeletonCard style={{ marginBottom: theme.spacing.md, height: 200 }} />
          <SkeletonCard style={{ marginBottom: theme.spacing.md, height: 150 }} />
        </View>
      </View>
    );
  }

  if (error || !trade) {
    return (
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <View style={[styles.header, { backgroundColor: theme.colors.surface }]}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <Ionicons name="arrow-back" size={24} color={theme.colors.text} />
          </TouchableOpacity>
          <Text style={[styles.title, { color: theme.colors.text }]}>Trade Detail</Text>
        </View>
        <View style={styles.errorContainer}>
          <Ionicons name="alert-circle-outline" size={64} color={theme.colors.error} />
          <Text style={[styles.errorText, { color: theme.colors.text }]}>
            Trade not found
          </Text>
          <Text style={[styles.errorSubtext, { color: theme.colors.textSecondary }]}>
            This trade may have been deleted or does not exist
          </Text>
        </View>
      </View>
    );
  }

  const isBuy = trade.side === 'buy';
  const sideVariant = isBuy ? 'success' : 'error';
  const statusVariant = trade.status === 'filled' ? 'success' : 
                       trade.status === 'canceled' ? 'error' : 'info';
  
  const hasProfitLoss = trade.profit_loss !== undefined;
  const isProfitable = hasProfitLoss && trade.profit_loss! > 0;
  const profitLossColor = isProfitable ? theme.colors.success : theme.colors.error;

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={[styles.header, { backgroundColor: theme.colors.surface, borderBottomColor: theme.colors.border }]}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={theme.colors.text} />
        </TouchableOpacity>
        <Text style={[styles.title, { color: theme.colors.text }]}>Trade Detail</Text>
      </View>

      <View style={{ padding: theme.spacing.md }}>
        {/* Trade Summary Card */}
        <Card header="Trade Summary" style={{ marginBottom: theme.spacing.md }}>
          <View style={styles.summaryRow}>
            <Text style={[styles.symbol, { color: theme.colors.text }]}>{trade.symbol}</Text>
            <Badge label={trade.side.toUpperCase()} variant={sideVariant} />
          </View>
          <View style={[styles.divider, { backgroundColor: theme.colors.border }]} />
          
          {hasProfitLoss && (
            <View style={styles.profitLossContainer}>
              <Text style={[styles.profitLossLabel, { color: theme.colors.textSecondary }]}>
                Profit/Loss
              </Text>
              <View style={styles.profitLossRow}>
                <Ionicons 
                  name={isProfitable ? 'trending-up' : 'trending-down'} 
                  size={24} 
                  color={profitLossColor} 
                />
                <Text style={[styles.profitLossValue, { color: profitLossColor }]}>
                  ${Math.abs(trade.profit_loss!).toFixed(2)}
                </Text>
                <Text style={[styles.profitLossPercent, { color: profitLossColor }]}>
                  ({isProfitable ? '+' : '-'}{((Math.abs(trade.profit_loss!) / trade.total_value) * 100).toFixed(2)}%)
                </Text>
              </View>
            </View>
          )}

          <View style={styles.detailRow}>
            <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>Status</Text>
            <Badge label={trade.status.toUpperCase()} variant={statusVariant} size="sm" />
          </View>
        </Card>

        {/* Trade Details Card */}
        <Card header="Trade Information" style={{ marginBottom: theme.spacing.md }}>
          <View style={styles.detailRow}>
            <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>Order ID</Text>
            <Text style={[styles.detailValue, { color: theme.colors.text }]}>
              {trade.order_id || trade.id}
            </Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>Quantity</Text>
            <Text style={[styles.detailValue, { color: theme.colors.text }]}>
              {trade.quantity}
            </Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>Price</Text>
            <Text style={[styles.detailValue, { color: theme.colors.text }]}>
              ${trade.price.toFixed(2)}
            </Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>Total Value</Text>
            <Text style={[styles.detailValue, { color: theme.colors.text }]}>
              ${trade.total_value.toFixed(2)}
            </Text>
          </View>
          {trade.commission !== undefined && (
            <View style={styles.detailRow}>
              <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>Commission</Text>
              <Text style={[styles.detailValue, { color: theme.colors.text }]}>
                ${trade.commission.toFixed(2)}
              </Text>
            </View>
          )}
        </Card>

        {/* Timeline Card */}
        <Card header="Timeline" style={{ marginBottom: theme.spacing.md }}>
          <View style={styles.timelineRow}>
            <View style={styles.timelineIcon}>
              <Ionicons name="time-outline" size={20} color={theme.colors.primary} />
            </View>
            <View style={styles.timelineContent}>
              <Text style={[styles.timelineLabel, { color: theme.colors.textSecondary }]}>
                Executed
              </Text>
              <Text style={[styles.timelineValue, { color: theme.colors.text }]}>
                {new Date(trade.timestamp).toLocaleString()}
              </Text>
            </View>
          </View>
        </Card>

        {/* Strategy & Notes Card */}
        {(trade.strategy || trade.notes) && (
          <Card header="Additional Information" style={{ marginBottom: theme.spacing.md }}>
            {trade.strategy && (
              <View style={styles.detailRow}>
                <Text style={[styles.detailLabel, { color: theme.colors.textSecondary }]}>Strategy</Text>
                <Text style={[styles.detailValue, { color: theme.colors.text }]}>
                  {trade.strategy}
                </Text>
              </View>
            )}
            {trade.notes && (
              <View style={{ marginTop: trade.strategy ? theme.spacing.sm : 0 }}>
                <Text style={[styles.detailLabel, { color: theme.colors.textSecondary, marginBottom: 4 }]}>
                  Notes
                </Text>
                <Text style={[styles.notesText, { color: theme.colors.text }]}>
                  {trade.notes}
                </Text>
              </View>
            )}
          </Card>
        )}

        {/* Chart Placeholder */}
        <Card header="Price Chart" style={{ marginBottom: theme.spacing.md }}>
          <View style={[styles.chartPlaceholder, { backgroundColor: theme.colors.background }]}>
            <Ionicons name="bar-chart-outline" size={48} color={theme.colors.border} />
            <Text style={[styles.chartPlaceholderText, { color: theme.colors.textSecondary }]}>
              Chart visualization coming soon
            </Text>
          </View>
        </Card>
      </View>
    </ScrollView>
  );
}

export default function TradeDetailScreen() {
  return (
    <ErrorBoundary>
      <TradeDetailContent />
    </ErrorBoundary>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
  },
  backButton: {
    marginRight: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  symbol: {
    fontSize: 28,
    fontWeight: 'bold',
  },
  divider: {
    height: 1,
    marginVertical: 16,
  },
  profitLossContainer: {
    marginBottom: 16,
  },
  profitLossLabel: {
    fontSize: 14,
    marginBottom: 8,
  },
  profitLossRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  profitLossValue: {
    fontSize: 32,
    fontWeight: 'bold',
  },
  profitLossPercent: {
    fontSize: 18,
    fontWeight: '600',
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  detailLabel: {
    fontSize: 14,
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
  },
  timelineRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  timelineIcon: {
    marginRight: 12,
    marginTop: 2,
  },
  timelineContent: {
    flex: 1,
  },
  timelineLabel: {
    fontSize: 14,
    marginBottom: 4,
  },
  timelineValue: {
    fontSize: 16,
    fontWeight: '600',
  },
  notesText: {
    fontSize: 14,
    lineHeight: 20,
  },
  chartPlaceholder: {
    height: 200,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 8,
  },
  chartPlaceholderText: {
    marginTop: 12,
    fontSize: 14,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  errorText: {
    fontSize: 18,
    fontWeight: '600',
    marginTop: 16,
  },
  errorSubtext: {
    fontSize: 14,
    marginTop: 8,
    textAlign: 'center',
  },
});
