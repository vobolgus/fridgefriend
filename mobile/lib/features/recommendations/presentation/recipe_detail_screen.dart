import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:fridgefriend_mobile/core/design/colors.dart';
import 'package:fridgefriend_mobile/core/design/spacing.dart';
import 'package:fridgefriend_mobile/features/auth/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/recommendations/presentation/providers.dart';

import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';

class RecipeDetailScreen extends ConsumerWidget {
  const RecipeDetailScreen({required this.recipe, super.key});

  final Recipe recipe;

  Widget _buildPlaceholder(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      height: 250,
      width: double.infinity,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [cs.primaryContainer, cs.primary],
        ),
      ),
      child: Center(
        child: Icon(
          Icons.restaurant_menu,
          size: 64,
          color: cs.onPrimary.withValues(alpha: 0.54),
        ),
      ),
    );
  }

  Widget _buildChip(
      BuildContext context, String label, Color bgColor, Color textColor) {
    return Container(
      padding:
          const EdgeInsets.symmetric(horizontal: AppSpacing.sm, vertical: 4),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(AppSpacing.chipRadius),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: textColor,
              fontWeight: FontWeight.bold,
            ),
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cs = Theme.of(context).colorScheme;
    final recipeDetailAsync = ref.watch(recipeDetailProvider(recipe.id));
    final displayedRecipe = recipeDetailAsync.valueOrNull ?? recipe;
    final savedAsync = ref.watch(savedRecipeProvider(recipe.id));
    final isSaved = savedAsync.valueOrNull ?? false;

    final substitutions = displayedRecipe.substitutions;

    Color progressColor;
    if (displayedRecipe.coveragePct > 0.7) {
      progressColor = AppColors.primary;
    } else if (displayedRecipe.coveragePct >= 0.4) {
      progressColor = AppColors.thisWeek;
    } else {
      progressColor = AppColors.error;
    }

    final hasIngredientsData = displayedRecipe.ingredients.isNotEmpty;
    final missingSet = displayedRecipe.missingItems.toSet();

    final haveIngredients = hasIngredientsData
        ? displayedRecipe.ingredients.where((i) {
            final name =
                i['canonical_name']?.toString() ?? i['name']?.toString() ?? '';
            return !missingSet.contains(name);
          }).toList()
        : [];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Recipe Details'),
        elevation: 0,
        actions: [
          IconButton(
            icon: Icon(isSaved ? Icons.bookmark : Icons.bookmark_border),
            onPressed: () async {
              final dao = ref.read(appDatabaseProvider).savedRecipeDao;
              await dao.toggleSave(
                displayedRecipe.id,
                displayedRecipe.title,
                displayedRecipe.imageUrl,
              );
              ref.invalidate(savedRecipeProvider(recipe.id));
              unawaited(
                ref.read(analyticsProvider).track(
                  'recipe_bookmarked',
                  payload: {
                    'recipe_id': displayedRecipe.id,
                    'saved': !isSaved,
                    'missing_item_count': displayedRecipe.missingItems.length,
                    'coverage_pct': displayedRecipe.coveragePct,
                  },
                ),
              );
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                      content:
                          Text(isSaved ? 'Recipe unsaved' : 'Recipe saved!')),
                );
              }
            },
          ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.md),
          child: Row(
            children: [
              if (displayedRecipe.missingItems.isNotEmpty) ...[
                Expanded(
                  child: _AddMissingToShoppingListButton(recipe: displayedRecipe),
                ),
                const SizedBox(width: AppSpacing.md),
              ],
              Expanded(
                child: FilledButton(
                  onPressed: () {
                    _showMealPlanBottomSheet(context, ref, displayedRecipe);
                  },
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: AppColors.textOnPrimary,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(AppSpacing.inputRadius),
                    ),
                    padding: const EdgeInsets.symmetric(vertical: AppSpacing.lg),
                    textStyle: const TextStyle(
                      fontFamily: 'Inter',
                      fontWeight: FontWeight.w700,
                      fontSize: 16,
                    ),
                  ),
                  child: const Text('Add to Meal Plan', textAlign: TextAlign.center),
                ),
              ),
            ],
          ),
        ),
      ),
      body: ListView(
        padding: EdgeInsets.zero,
        children: [
          if (recipeDetailAsync.isLoading)
            const LinearProgressIndicator(minHeight: 2),
          // Hero Image
          Stack(
            children: [
              if (displayedRecipe.imageUrl != null)
                Image.network(
                  displayedRecipe.imageUrl!,
                  height: 250,
                  width: double.infinity,
                  fit: BoxFit.cover,
                  errorBuilder: (context, error, stackTrace) =>
                      _buildPlaceholder(context),
                )
              else
                _buildPlaceholder(context),
              Positioned(
                bottom: 0,
                left: 0,
                right: 0,
                child: Container(
                  height: 120,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [Colors.transparent, AppColors.scrim.withValues(alpha: 0.87)],
                    ),
                  ),
                ),
              ),
              Positioned(
                bottom: AppSpacing.md,
                left: AppSpacing.md,
                right: AppSpacing.md,
                child: Text(
                  displayedRecipe.title,
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: AppColors.textOnDark,
                      ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),

          Padding(
            padding: AppSpacing.screenPadding,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Cuisines & Dietary Tags
                if (displayedRecipe.cuisines.isNotEmpty ||
                    displayedRecipe.dietaryTags.isNotEmpty) ...[
                  Wrap(
                    spacing: AppSpacing.xs,
                    runSpacing: AppSpacing.xs,
                    children: [
                     ...displayedRecipe.cuisines.map((c) => _buildChip(context,
                          c, cs.secondaryContainer, cs.secondary)),
                       ...displayedRecipe.dietaryTags.map((d) => _buildChip(
                          context, d, cs.tertiaryContainer, cs.tertiary)),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.md),
                ],

                // Prep Time & Servings
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: AppSpacing.md, vertical: AppSpacing.sm),
                         decoration: BoxDecoration(
                           color: cs.primaryContainer,
                           borderRadius:
                               BorderRadius.circular(AppSpacing.chipRadius),
                         ),
                         child: Row(
                           mainAxisSize: MainAxisSize.min,
                           children: [
                             const Icon(Icons.timer_outlined,
                                 size: 16, color: AppColors.primary),
                          const SizedBox(width: AppSpacing.xs),
                          Text(
                            '${displayedRecipe.prepMinutes} min',
                            style: const TextStyle(
                                color: AppColors.primary,
                                fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    ),
                    if (displayedRecipe.servings != null) ...[
                      const SizedBox(width: AppSpacing.md),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: AppSpacing.md, vertical: AppSpacing.sm),
                         decoration: BoxDecoration(
                           color: cs.surfaceContainerHigh,
                           borderRadius:
                               BorderRadius.circular(AppSpacing.chipRadius),
                         ),
                         child: Row(
                           mainAxisSize: MainAxisSize.min,
                           children: [
                             Icon(Icons.restaurant_outlined,
                                 size: 16, color: cs.onSurfaceVariant),
                             const SizedBox(width: AppSpacing.xs),
                             Text(
                               '${displayedRecipe.servings} servings',
                               style: TextStyle(
                                   color: cs.onSurfaceVariant,
                                   fontWeight: FontWeight.bold),
                             ),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: AppSpacing.xl),

                // Summary
                if (displayedRecipe.summary != null &&
                    displayedRecipe.summary!.isNotEmpty) ...[
                   Text(
                     displayedRecipe.summary!,
                     style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                           color: cs.onSurfaceVariant,
                           height: 1.5,
                         ),
                   ),
                  const SizedBox(height: AppSpacing.xl),
                ],

                // Coverage
                Container(
                  padding: AppSpacing.cardPadding,
                   decoration: BoxDecoration(
                     color: cs.surfaceContainerHigh,
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
                            style: Theme.of(context)
                                .textTheme
                                .titleMedium
                                ?.copyWith(
                                  fontWeight: FontWeight.bold,
                                ),
                          ),
                          Text(
                            '${(displayedRecipe.coveragePct * 100).toStringAsFixed(0)}%',
                            style: Theme.of(context)
                                .textTheme
                                .titleMedium
                                ?.copyWith(
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
                           value: displayedRecipe.coveragePct,
                           backgroundColor: cs.surfaceContainerHigh,
                           color: progressColor,
                           minHeight: 12,
                         ),
                       ),
                    ],
                  ),
                ),
                const SizedBox(height: AppSpacing.xl),

                // Ingredients
                Text(
                  'Ingredients',
                  style: Theme.of(context)
                      .textTheme
                      .titleLarge
                      ?.copyWith(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: AppSpacing.md),

                // You Have
                Text(
                  'You Have',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: AppColors.primaryDark),
                ),
                const SizedBox(height: AppSpacing.sm),
                if (!hasIngredientsData)
                  Card(
                    elevation: 0,
                    color: AppColors.safeLaterSurface,
                    margin: const EdgeInsets.only(bottom: AppSpacing.md),
                    shape: RoundedRectangleBorder(
                        borderRadius:
                            BorderRadius.circular(AppSpacing.cardRadius)),
                    child: const ListTile(
                      contentPadding:
                          EdgeInsets.symmetric(horizontal: AppSpacing.md),
                      leading: Icon(Icons.check_circle_rounded,
                          color: AppColors.primary),
                      title: Text('On hand items',
                          style: TextStyle(
                              fontWeight: FontWeight.w600,
                              color: AppColors.primaryDark)),
                      subtitle: Text('Based on your coverage score',
                          style: TextStyle(color: AppColors.primaryDark)),
                    ),
                  )
                else if (haveIngredients.isEmpty)
                   Padding(
                     padding: const EdgeInsets.only(bottom: AppSpacing.md),
                     child: Text('No ingredients on hand.',
                         style: TextStyle(color: cs.onSurfaceVariant)),
                   )
                else
                  ...haveIngredients.map((item) {
                    final name = item['canonical_name']?.toString() ??
                        item['name']?.toString() ??
                        'Unknown';
                    final qty = item['quantity']?.toString() ?? '';
                    final unit = item['unit']?.toString() ?? '';
                    return Card(
                      elevation: 0,
                      color: AppColors.safeLaterSurface,
                      margin: const EdgeInsets.only(bottom: AppSpacing.sm),
                      shape: RoundedRectangleBorder(
                          borderRadius:
                              BorderRadius.circular(AppSpacing.cardRadius)),
                      child: ListTile(
                        contentPadding: const EdgeInsets.symmetric(
                            horizontal: AppSpacing.md),
                        leading: const Icon(Icons.check_circle_rounded,
                            color: AppColors.primary),
                        title: Text(name,
                            style: const TextStyle(
                                fontWeight: FontWeight.w600,
                                color: AppColors.primaryDark)),
                        trailing: Text('$qty $unit'.trim(),
                            style: const TextStyle(
                                fontWeight: FontWeight.w600,
                                color: AppColors.primaryDark)),
                      ),
                    );
                  }),

                const SizedBox(height: AppSpacing.md),

                // Missing
                Text(
                  'Missing',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold, color: AppColors.error),
                ),
                const SizedBox(height: AppSpacing.sm),
                if (displayedRecipe.missingItems.isEmpty)
                  Card(
                    elevation: 0,
                    color: AppColors.safeLaterSurface,
                    shape: RoundedRectangleBorder(
                        borderRadius:
                            BorderRadius.circular(AppSpacing.cardRadius)),
                    child: const Padding(
                      padding: AppSpacing.cardPadding,
                      child: Row(
                        children: [
                          Icon(Icons.check_circle_outline,
                              color: AppColors.primary),
                          SizedBox(width: AppSpacing.md),
                          Text('You have all ingredients!'),
                        ],
                      ),
                    ),
                  )
                else if (!hasIngredientsData)
                  ...displayedRecipe.missingItems.map((item) => Card(
                        elevation: 0,
                        color: AppColors.errorLight,
                        margin: const EdgeInsets.only(bottom: AppSpacing.sm),
                        shape: RoundedRectangleBorder(
                            borderRadius:
                                BorderRadius.circular(AppSpacing.cardRadius)),
                        child: ListTile(
                          contentPadding: const EdgeInsets.symmetric(
                              horizontal: AppSpacing.md),
                          leading: const Icon(Icons.close_rounded,
                              color: AppColors.error),
                          title: Text(item,
                              style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                  color: AppColors.error)),
                        ),
                      ))
                else
                  ...displayedRecipe.missingItems.map((missingName) {
                    final item = displayedRecipe.ingredients.firstWhere(
                      (i) =>
                          (i['canonical_name']?.toString() ??
                              i['name']?.toString() ??
                              '') ==
                          missingName,
                      orElse: () => <String, dynamic>{},
                    );
                    final name = missingName;
                    final qty = item['quantity']?.toString() ?? '';
                    final unit = item['unit']?.toString() ?? '';
                    return Card(
                      elevation: 0,
                      color: AppColors.errorLight,
                      margin: const EdgeInsets.only(bottom: AppSpacing.sm),
                      shape: RoundedRectangleBorder(
                          borderRadius:
                              BorderRadius.circular(AppSpacing.cardRadius)),
                      child: ListTile(
                        contentPadding: const EdgeInsets.symmetric(
                            horizontal: AppSpacing.md),
                        leading: const Icon(Icons.close_rounded,
                            color: AppColors.error),
                        title: Text(name,
                            style: const TextStyle(
                                fontWeight: FontWeight.w600,
                                color: AppColors.error)),
                        trailing: Text('$qty $unit'.trim(),
                            style: const TextStyle(
                                fontWeight: FontWeight.w600,
                                color: AppColors.error)),
                      ),
                    );
                  }),

                const SizedBox(height: AppSpacing.xl),

                // Substitutions
                Text(
                  'Substitutions',
                  style: Theme.of(context)
                      .textTheme
                      .titleLarge
                      ?.copyWith(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: AppSpacing.md),
                 if (substitutions.isEmpty)
                   Text('No substitutions suggested',
                       style: TextStyle(color: cs.onSurfaceVariant))
                else
                  ...substitutions.map((sub) => Card(
                        elevation: 0,
                        color: AppColors.todaySurface,
                        margin: const EdgeInsets.only(bottom: AppSpacing.sm),
                        shape: RoundedRectangleBorder(
                            borderRadius:
                                BorderRadius.circular(AppSpacing.cardRadius)),
                        child: ListTile(
                          contentPadding: const EdgeInsets.symmetric(
                              horizontal: AppSpacing.md),
                          leading: const Icon(Icons.swap_horiz_rounded,
                              color: AppColors.today),
                          title: Text(sub,
                              style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                  color: AppColors.today)),
                        ),
                      )),

                // Instructions
                if (displayedRecipe.instructions.isNotEmpty) ...[
                  const SizedBox(height: AppSpacing.xl),
                  Text(
                    'Instructions',
                    style: Theme.of(context)
                        .textTheme
                        .titleLarge
                        ?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: AppSpacing.md),
                   ...displayedRecipe.instructions.map((inst) {
                     final num = inst['number']?.toString() ?? '';
                     final step = inst['step']?.toString() ?? '';
                     return Card(
                       elevation: 0,
                       color: cs.surfaceContainerHigh,
                       margin: const EdgeInsets.only(bottom: AppSpacing.sm),
                      shape: RoundedRectangleBorder(
                          borderRadius:
                              BorderRadius.circular(AppSpacing.cardRadius)),
                      child: Padding(
                        padding: AppSpacing.cardPadding,
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            CircleAvatar(
                              radius: 14,
                              backgroundColor: AppColors.primary,
                              child: Text(num,
                                  style: const TextStyle(
                                      color: AppColors.textOnPrimary,
                                      fontSize: 12,
                                      fontWeight: FontWeight.bold)),
                            ),
                            const SizedBox(width: AppSpacing.md),
                            Expanded(
                              child: Text(step,
                                  style: Theme.of(context)
                                      .textTheme
                                      .bodyMedium
                                      ?.copyWith(height: 1.5)),
                            ),
                          ],
                        ),
                      ),
                    );
                  }),
                ],

                // Nutrition
                if (displayedRecipe.nutrition != null) ...[
                  const SizedBox(height: AppSpacing.xl),
                  Text(
                    'Nutrition',
                    style: Theme.of(context)
                        .textTheme
                        .titleLarge
                        ?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: AppSpacing.md),
                   Card(
                     elevation: 0,
                     color: cs.surfaceContainerHigh,
                     shape: RoundedRectangleBorder(
                         borderRadius:
                             BorderRadius.circular(AppSpacing.cardRadius)),
                     child: Padding(
                       padding: AppSpacing.cardPadding,
                       child: Row(
                         mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          _buildNutritionItem(
                              context,
                              'Calories',
                              '${displayedRecipe.nutrition!['calories'] ?? '-'}',
                              Icons.local_fire_department_outlined,
                              AppColors.accent),
                          _buildNutritionItem(
                              context,
                              'Protein',
                              '${displayedRecipe.nutrition!['protein'] ?? '-'}g',
                              Icons.fitness_center_outlined,
                              AppColors.primary),
                          _buildNutritionItem(
                              context,
                              'Fat',
                              '${displayedRecipe.nutrition!['fat'] ?? '-'}g',
                              Icons.opacity_outlined,
                              AppColors.today),
                          _buildNutritionItem(
                              context,
                              'Carbs',
                              '${displayedRecipe.nutrition!['carbs'] ?? '-'}g',
                              Icons.grass_outlined,
                              AppColors.secondary),
                        ],
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: AppSpacing.xxxl),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _showMealPlanBottomSheet(
    BuildContext context,
    WidgetRef ref,
    Recipe recipe,
  ) {
    int days = 7;
    int servings = 2;
    bool isLoading = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius:
            BorderRadius.vertical(top: Radius.circular(AppSpacing.cardRadius)),
      ),
      builder: (bottomSheetContext) {
        return StatefulBuilder(
          builder: (context, setState) {
            return Padding(
              padding: EdgeInsets.only(
                bottom:
                    MediaQuery.of(context).viewInsets.bottom + AppSpacing.md,
                left: AppSpacing.md,
                right: AppSpacing.md,
                top: AppSpacing.md,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      if (recipe.imageUrl != null)
                        ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.network(recipe.imageUrl!,
                              width: 60, height: 60, fit: BoxFit.cover),
                        )
                      else
                        Container(
                            width: 60,
                            height: 60,
                            color:
                                Theme.of(context).colorScheme.primaryContainer),
                      const SizedBox(width: AppSpacing.md),
                      Expanded(
                        child: Text(
                          'Generate a meal plan featuring ${recipe.title}?',
                          style: Theme.of(context)
                              .textTheme
                              .titleMedium
                              ?.copyWith(fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.xl),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Days',
                          style: TextStyle(
                              fontWeight: FontWeight.bold, fontSize: 16)),
                      DropdownButton<int>(
                        value: days,
                        items: [3, 4, 5, 6, 7]
                            .map((e) => DropdownMenuItem(
                                value: e, child: Text('$e days')))
                            .toList(),
                        onChanged: (v) => setState(() => days = v!),
                      ),
                    ],
                  ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Servings',
                          style: TextStyle(
                              fontWeight: FontWeight.bold, fontSize: 16)),
                      DropdownButton<int>(
                        value: servings,
                        items: [1, 2, 3, 4]
                            .map((e) => DropdownMenuItem(
                                value: e, child: Text('$e servings')))
                            .toList(),
                        onChanged: (v) => setState(() => servings = v!),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.xl),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton(
                      onPressed: isLoading
                          ? null
                          : () async {
                              setState(() => isLoading = true);
                              try {
                                await ref
                                    .read(mealPlanProvider.notifier)
                                    .generatePlan(days: days);
                                if (context.mounted) {
                                  Navigator.pop(context); // close bottom sheet
                                  context.push('/plan',
                                      extra: {'suggestedRecipe': recipe});
                                }
                              } catch (e) {
                                setState(() => isLoading = false);
                                if (context.mounted) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                        content:
                                            Text('Failed to generate plan')),
                                  );
                                }
                              }
                            },
                      style: FilledButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: AppColors.textOnPrimary,
                        padding:
                            const EdgeInsets.symmetric(vertical: AppSpacing.lg),
                      ),
                      child: isLoading
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                  color: AppColors.textOnPrimary, strokeWidth: 2),
                            )
                          : const Text('Generate Plan'),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildNutritionItem(BuildContext context, String label, String value,
      IconData icon, Color color) {
    final cs = Theme.of(context).colorScheme;
    return Column(
      children: [
        Icon(icon, color: color, size: 24),
        const SizedBox(height: AppSpacing.xs),
        Text(value,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold, color: cs.onSurface)),
        Text(label,
            style: Theme.of(context)
                .textTheme
                .bodySmall
                ?.copyWith(color: cs.onSurfaceVariant)),
      ],
    );
  }
}

