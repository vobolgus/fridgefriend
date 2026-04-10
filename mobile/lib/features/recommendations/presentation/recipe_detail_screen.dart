import 'package:flutter/material.dart';

import 'package:fridgefriend_mobile/core/design/colors.dart';
import 'package:fridgefriend_mobile/core/design/spacing.dart';

import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';

class RecipeDetailScreen extends StatelessWidget {
  const RecipeDetailScreen({required this.recipe, super.key});

  final Recipe recipe;

  Widget _buildPlaceholder() {
    return Container(
      height: 250,
      width: double.infinity,
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AppColors.primaryLight, AppColors.primary],
        ),
      ),
      child: const Center(
        child: Icon(
          Icons.restaurant_menu,
          size: 64,
          color: Colors.white54,
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

    final hasIngredientsData = recipe.ingredients.isNotEmpty;
    final missingSet = recipe.missingItems.toSet();

    final haveIngredients = hasIngredientsData
        ? recipe.ingredients.where((i) {
            final name =
                i['canonical_name']?.toString() ?? i['name']?.toString() ?? '';
            return !missingSet.contains(name);
          }).toList()
        : [];

    final missingIngredients = hasIngredientsData
        ? recipe.ingredients.where((i) {
            final name =
                i['canonical_name']?.toString() ?? i['name']?.toString() ?? '';
            return missingSet.contains(name);
          }).toList()
        : [];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Recipe Details'),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.bookmark_border),
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Recipe saved!')),
              );
            },
          ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.md),
          child: SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Recipe added to plan!')),
                );
              },
              style: FilledButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
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
              child: const Text('Add to Meal Plan'),
            ),
          ),
        ),
      ),
      body: ListView(
        padding: EdgeInsets.zero,
        children: [
          // Hero Image
          Stack(
            children: [
              if (recipe.imageUrl != null)
                Image.network(
                  recipe.imageUrl!,
                  height: 250,
                  width: double.infinity,
                  fit: BoxFit.cover,
                  errorBuilder: (context, error, stackTrace) =>
                      _buildPlaceholder(),
                )
              else
                _buildPlaceholder(),
              Positioned(
                bottom: 0,
                left: 0,
                right: 0,
                child: Container(
                  height: 120,
                  decoration: const BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [Colors.transparent, Colors.black87],
                    ),
                  ),
                ),
              ),
              Positioned(
                bottom: AppSpacing.md,
                left: AppSpacing.md,
                right: AppSpacing.md,
                child: Text(
                  recipe.title,
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
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
                if (recipe.cuisines.isNotEmpty ||
                    recipe.dietaryTags.isNotEmpty) ...[
                  Wrap(
                    spacing: AppSpacing.xs,
                    runSpacing: AppSpacing.xs,
                    children: [
                      ...recipe.cuisines.map((c) => _buildChip(context, c,
                          AppColors.secondaryLight, AppColors.secondary)),
                      ...recipe.dietaryTags.map((d) => _buildChip(
                          context, d, AppColors.accentLight, AppColors.accent)),
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
                        color: AppColors.primarySurface,
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
                            '${recipe.prepMinutes} min',
                            style: const TextStyle(
                                color: AppColors.primary,
                                fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    ),
                    if (recipe.servings != null) ...[
                      const SizedBox(width: AppSpacing.md),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: AppSpacing.md, vertical: AppSpacing.sm),
                        decoration: BoxDecoration(
                          color: AppColors.surfaceVariant,
                          borderRadius:
                              BorderRadius.circular(AppSpacing.chipRadius),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(Icons.restaurant_outlined,
                                size: 16, color: AppColors.textSecondary),
                            const SizedBox(width: AppSpacing.xs),
                            Text(
                              '${recipe.servings} servings',
                              style: const TextStyle(
                                  color: AppColors.textSecondary,
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
                if (recipe.summary != null && recipe.summary!.isNotEmpty) ...[
                  Text(
                    recipe.summary!,
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          color: AppColors.textSecondary,
                          height: 1.5,
                        ),
                  ),
                  const SizedBox(height: AppSpacing.xl),
                ],

                // Coverage
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
                            style: Theme.of(context)
                                .textTheme
                                .titleMedium
                                ?.copyWith(
                                  fontWeight: FontWeight.bold,
                                ),
                          ),
                          Text(
                            '${(recipe.coveragePct * 100).toStringAsFixed(0)}%',
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
                  const Padding(
                    padding: EdgeInsets.only(bottom: AppSpacing.md),
                    child: Text('No ingredients on hand.',
                        style: TextStyle(color: AppColors.textSecondary)),
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
                if (recipe.missingItems.isEmpty)
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
                  ...recipe.missingItems.map((item) => Card(
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
                  ...missingIngredients.map((item) {
                    final name = item['canonical_name']?.toString() ??
                        item['name']?.toString() ??
                        'Unknown';
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
                  const Text('No substitutions suggested',
                      style: TextStyle(color: AppColors.textSecondary))
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
                if (recipe.instructions.isNotEmpty) ...[
                  const SizedBox(height: AppSpacing.xl),
                  Text(
                    'Instructions',
                    style: Theme.of(context)
                        .textTheme
                        .titleLarge
                        ?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: AppSpacing.md),
                  ...recipe.instructions.map((inst) {
                    final num = inst['number']?.toString() ?? '';
                    final step = inst['step']?.toString() ?? '';
                    return Card(
                      elevation: 0,
                      color: AppColors.surfaceVariant,
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
                                      color: Colors.white,
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
                if (recipe.nutrition != null) ...[
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
                    color: AppColors.surfaceVariant,
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
                              '${recipe.nutrition!['calories'] ?? '-'}',
                              Icons.local_fire_department_outlined,
                              AppColors.accent),
                          _buildNutritionItem(
                              context,
                              'Protein',
                              '${recipe.nutrition!['protein'] ?? '-'}g',
                              Icons.fitness_center_outlined,
                              AppColors.primary),
                          _buildNutritionItem(
                              context,
                              'Fat',
                              '${recipe.nutrition!['fat'] ?? '-'}g',
                              Icons.opacity_outlined,
                              AppColors.today),
                          _buildNutritionItem(
                              context,
                              'Carbs',
                              '${recipe.nutrition!['carbs'] ?? '-'}g',
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

  Widget _buildNutritionItem(BuildContext context, String label, String value,
      IconData icon, Color color) {
    return Column(
      children: [
        Icon(icon, color: color, size: 24),
        const SizedBox(height: AppSpacing.xs),
        Text(value,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold, color: AppColors.textPrimary)),
        Text(label,
            style: Theme.of(context)
                .textTheme
                .bodySmall
                ?.copyWith(color: AppColors.textSecondary)),
      ],
    );
  }
}
