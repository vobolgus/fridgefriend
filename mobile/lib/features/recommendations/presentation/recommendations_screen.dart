import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:fridgefriend_mobile/core/design/colors.dart';
import 'package:fridgefriend_mobile/core/design/spacing.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/empty_state.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/error_view.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/loading_view.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/animated_list_item.dart';

import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

class RecommendationsScreen extends ConsumerWidget {
  const RecommendationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recommendations = ref.watch(recommendationsProvider);

    return Scaffold(
      body: recommendations.when(
        data: (recipes) {
          if (recipes.isEmpty) {
            return const EmptyState(
              icon: Icons.restaurant_menu_outlined,
              title: 'No recipes yet',
              subtitle: 'Add items to get personalized recommendations',
            );
          }

          return ListView.builder(
            padding: AppSpacing.screenPadding,
            itemCount: recipes.length,
            itemBuilder: (context, index) {
              final recipe = recipes[index];

              Color progressColor;
              if (recipe.coveragePct > 0.7) {
                progressColor = AppColors.primary;
              } else if (recipe.coveragePct >= 0.4) {
                progressColor = AppColors.thisWeek;
              } else {
                progressColor = AppColors.error;
              }

              return AnimatedListItem(
                index: index,
                child: Card(
                  margin: const EdgeInsets.only(bottom: AppSpacing.lg),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
                  ),
                  elevation: 2,
                  child: InkWell(
                    borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
                    onTap: () {
                      HapticFeedback.lightImpact();
                      context.push('/recipes/${recipe.id}', extra: recipe);
                    },
                    child: Padding(
                      padding: AppSpacing.cardPadding,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            recipe.title,
                            style: Theme.of(context)
                                .textTheme
                                .titleLarge
                                ?.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.textPrimary,
                                ),
                          ),
                          const SizedBox(height: AppSpacing.md),
                          Row(
                            children: [
                              Text(
                                'Coverage: ${(recipe.coveragePct * 100).toStringAsFixed(0)}%',
                                style: Theme.of(context)
                                    .textTheme
                                    .bodyMedium
                                    ?.copyWith(
                                      fontWeight: FontWeight.bold,
                                      color: progressColor,
                                    ),
                              ),
                              const SizedBox(width: AppSpacing.sm),
                              Expanded(
                                child: ClipRRect(
                                  borderRadius: BorderRadius.circular(4),
                                  child: LinearProgressIndicator(
                                    value: recipe.coveragePct,
                                    backgroundColor: AppColors.surfaceVariant,
                                    color: progressColor,
                                    minHeight: 8,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: AppSpacing.md),
                          Row(
                            children: [
                              const Icon(Icons.timer_outlined,
                                  size: 16, color: AppColors.textSecondary),
                              const SizedBox(width: 4),
                              Text(
                                '${recipe.prepMinutes} min',
                                style: Theme.of(context)
                                    .textTheme
                                    .bodyMedium
                                    ?.copyWith(
                                      color: AppColors.textSecondary,
                                    ),
                              ),
                              const SizedBox(width: AppSpacing.xl),
                              const Icon(Icons.inventory_2_outlined,
                                  size: 16, color: AppColors.textSecondary),
                              const SizedBox(width: 4),
                              Text(
                                '${recipe.missingItems.length} missing',
                                style: Theme.of(context)
                                    .textTheme
                                    .bodyMedium
                                    ?.copyWith(
                                      color: AppColors.textSecondary,
                                    ),
                              ),
                            ],
                          ),
                          if (recipe.missingItems.isNotEmpty) ...[
                            const SizedBox(height: AppSpacing.md),
                            Wrap(
                              spacing: AppSpacing.xs,
                              runSpacing: AppSpacing.xs,
                              children: recipe.missingItems.map((item) {
                                return Chip(
                                  label: Text(item),
                                  labelStyle: Theme.of(context)
                                      .textTheme
                                      .bodySmall
                                      ?.copyWith(
                                        color: AppColors.error,
                                        fontWeight: FontWeight.w600,
                                      ),
                                  backgroundColor: AppColors.errorLight,
                                  side: BorderSide.none,
                                  padding: EdgeInsets.zero,
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(
                                        AppSpacing.chipRadius),
                                  ),
                                );
                              }).toList(),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                ),
              );
            },
          );
        },
        error: (error, _) => ErrorView(message: error.toString()),
        loading: () => const LoadingView(),
      ),
    );
  }
}
