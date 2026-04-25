import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:fridgefriend_mobile/core/design/colors.dart';
import 'package:fridgefriend_mobile/core/design/spacing.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/empty_state.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/error_view.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/loading_view.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/urgency_badge.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/animated_list_item.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

class InventoryScreen extends ConsumerWidget {
  const InventoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final items = ref.watch(inventoryProvider);

    return Scaffold(
      body: items.when(
        data: (inventoryItems) {
          if (inventoryItems.isEmpty) {
            return EmptyState(
              icon: Icons.kitchen_outlined,
              title: 'Your fridge is empty',
              subtitle:
                  'Add items by scanning a barcode, taking a photo, or entering them manually.',
              actionLabel: 'Add First Item',
              onAction: () => context.push('/add-item'),
            );
          }

          final expiringCount = inventoryItems.where((item) {
            return item.urgencyBucket == 'today' ||
                item.urgencyBucket == 'this_week' ||
                item.urgencyBucket == 'expired';
          }).length;

          return RefreshIndicator(
            color: AppColors.primary,
            onRefresh: () => ref.read(inventoryProvider.notifier).loadItems(),
            child: ListView.builder(
              padding: const EdgeInsets.only(top: AppSpacing.sm, bottom: 100),
              itemCount: inventoryItems.length + (expiringCount > 0 ? 1 : 0),
              itemBuilder: (context, index) {
                if (expiringCount > 0 && index == 0) {
                  return _ExpiringBanner(count: expiringCount);
                }

                final item =
                    inventoryItems[index - (expiringCount > 0 ? 1 : 0)];
                return AnimatedListItem(
                  index: index,
                  child: _InventoryTile(item: item),
                );
              },
            ),
          );
        },
        error: (error, _) => ErrorView(
          message: '$error',
          onRetry: () => ref.invalidate(inventoryProvider),
        ),
        loading: () => const LoadingView(message: 'Loading inventory...'),
      ),
    );
  }
}

class _ExpiringBanner extends StatelessWidget {
  const _ExpiringBanner({required this.count});

  final int count;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.fromLTRB(
          AppSpacing.lg, AppSpacing.sm, AppSpacing.lg, AppSpacing.sm),
      child: Material(
        color: cs.tertiaryContainer,
        borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
        child: InkWell(
          borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
          onTap: () {
            HapticFeedback.lightImpact();
            context.push('/use-soon');
          },
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: cs.tertiary,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(Icons.warning_amber_rounded,
                      color: cs.onTertiary, size: 22),
                ),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '$count item${count == 1 ? '' : 's'} expiring soon',
                        style:
                            Theme.of(context).textTheme.titleMedium?.copyWith(
                                  color: cs.onTertiaryContainer,
                                  fontWeight: FontWeight.w600,
                                ),
                      ),
                      Text(
                        'Tap to see what to use first',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: cs.onTertiaryContainer.withValues(alpha: 0.7),
                            ),
                      ),
                    ],
                  ),
                ),
                Icon(Icons.chevron_right_rounded,
                    color: cs.onTertiaryContainer),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _InventoryTile extends ConsumerWidget {
  const _InventoryTile({required this.item});

  final InventoryItem item;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cs = Theme.of(context).colorScheme;
    final quantityStr = item.quantity.truncateToDouble() == item.quantity
        ? item.quantity.toInt().toString()
        : item.quantity.toStringAsFixed(1);

    return Padding(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.lg, vertical: AppSpacing.xs),
      child: Material(
        color: cs.surfaceContainer,
        borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
        child: InkWell(
          borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
          onTap: () => context.push('/add-item', extra: item),
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.md),
            child: Row(
              children: [
                Container(
                  width: 48,
                  height: 48,
                   decoration: BoxDecoration(
                     color: cs.surfaceContainerHigh,
                     borderRadius: BorderRadius.circular(12),
                   ),
                   child: Icon(
                     _storageIcon(item.storageLocation),
                     color: cs.onSurfaceVariant,
                   ),
                ),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        item.displayName,
                        style: Theme.of(context).textTheme.titleMedium,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 2),
                       Text(
                         '$quantityStr ${item.unit} · ${item.storageLocation}',
                         style: Theme.of(context).textTheme.bodySmall?.copyWith(
                               color: cs.onSurfaceVariant,
                             ),
                       ),
                    ],
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                UrgencyBadge(bucket: item.urgencyBucket),
                _buildPopupMenu(context, ref),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildPopupMenu(BuildContext context, WidgetRef ref) {
    return PopupMenuButton<String>(
      icon: Icon(Icons.more_vert_rounded, color: Theme.of(context).colorScheme.onSurfaceVariant),
      onSelected: (value) async {
        if (value != 'edit') {
          HapticFeedback.mediumImpact();
        }
        final notifier = ref.read(inventoryProvider.notifier);
        if (value == 'edit') {
          context.push('/add-item', extra: item);
          return;
        }

        try {
          if (value == 'used') {
            await notifier.markUsed(item.id);
          } else if (value == 'discarded') {
            await notifier.markDiscarded(item.id);
          } else if (value == 'frozen') {
            await notifier.markFrozen(item.id);
          }
          if (!context.mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Item marked as $value'),
              action: SnackBarAction(
                label: 'Undo',
                onPressed: () => notifier.undoItem(item.id),
              ),
            ),
          );
        } on StateError {
          if (!context.mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Conflict: item was modified. Refreshing...'),
            ),
          );
        }
      },
      itemBuilder: (context) => const [
        PopupMenuItem(value: 'edit', child: Text('Edit')),
        PopupMenuItem(value: 'used', child: Text('Mark Used')),
        PopupMenuItem(value: 'discarded', child: Text('Mark Discarded')),
        PopupMenuItem(value: 'frozen', child: Text('Mark Frozen')),
      ],
    );
  }

  static IconData _storageIcon(String location) {
    return switch (location.toLowerCase()) {
      'fridge' || 'refrigerator' => Icons.kitchen_rounded,
      'freezer' => Icons.ac_unit_rounded,
      'pantry' => Icons.shelves,
      'counter' => Icons.countertops_rounded,
      _ => Icons.inventory_2_rounded,
    };
  }
}
