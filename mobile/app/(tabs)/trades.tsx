import React, { useState, useMemo } from 'react';
import { View, Text, StyleSheet, FlatList, RefreshControl, TextInput, TouchableOpacity, Modal } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { tradesService } from '@/api/services/trades';
import { Trade } from '@/types';
import { useTheme } from '@/context/ThemeContext';
import { Card, Badge, SkeletonCard, Button } from '@/components/ui';
import { ErrorBoundary } from '@/components/ErrorBoundary';

type SortOption = 'newest' | 'oldest' | 'highest_value' | 'lowest_value';
type StatusFilter = 'all' | 'filled' | 'pending' | 'canceled';

function TradesScreenContent() {
  const { theme } = useTheme();
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilterModal, setShowFilterModal] = useState(false);
  const [sortBy, setSortBy] = useState<SortOption>('newest');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  
  const { data: tradesData, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['trades'],
    queryFn: () => tradesService.getTrades(50, 0),
  });

  // Filter and sort trades
  const filteredTrades = useMemo(() => {
    let trades = tradesData?.trades || [];

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      trades = trades.filter(trade => 
        trade.symbol.toLowerCase().includes(query) ||
        trade.id.toLowerCase().includes(query)
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      trades = trades.filter(trade => trade.status === statusFilter);
    }

    // Apply sorting
    const sorted = [...trades];
    switch (sortBy) {
      case 'newest':
        sorted.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
        break;
      case 'oldest':
        sorted.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
        break;
      case 'highest_value':
        sorted.sort((a, b) => b.total_value - a.total_value);
        break;
      case 'lowest_value':
        sorted.sort((a, b) => a.total_value - b.total_value);
        break;
    }

    return sorted;
  }, [tradesData?.trades, searchQuery, statusFilter, sortBy]);

  const activeFilterCount = (searchQuery ? 1 : 0) + (statusFilter !== 'all' ? 1 : 0) + (sortBy !== 'newest' ? 1 : 0);

  const handleClearFilters = () => {
    setSearchQuery('');
    setStatusFilter('all');
    setSortBy('newest');
    setShowFilterModal(false);
  };

  const renderTrade = ({ item }: { item: Trade }) => {
    const isBuy = item.side === 'buy';
    const sideVariant = isBuy ? 'success' : 'error';
    const statusVariant = item.status === 'filled' ? 'success' : 
                         item.status === 'canceled' ? 'error' : 'info';

    return (
      <TouchableOpacity onPress={() => router.push(`/trade/${item.id}`)}>
        <Card style={{ marginBottom: theme.spacing.md }} noPadding>
          <View style={{ padding: theme.spacing.md }}>
            <View style={styles.tradeHeader}>
              <Text style={[styles.symbol, { color: theme.colors.text }]}>{item.symbol}</Text>
              <Badge label={item.side.toUpperCase()} variant={sideVariant} size="sm" />
            </View>
            <View style={styles.tradeDetails}>
              <View style={styles.tradeRow}>
                <Text style={[styles.label, { color: theme.colors.textSecondary }]}>Quantity:</Text>
                <Text style={[styles.value, { color: theme.colors.text }]}>{item.quantity}</Text>
              </View>
              <View style={styles.tradeRow}>
                <Text style={[styles.label, { color: theme.colors.textSecondary }]}>Price:</Text>
                <Text style={[styles.value, { color: theme.colors.text }]}>
                  ${item.price.toFixed(2)}
                </Text>
              </View>
              <View style={styles.tradeRow}>
                <Text style={[styles.label, { color: theme.colors.textSecondary }]}>Total:</Text>
                <Text style={[styles.value, { color: theme.colors.text }]}>
                  ${item.total_value.toFixed(2)}
                </Text>
              </View>
              <View style={styles.tradeRow}>
                <Text style={[styles.label, { color: theme.colors.textSecondary }]}>Status:</Text>
                <Badge label={item.status.toUpperCase()} variant={statusVariant} size="sm" />
              </View>
              <Text style={[styles.timestamp, { color: theme.colors.textSecondary }]}>
                {new Date(item.timestamp).toLocaleString()}
              </Text>
            </View>
          </View>
        </Card>
      </TouchableOpacity>
    );
  };

  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <View style={[styles.header, { backgroundColor: theme.colors.surface }]}>
          <Text style={[styles.title, { color: theme.colors.text }]}>Trade History</Text>
        </View>
        <View style={{ padding: theme.spacing.md }}>
          <SkeletonCard style={{ marginBottom: theme.spacing.md }} />
          <SkeletonCard style={{ marginBottom: theme.spacing.md }} />
          <SkeletonCard />
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={[styles.header, { backgroundColor: theme.colors.surface, borderBottomColor: theme.colors.border }]}>
        <Text style={[styles.title, { color: theme.colors.text }]}>Trade History</Text>
        <Text style={[styles.subtitle, { color: theme.colors.textSecondary }]}>
          {filteredTrades.length} of {tradesData?.total || 0} trades
        </Text>
      </View>

      {/* Search Bar */}
      <View style={[styles.searchContainer, { backgroundColor: theme.colors.surface, borderBottomColor: theme.colors.border }]}>
        <View style={[styles.searchInputContainer, { backgroundColor: theme.colors.background, borderColor: theme.colors.border }]}>
          <Ionicons name="search" size={20} color={theme.colors.textSecondary} />
          <TextInput
            style={[styles.searchInput, { color: theme.colors.text }]}
            placeholder="Search by symbol or ID..."
            placeholderTextColor={theme.colors.textSecondary}
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
          {searchQuery ? (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Ionicons name="close-circle" size={20} color={theme.colors.textSecondary} />
            </TouchableOpacity>
          ) : null}
        </View>
        <TouchableOpacity 
          style={[styles.filterButton, { backgroundColor: theme.colors.primary }]}
          onPress={() => setShowFilterModal(true)}
        >
          <Ionicons name="options" size={20} color="#ffffff" />
          {activeFilterCount > 0 && (
            <View style={[styles.filterBadge, { backgroundColor: theme.colors.error }]}>
              <Text style={styles.filterBadgeText}>{activeFilterCount}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>
      
      <FlatList
        data={filteredTrades}
        renderItem={renderTrade}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContainer}
        refreshControl={
          <RefreshControl refreshing={isRefetching} onRefresh={refetch} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Ionicons name="file-tray-outline" size={64} color={theme.colors.border} />
            <Text style={[styles.emptyText, { color: theme.colors.textSecondary }]}>
              {searchQuery || statusFilter !== 'all' ? 'No matching trades' : 'No trades yet'}
            </Text>
            <Text style={[styles.emptySubtext, { color: theme.colors.textSecondary }]}>
              {searchQuery || statusFilter !== 'all' 
                ? 'Try adjusting your filters' 
                : 'Your trade history will appear here'}
            </Text>
          </View>
        }
      />

      {/* Filter Modal */}
      <Modal
        visible={showFilterModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowFilterModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { backgroundColor: theme.colors.surface }]}>
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: theme.colors.text }]}>
                Filters & Sorting
              </Text>
              <TouchableOpacity onPress={() => setShowFilterModal(false)}>
                <Ionicons name="close" size={24} color={theme.colors.text} />
              </TouchableOpacity>
            </View>

            {/* Status Filter */}
            <View style={styles.filterSection}>
              <Text style={[styles.filterSectionTitle, { color: theme.colors.text }]}>
                Status
              </Text>
              <View style={styles.filterOptions}>
                {(['all', 'filled', 'pending', 'canceled'] as StatusFilter[]).map((status) => (
                  <TouchableOpacity
                    key={status}
                    style={[
                      styles.filterOption,
                      { borderColor: theme.colors.border },
                      statusFilter === status && { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary }
                    ]}
                    onPress={() => setStatusFilter(status)}
                  >
                    <Text style={[
                      styles.filterOptionText,
                      { color: theme.colors.text },
                      statusFilter === status && { color: '#ffffff' }
                    ]}>
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            {/* Sort By */}
            <View style={styles.filterSection}>
              <Text style={[styles.filterSectionTitle, { color: theme.colors.text }]}>
                Sort By
              </Text>
              <View style={styles.filterOptions}>
                {([
                  { value: 'newest', label: 'Newest' },
                  { value: 'oldest', label: 'Oldest' },
                  { value: 'highest_value', label: 'Highest Value' },
                  { value: 'lowest_value', label: 'Lowest Value' },
                ] as { value: SortOption; label: string }[]).map(({ value, label }) => (
                  <TouchableOpacity
                    key={value}
                    style={[
                      styles.filterOption,
                      { borderColor: theme.colors.border },
                      sortBy === value && { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary }
                    ]}
                    onPress={() => setSortBy(value)}
                  >
                    <Text style={[
                      styles.filterOptionText,
                      { color: theme.colors.text },
                      sortBy === value && { color: '#ffffff' }
                    ]}>
                      {label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            {/* Action Buttons */}
            <View style={styles.modalActions}>
              <Button
                label="Clear All"
                onPress={handleClearFilters}
                variant="outline"
                style={{ flex: 1 }}
              />
              <Button
                label="Apply"
                onPress={() => setShowFilterModal(false)}
                style={{ flex: 1 }}
              />
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

export default function TradesScreen() {
  return (
    <ErrorBoundary>
      <TradesScreenContent />
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
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    gap: 8,
    borderBottomWidth: 1,
  },
  searchInputContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    gap: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
  },
  filterButton: {
    width: 44,
    height: 44,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  filterBadge: {
    position: 'absolute',
    top: -4,
    right: -4,
    width: 18,
    height: 18,
    borderRadius: 9,
    justifyContent: 'center',
    alignItems: 'center',
  },
  filterBadgeText: {
    color: '#ffffff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  listContainer: {
    padding: 16,
  },
  tradeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  symbol: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  tradeDetails: {
    gap: 8,
  },
  tradeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  label: {
    fontSize: 14,
  },
  value: {
    fontSize: 14,
    fontWeight: '500',
  },
  timestamp: {
    fontSize: 12,
    marginTop: 8,
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
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
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  filterSection: {
    marginBottom: 20,
  },
  filterSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  filterOptions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  filterOption: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
  },
  filterOptionText: {
    fontSize: 14,
    fontWeight: '500',
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 20,
  },
});

