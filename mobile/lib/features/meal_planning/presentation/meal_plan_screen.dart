import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:fridgefriend_mobile/core/design/colors.dart';
import 'package:fridgefriend_mobile/core/design/spacing.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/empty_state.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/error_view.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/loading_view.dart';

import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/meal_planning/domain/meal_plan.dart';
import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';

class MealPlanScreen extends ConsumerStatefulWidget {
  const MealPlanScreen({super.key});

  @override
  ConsumerState<MealPlanScreen> createState() => _MealPlanScreenState();
}

class _MealPlanScreenState extends ConsumerState<MealPlanScreen> {
  int _selectedDays = 7;

  @override
  Widget build(BuildContext context) {
    final planState = ref.watch(mealPlanProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Meal Plan')),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(
                AppSpacing.lg, AppSpacing.lg, AppSpacing.lg, 0),
            child: Text(
              'Plan length',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Row(
              children: [
                Expanded(
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: [3, 4, 5, 6, 7].map((days) {
                        final isSelected = days == _selectedDays;
                        return Padding(
                          padding: const EdgeInsets.only(right: AppSpacing.sm),
                          child: ChoiceChip(
                            label: Text('$days Days'),
                            selected: isSelected,
                            onSelected: (selected) {
                              if (selected) {
                                setState(() => _selectedDays = days);
                              }
                            },
                            selectedColor: AppColors.primary,
                            backgroundColor: AppColors.surfaceVariant,
                            side: BorderSide.none,
                            shape: RoundedRectangleBorder(
                              borderRadius:
                                  BorderRadius.circular(AppSpacing.chipRadius),
                            ),
                            labelStyle: TextStyle(
                              color: isSelected
                                  ? AppColors.textOnPrimary
                                  : AppColors.textPrimary,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: _buildPlanContent(planState),
          ),
        ],
      ),
    );
  }

  Widget _buildPlanContent(AsyncValue<MealPlan?> planState) {
    return planState.when(
      data: (mealPlan) {
        if (mealPlan == null || mealPlan.days.isEmpty) {
          return EmptyState(
            icon: Icons.calendar_month_outlined,
            title: 'No meal plan',
            subtitle: 'Generate a plan based on your inventory',
            actionLabel: 'Generate Plan',
            onAction: () {
              ref
                  .read(mealPlanProvider.notifier)
                  .generatePlan(days: _selectedDays);
            },
          );
        }

        return Column(
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
              child: SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: () {
                    ref
                        .read(mealPlanProvider.notifier)
                        .generatePlan(days: _selectedDays);
                  },
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    shape: RoundedRectangleBorder(
                      borderRadius:
                          BorderRadius.circular(AppSpacing.buttonRadius),
                    ),
                    padding:
                        const EdgeInsets.symmetric(vertical: AppSpacing.lg),
                  ),
                  child: const Text('Regenerate Plan',
                      style:
                          TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.lg),
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.fromLTRB(
                    AppSpacing.lg, 0, AppSpacing.lg, AppSpacing.lg),
                itemCount: mealPlan.days.length,
                itemBuilder: (context, index) {
                  final day = mealPlan.days[index];

                  return Card(
                    margin: const EdgeInsets.only(bottom: AppSpacing.md),
                    elevation: 2,
                    shape: RoundedRectangleBorder(
                      borderRadius:
                          BorderRadius.circular(AppSpacing.cardRadius),
                    ),
                    child: InkWell(
                      borderRadius:
                          BorderRadius.circular(AppSpacing.cardRadius),
                      onTap: () {
                        context.push(
                          '/recipes/${day.recipeId}',
                          extra: Recipe(
                            id: day.recipeId,
                            title: day.recipeTitle,
                            coveragePct: 0.0,
                            score: 0.0,
                            prepMinutes: 0,
                            missingItems: const [],
                            substitutions: const [],
                          ),
                        );
                      },
                      child: Padding(
                        padding: AppSpacing.cardPadding,
                        child: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(AppSpacing.md),
                              decoration: const BoxDecoration(
                                color: AppColors.primarySurface,
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(Icons.calendar_today_outlined,
                                  color: AppColors.primary),
                            ),
                            const SizedBox(width: AppSpacing.md),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    _formatDate(day.date),
                                    style: Theme.of(context)
                                        .textTheme
                                        .bodySmall
                                        ?.copyWith(
                                          color: AppColors.textSecondary,
                                          fontWeight: FontWeight.w600,
                                        ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    day.recipeTitle,
                                    style: Theme.of(context)
                                        .textTheme
                                        .titleMedium
                                        ?.copyWith(
                                          fontWeight: FontWeight.bold,
                                          color: AppColors.textPrimary,
                                        ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        );
      },
      error: (error, _) => ErrorView(
        message: error.toString(),
        onRetry: () {
          ref.read(mealPlanProvider.notifier).generatePlan(days: _selectedDays);
        },
      ),
      loading: () => const LoadingView(),
    );
  }

  String _formatDate(DateTime date) {
    final month = date.month.toString().padLeft(2, '0');
    final day = date.day.toString().padLeft(2, '0');
    return '${date.year}-$month-$day';
  }
}
