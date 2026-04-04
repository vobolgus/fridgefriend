import 'package:flutter/material.dart';

import 'package:fridgefriend_mobile/core/design/colors.dart';
import 'package:fridgefriend_mobile/core/design/spacing.dart';

import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';

class RecipeDetailScreen extends StatelessWidget {
  const RecipeDetailScreen({required this.recipe, super.key});

  final Recipe recipe;

  @override
  Widget build(BuildContext context) {
    final substitutions = recipe.substitutions;

    Color progressColor;
    if (recipe.coveragePct > 0.7) {
      progressColor = AppColors.primary;
    } else if (recipe.coveragePct >= 0.4) {
      progressColor = AppColors.thisWeek;
    } else {
      progressColor = AppColors.error;
    }

    return Scaffold(
      appBar: AppBar(title: Text(recipe.title)),
      body: ListView(
        padding: AppSpacing.screenPadding,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Text(
                  recipe.title,
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.md, vertical: AppSpacing.sm),
                decoration: BoxDecoration(
                  color: AppColors.primarySurface,
                  borderRadius: BorderRadius.circular(AppSpacing.chipRadius),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.timer_outlined,
                        size: 16, color: AppColors.primary),
                    const SizedBox(width: AppSpacing.xs),
                    Text(
                      '${recipe.prepMinutes} min',
                      style: const TextStyle(
                        color: AppColors.primary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.xl),
          Container(
            padding: AppSpacing.cardPadding,
            decoration: BoxDecoration(
              color: AppColors.surfaceVariant,
              borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Ingredient Coverage',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                    Text(
                      '${(recipe.coveragePct * 100).toStringAsFixed(0)}%',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: progressColor,
                          ),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.md),
                ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: LinearProgressIndicator(
                    value: recipe.coveragePct,
                    backgroundColor: AppColors.divider,
                    color: progressColor,
                    minHeight: 12,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.xl),
          Text(
            'Ingredients You Have',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
          const SizedBox(height: AppSpacing.md),
          Card(
            elevation: 0,
            color: AppColors.safeLaterSurface,
            margin: const EdgeInsets.only(bottom: AppSpacing.sm),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
            ),
            child: const ListTile(
              contentPadding: EdgeInsets.symmetric(horizontal: AppSpacing.md),
              leading:
                  Icon(Icons.check_circle_rounded, color: AppColors.primary),
              title: Text(
                'On hand items',
                style: TextStyle(
                    fontWeight: FontWeight.w600, color: AppColors.primaryDark),
              ),
              subtitle: Text(
                'Based on your coverage score',
                style: TextStyle(color: AppColors.primaryDark),
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.xl),
          Text(
            'Missing Items',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
          const SizedBox(height: AppSpacing.md),
          if (recipe.missingItems.isEmpty)
            Card(
              elevation: 0,
              color: AppColors.safeLaterSurface,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
              ),
              child: const Padding(
                padding: AppSpacing.cardPadding,
                child: Row(
                  children: [
                    Icon(Icons.check_circle_outline, color: AppColors.primary),
                    SizedBox(width: AppSpacing.md),
                    Text('You have all ingredients!'),
                  ],
                ),
              ),
            )
          else
            ...recipe.missingItems.map(
              (item) => Card(
                elevation: 0,
                color: AppColors.errorLight,
                margin: const EdgeInsets.only(bottom: AppSpacing.sm),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
                ),
                child: ListTile(
                  contentPadding:
                      const EdgeInsets.symmetric(horizontal: AppSpacing.md),
                  leading:
                      const Icon(Icons.close_rounded, color: AppColors.error),
                  title: Text(
                    item,
                    style: const TextStyle(
                        fontWeight: FontWeight.w600, color: AppColors.error),
                  ),
                ),
              ),
            ),
          const SizedBox(height: AppSpacing.xl),
          Text(
            'Substitutions',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
          const SizedBox(height: AppSpacing.md),
          if (substitutions.isEmpty)
            const Text(
              'No substitutions suggested',
              style: TextStyle(color: AppColors.textSecondary),
            )
          else
            ...substitutions.map(
              (sub) => Card(
                elevation: 0,
                color: AppColors.todaySurface,
                margin: const EdgeInsets.only(bottom: AppSpacing.sm),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
                ),
                child: ListTile(
                  contentPadding:
                      const EdgeInsets.symmetric(horizontal: AppSpacing.md),
                  leading: const Icon(Icons.swap_horiz_rounded,
                      color: AppColors.today),
                  title: Text(
                    sub,
                    style: const TextStyle(
                        fontWeight: FontWeight.w600, color: AppColors.today),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
