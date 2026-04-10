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

  Widget _buildPlaceholder() {
    return Container(
      height: 160,
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
          size: 48,
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
  Widget build(BuildContext context, WidgetRef ref) {
    final recommendations = ref.watch(recommendationsProvider);
    Object? extra;
    try {
      extra = GoRouterState.of(context).extra;
    } catch (_) {}

    final filterIngredient = extra is Map<String, dynamic>
        ? extra['filterIngredient'] as String?
        : null;

    return Scaffold(
      body: recommendations.when(
        data: (recipes) {
          var displayRecipes = recipes;
          if (filterIngredient != null) {
            final searchStr = filterIngredient.toLowerCase();
            displayRecipes = recipes.where((r) {
              return r.ingredients.any(
                      (i) => i.toString().toLowerCase().contains(searchStr)) ||
                  r.title.toLowerCase().contains(searchStr);
            }).toList();
          }

          return Column(
            children: [
              if (filterIngredient != null)
                Container(
                  color: AppColors.primarySurface,
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.lg,
                    vertical: AppSpacing.md,
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.filter_list, color: AppColors.primary),
                      const SizedBox(width: AppSpacing.sm),
                      Expanded(
                        child: Text(
                          'Recipes using $filterIngredient',
                          style: const TextStyle(
                            color: AppColors.primaryDark,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close,
                            color: AppColors.primaryDark),
                        onPressed: () {
                          context.go('/recipes');
                        },
                      ),
                    ],
                  ),
                ),
              Expanded(
                child: displayRecipes.isEmpty
                    ? EmptyState(
                        icon: filterIngredient != null
                            ? Icons.search_off_outlined
                            : Icons.restaurant_menu_outlined,
                        title: filterIngredient != null
                            ? 'No matches found'
                            : 'No recipes yet',
                        subtitle: filterIngredient != null
                            ? 'Try a different ingredient'
                            : 'Add items to get personalized recommendations',
                        actionLabel:
                            filterIngredient == null ? 'Add Items' : null,
                        onAction: filterIngredient == null
                            ? () => context.go('/')
                            : null,
                      )
                    : ListView.builder(
                        padding: AppSpacing.screenPadding,
                        itemCount: displayRecipes.length,
                        itemBuilder: (context, index) {
                          final recipe = displayRecipes[index];

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
                              margin:
                                  const EdgeInsets.only(bottom: AppSpacing.lg),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(
                                    AppSpacing.cardRadius),
                              ),
                              clipBehavior: Clip.antiAlias,
                              elevation: 2,
                              child: InkWell(
                                borderRadius: BorderRadius.circular(
                                    AppSpacing.cardRadius),
                                onTap: () {
                                  HapticFeedback.lightImpact();
                                  context.push('/recipes/${recipe.id}',
                                      extra: recipe);
                                },
                                child: Column(
                                  crossAxisAlignment:
                                      CrossAxisAlignment.stretch,
                                  children: [
                                    Stack(
                                      children: [
                                        if (recipe.imageUrl != null)
                                          Image.network(
                                            recipe.imageUrl!,
                                            height: 160,
                                            width: double.infinity,
                                            fit: BoxFit.cover,
                                            errorBuilder:
                                                (context, error, stackTrace) =>
                                                    _buildPlaceholder(),
                                          )
                                        else
                                          _buildPlaceholder(),
                                        Positioned(
                                          bottom: 0,
                                          left: 0,
                                          right: 0,
                                          child: Container(
                                            height: 80,
                                            decoration: const BoxDecoration(
                                              gradient: LinearGradient(
                                                begin: Alignment.topCenter,
                                                end: Alignment.bottomCenter,
                                                colors: [
                                                  Colors.transparent,
                                                  Colors.black87
                                                ],
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
                                            style: Theme.of(context)
                                                .textTheme
                                                .titleLarge
                                                ?.copyWith(
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
                                      padding:
                                          const EdgeInsets.all(AppSpacing.md),
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          if (recipe.cuisines.isNotEmpty ||
                                              recipe
                                                  .dietaryTags.isNotEmpty) ...[
                                            Wrap(
                                              spacing: AppSpacing.xs,
                                              runSpacing: AppSpacing.xs,
                                              children: [
                                                ...recipe.cuisines.map((c) =>
                                                    _buildChip(
                                                        context,
                                                        c,
                                                        AppColors
                                                            .secondaryLight,
                                                        AppColors.secondary)),
                                                ...recipe.dietaryTags.map((d) =>
                                                    _buildChip(
                                                        context,
                                                        d,
                                                        AppColors.accentLight,
                                                        AppColors.accent)),
                                              ],
                                            ),
                                            const SizedBox(
                                                height: AppSpacing.md),
                                          ],
                                          Row(
                                            children: [
                                              const Icon(Icons.timer_outlined,
                                                  size: 16,
                                                  color:
                                                      AppColors.textSecondary),
                                              const SizedBox(width: 4),
                                              Text(
                                                '${recipe.prepMinutes} min',
                                                style: Theme.of(context)
                                                    .textTheme
                                                    .bodyMedium
                                                    ?.copyWith(
                                                      color: AppColors
                                                          .textSecondary,
                                                    ),
                                              ),
                                              if (recipe.servings != null) ...[
                                                const SizedBox(
                                                    width: AppSpacing.md),
                                                const Icon(
                                                    Icons.restaurant_outlined,
                                                    size: 16,
                                                    color: AppColors
                                                        .textSecondary),
                                                const SizedBox(width: 4),
                                                Text(
                                                  '${recipe.servings} servings',
                                                  style: Theme.of(context)
                                                      .textTheme
                                                      .bodyMedium
                                                      ?.copyWith(
                                                        color: AppColors
                                                            .textSecondary,
                                                      ),
                                                ),
                                              ],
                                              const Spacer(),
                                              Container(
                                                padding:
                                                    const EdgeInsets.symmetric(
                                                        horizontal:
                                                            AppSpacing.sm,
                                                        vertical: 4),
                                                decoration: BoxDecoration(
                                                  color: progressColor
                                                      .withOpacity(0.1),
                                                  borderRadius:
                                                      BorderRadius.circular(
                                                          AppSpacing
                                                              .chipRadius),
                                                ),
                                                child: Text(
                                                  '${(recipe.coveragePct * 100).toStringAsFixed(0)}% Match',
                                                  style: Theme.of(context)
                                                      .textTheme
                                                      .labelMedium
                                                      ?.copyWith(
                                                        color: progressColor,
                                                        fontWeight:
                                                            FontWeight.bold,
                                                      ),
                                                ),
                                              ),
                                            ],
                                          ),
                                          if (recipe
                                              .missingItems.isNotEmpty) ...[
                                            const SizedBox(
                                                height: AppSpacing.sm),
                                            Text(
                                              'Missing ${recipe.missingItems.length} items',
                                              style: Theme.of(context)
                                                  .textTheme
                                                  .bodySmall
                                                  ?.copyWith(
                                                    color: AppColors.error,
                                                    fontWeight: FontWeight.w600,
                                                  ),
                                            ),
                                          ],
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
        error: (error, _) => ErrorView(message: error.toString()),
        loading: () => const LoadingView(),
      ),
    );
  }
}
