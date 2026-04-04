import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

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
            return const Center(child: Text('No inventory items yet'));
          }

          return RefreshIndicator(
            onRefresh: () => ref.read(inventoryProvider.notifier).loadItems(),
            child: ListView.builder(
              itemCount: inventoryItems.length,
              itemBuilder: (context, index) {
                final item = inventoryItems[index];
                final badgeColor = _badgeColor(item.urgencyBucket);

                return ListTile(
                  title: Text(item.displayName),
                  subtitle: Text(
                    '${item.quantity.toStringAsFixed(item.quantity.truncateToDouble() == item.quantity ? 0 : 1)} ${item.unit} • ${item.storageLocation}',
                  ),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      DecoratedBox(
                        decoration: BoxDecoration(
                          color: badgeColor,
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 6,
                          ),
                          child: Text(
                            _urgencyLabel(item.urgencyBucket),
                            style: const TextStyle(color: Colors.white),
                          ),
                        ),
                      ),
                      PopupMenuButton<String>(
                        onSelected: (value) {
                          final notifier = ref.read(inventoryProvider.notifier);
                          if (value == 'used') {
                            notifier.markUsed(item.id);
                          } else if (value == 'discarded') {
                            notifier.markDiscarded(item.id);
                          } else if (value == 'frozen') {
                            notifier.markFrozen(item.id);
                          }
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text('Item marked as $value'),
                              action: SnackBarAction(
                                label: 'Undo',
                                onPressed: () {
                                  notifier.undoItem(item.id);
                                },
                              ),
                            ),
                          );
                        },
                        itemBuilder: (context) => [
                          const PopupMenuItem(
                            value: 'used',
                            child: Text('Mark Used'),
                          ),
                          const PopupMenuItem(
                            value: 'discarded',
                            child: Text('Mark Discarded'),
                          ),
                          const PopupMenuItem(
                            value: 'frozen',
                            child: Text('Mark Frozen'),
                          ),
                        ],
                      ),
                    ],
                  ),
                );
              },
            ),
          );
        },
        error: (error, _) => Center(child: Text('Failed to load inventory: $error')),
        loading: () => const Center(child: CircularProgressIndicator()),
      ),
    );
  }

  Color _badgeColor(String urgencyBucket) {
    switch (urgencyBucket) {
      case 'expired':
      case 'today':
        return Colors.red;
      case 'this_week':
        return Colors.orange;
      case 'safe_later':
        return Colors.green;
      default:
        return Colors.blueGrey;
    }
  }

  String _urgencyLabel(String urgencyBucket) {
    switch (urgencyBucket) {
      case 'expired':
        return 'Expired';
      case 'today':
        return 'Today';
      case 'this_week':
        return 'This Week';
      case 'safe_later':
        return 'Safe Later';
      default:
        return urgencyBucket;
    }
  }
}
