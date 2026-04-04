import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

class UseSoonScreen extends ConsumerWidget {
  const UseSoonScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final itemsAsync = ref.watch(inventoryProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Use Soon')),
      body: itemsAsync.when(
        data: (items) {
          final expired = items.where((i) => i.urgencyBucket == 'expired').toList();
          final today = items.where((i) => i.urgencyBucket == 'today').toList();
          final thisWeek = items.where((i) => i.urgencyBucket == 'this_week').toList();
          final safeLater = items.where((i) => i.urgencyBucket == 'safe_later').toList();

          return ListView(
            padding: const EdgeInsets.all(16.0),
            children: [
              if (expired.isNotEmpty)
                _buildSection(context, 'Expired', expired, Colors.red[100]!),
              if (today.isNotEmpty)
                _buildSection(context, 'Today', today, Colors.orange[100]!),
              if (thisWeek.isNotEmpty)
                _buildSection(context, 'This Week', thisWeek, Colors.yellow[100]!),
              if (safeLater.isNotEmpty)
                _buildSection(context, 'Safe Later', safeLater, Colors.green[100]!),
              if (expired.isEmpty && today.isEmpty && thisWeek.isEmpty && safeLater.isEmpty)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(32.0),
                    child: Text('No items in your inventory.'),
                  ),
                ),
            ],
          );
        },
        error: (error, _) => Center(child: Text('Error: $error')),
        loading: () => const Center(child: CircularProgressIndicator()),
      ),
    );
  }

  Widget _buildSection(
    BuildContext context,
    String title,
    List<InventoryItem> items,
    Color backgroundColor,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8.0),
          child: Text(
            title,
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
        ),
        ...items.map(
          (item) => Card(
            color: backgroundColor,
            margin: const EdgeInsets.only(bottom: 8.0),
            child: ListTile(
              title: Text(item.displayName),
              subtitle: Text('${item.quantity} ${item.unit}'),
              trailing: const Icon(Icons.restaurant_menu),
              onTap: () {
                // In a real app, this might pass the ingredient to the recipes filter
                context.push('/recipes');
              },
            ),
          ),
        ),
        const SizedBox(height: 16),
      ],
    );
  }
}
