import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

final savedRecipeProvider =
    FutureProvider.family<bool, String>((ref, recipeId) async {
  final dao = ref.watch(appDatabaseProvider).savedRecipeDao;
  return dao.isSaved(recipeId);
});