class _AddMissingToShoppingListButton extends ConsumerStatefulWidget {
  const _AddMissingToShoppingListButton({required this.recipe});

  final Recipe recipe;

  @override
  ConsumerState<_AddMissingToShoppingListButton> createState() =>
      _AddMissingToShoppingListButtonState();
}

class _AddMissingToShoppingListButtonState
    extends ConsumerState<_AddMissingToShoppingListButton> {
  bool _isAdding = false;

  @override
  Widget build(BuildContext context) {
    if (widget.recipe.missingItems.isEmpty) {
      return const SizedBox.shrink();
    }
    final cs = Theme.of(context).colorScheme;
    final count = widget.recipe.missingItems.length;

    return SizedBox(
      width: double.infinity,
      child: FilledButton.tonal(
        onPressed: _isAdding ? null : _handleTap,
        style: FilledButton.styleFrom(
          padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppSpacing.inputRadius),
          ),
        ),
        child: _isAdding
            ? SizedBox(
                height: 20,
                width: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: cs.onSecondaryContainer,
                ),
              )
            : Text(
                'Add $count missing to shopping list',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontFamily: 'Inter',
                  fontWeight: FontWeight.w600,
                  fontSize: 15,
                ),
              ),
      ),
    );
  }

  Future<void> _handleTap() async {
    setState(() => _isAdding = true);
    try {
      final apiClient = ref.read(apiClientProvider);
      final items = widget.recipe.missingItems
          .map((name) => <String, Object?>{
                'name': name,
                'recipe_id': widget.recipe.id,
              })
          .toList();
      await apiClient.addToShoppingList(items: items);
      if (!mounted) return;
      ref.invalidate(shoppingListProvider);
      final count = widget.recipe.missingItems.length;
      unawaited(
        ref.read(analyticsProvider).track(
          'recipe_missing_added_to_shopping_list',
          payload: {
            'recipe_id': widget.recipe.id,
            'count': count,
          },
        ),
      );
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Added $count ${count == 1 ? 'item' : 'items'} to shopping list',
          ),
        ),
      );
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Could not add to shopping list. Try again.'),
        ),
      );
    } finally {
      if (mounted) setState(() => _isAdding = false);
    }
  }
}

