import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:fridgefriend_mobile/core/design/colors.dart';
import 'package:fridgefriend_mobile/core/design/spacing.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/empty_state.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/error_view.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/loading_view.dart';

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
          final expired =
              items.where((i) => i.urgencyBucket == 'expired').toList();
          final today = items.where((i) => i.urgencyBucket == 'today').toList();
          final thisWeek =
              items.where((i) => i.urgencyBucket == 'this_week').toList();
          final safeLater =
              items.where((i) => i.urgencyBucket == 'safe_later').toList();

          if (expired.isEmpty &&
              today.isEmpty &&
              thisWeek.isEmpty &&
              safeLater.isEmpty) {
            return const EmptyState(
              icon: Icons.kitchen_outlined,
              title: 'No items in your inventory',
              subtitle: 'Add items to start tracking expirations.',
            );
          }

          return ListView(
            padding: AppSpacing.screenPadding,
            children: [
              if (expired.isNotEmpty)
                _buildSection(context, 'Expired', expired,
                    AppColors.expiredSurface, AppColors.expired),
              if (today.isNotEmpty)
                _buildSection(context, 'Today', today, AppColors.todaySurface,
                    AppColors.today),
              if (thisWeek.isNotEmpty)
                _buildSection(context, 'This Week', thisWeek,
                    AppColors.thisWeekSurface, AppColors.thisWeek),
              if (safeLater.isNotEmpty)
                _buildSection(context, 'Safe Later', safeLater,
                    AppColors.safeLaterSurface, AppColors.safeLater),
            ],
          );
        },
        error: (error, _) => ErrorView(message: error.toString()),
        loading: () => const LoadingView(),
      ),
    );
  }

  Widget _buildSection(
    BuildContext context,
    String title,
    List<InventoryItem> items,
    Color backgroundColor,
    Color accentColor,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
          child: Container(
            decoration: BoxDecoration(
              border: Border(left: BorderSide(color: accentColor, width: 4)),
            ),
            padding: const EdgeInsets.only(left: AppSpacing.sm),
            child: Text(
              title,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
          ),
        ),
        ...items.map(
          (item) => Card(
            color: backgroundColor,
            margin: const EdgeInsets.only(bottom: AppSpacing.sm),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
            ),
            elevation: 0,
            child: ListTile(
              contentPadding: AppSpacing.listItemPadding,
              leading: Icon(Icons.inventory_2_outlined, color: accentColor),
              title: Text(
                item.displayName,
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              trailing: Text(
                '${item.quantity} ${item.unit}',
                style: const TextStyle(
                  color: AppColors.textSecondary,
                  fontWeight: FontWeight.w600,
                ),
              ),
              onTap: () {
                context.push('/recipes');
              },
            ),
          ),
        ),
        const SizedBox(height: AppSpacing.lg),
      ],
    );
  }
}
