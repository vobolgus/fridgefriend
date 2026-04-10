import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

final savedRecipeProvider =
    FutureProvider.family<bool, String>((ref, recipeId) async {
  final dao = ref.watch(appDatabaseProvider).savedRecipeDao;
  return dao.isSaved(recipeId);
});

final recipeDetailProvider =
    FutureProvider.family<Recipe, String>((ref, recipeId) async {
  final apiClient = ref.watch(apiClientProvider);
  return apiClient.getRecipe(recipeId);
});
