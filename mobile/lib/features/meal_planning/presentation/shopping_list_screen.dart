import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fridgefriend_mobile/core/design/colors.dart';
import 'package:fridgefriend_mobile/core/design/spacing.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/empty_state.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/error_view.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/loading_view.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/meal_planning/domain/meal_plan.dart';

class ShoppingListScreen extends ConsumerWidget {
  const ShoppingListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final shoppingItems = ref.watch(shoppingListProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text(
          'Shopping List',
          style: TextStyle(
            fontFamily: 'Inter',
            fontWeight: FontWeight.w900,
            fontSize: 24,
            color: AppColors.textPrimary,
          ),
        ),
        backgroundColor: AppColors.navBarBackground,
        elevation: 0,
        centerTitle: false,
      ),
      body: shoppingItems.when(
        data: (items) {
          if (items.isEmpty) {
            return const EmptyState(
              icon: Icons.shopping_cart_outlined,
              title: 'All stocked up!',
              subtitle: 'Your shopping list is empty. Time to plan some meals!',
            );
          }
          return _ShoppingListContent(items: items);
        },
        error: (error, _) => ErrorView(
          message: 'Failed to load shopping list: $error',
        ),
        loading: () => const LoadingView(message: 'Loading your list...'),
      ),
    );
  }
}

class _ShoppingListContent extends StatefulWidget {
  final List<ShoppingItem> items;

  const _ShoppingListContent({required this.items});

  @override
  State<_ShoppingListContent> createState() => _ShoppingListContentState();
}

class _ShoppingListContentState extends State<_ShoppingListContent> {
  final Set<String> _checkedItems = {};

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding: AppSpacing.screenPadding,
      itemCount: widget.items.length,
      separatorBuilder: (_, __) => const SizedBox(height: AppSpacing.md),
      itemBuilder: (context, index) {
        final item = widget.items[index];
        final isChecked = _checkedItems.contains(item.ingredientName);

        return AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          decoration: BoxDecoration(
            color: isChecked ? AppColors.surfaceVariant : AppColors.surface,
            borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
            border: Border.all(
              color: isChecked ? AppColors.divider : Colors.transparent,
              width: 2,
            ),
            boxShadow: isChecked
                ? []
                : [
                    BoxShadow(
                      color: AppColors.textPrimary.withOpacity(0.05),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    ),
                  ],
          ),
          child: Material(
            color: Colors.transparent,
            borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
            child: InkWell(
              borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
              onTap: () {
                setState(() {
                  if (isChecked) {
                    _checkedItems.remove(item.ingredientName);
                  } else {
                    _checkedItems.add(item.ingredientName);
                  }
                });
              },
              child: Padding(
                padding: AppSpacing.listItemPadding,
                child: Row(
                  children: [
                    Container(
                      width: 28,
                      height: 28,
                      decoration: BoxDecoration(
                        color:
                            isChecked ? AppColors.primary : Colors.transparent,
                        border: Border.all(
                          color: isChecked
                              ? AppColors.primary
                              : AppColors.textSecondary,
                          width: 2.5,
                        ),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: isChecked
                          ? const Icon(
                              Icons.check,
                              color: AppColors.textOnPrimary,
                              size: 18,
                              weight: 900,
                            )
                          : null,
                    ),
                    const SizedBox(width: AppSpacing.lg),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            item.ingredientName,
                            style: TextStyle(
                              fontFamily: 'Inter',
                              fontWeight: FontWeight.w800,
                              fontSize: 18,
                              color: isChecked
                                  ? AppColors.textSecondary
                                  : AppColors.textPrimary,
                              decoration:
                                  isChecked ? TextDecoration.lineThrough : null,
                            ),
                          ),
                          const SizedBox(height: AppSpacing.xs),
                          Text(
                            '${item.quantity} ${item.unit}',
                            style: TextStyle(
                              fontFamily: 'Inter',
                              fontWeight: FontWeight.w600,
                              fontSize: 14,
                              color: AppColors.textSecondary
                                  .withOpacity(isChecked ? 0.5 : 1.0),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
