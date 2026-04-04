import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fridgefriend_mobile/core/network/api_client.dart';
import 'package:fridgefriend_mobile/database/app_database.dart';
import 'package:fridgefriend_mobile/database/daos/recipe_dao.dart';
import 'package:fridgefriend_mobile/database/sync_manager.dart';
import 'package:fridgefriend_mobile/features/auth/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/inventory/data/inventory_repository_impl.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_repository.dart';
import 'package:fridgefriend_mobile/features/meal_planning/domain/meal_plan.dart';
import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';

final apiClientProvider = Provider<ApiClient>((ref) {
  final authService = ref.watch(authServiceProvider);
  return ApiClient(
    tokenProvider: authService.getToken,
    fallbackToken: useMockAuth ? 'test-token' : null,
  );
});

final appDatabaseProvider = Provider<AppDatabase>((ref) {
  final database = AppDatabase();
  ref.onDispose(database.close);
  return database;
});

final syncManagerProvider = Provider<SyncManager>((ref) {
  final database = ref.watch(appDatabaseProvider);
  return SyncManager(
    database: database,
    apiClient: ref.watch(apiClientProvider),
    inventoryDao: database.inventoryDao,
  );
});

final inventoryRepositoryProvider = Provider<InventoryRepository>(
  (ref) => InventoryRepositoryImpl(
    ref.watch(apiClientProvider),
    inventoryDao: ref.watch(appDatabaseProvider).inventoryDao,
    syncManager: ref.watch(syncManagerProvider),
  ),
);

class InventoryNotifier extends StateNotifier<AsyncValue<List<InventoryItem>>> {
  InventoryNotifier(this._repository) : super(const AsyncValue.loading()) {
    loadItems();
  }

  InventoryNotifier.withInitialData(List<InventoryItem> items)
      : _repository = _NoopRepository(),
        super(AsyncValue.data(items));

  final InventoryRepository _repository;

  Future<void> loadItems() async {
    state = const AsyncValue.loading();
    try {
      final items = await _repository.getInventoryItems();
      state = AsyncValue.data(items);
      unawaited(refreshFromSync());
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  Future<void> refreshFromSync() async {
    try {
      final items = await _repository.syncInventoryItems();
      state = AsyncValue.data(items);
    } catch (_) {
      // Preserve cached state when background sync fails.
    }
  }

  Future<void> addItem({
    required String displayName,
    required double quantity,
    required String unit,
    required String storageLocation,
    String? source,
    String? canonicalName,
    String? canonicalIngredientId,
    double? confidence,
    DateTime? estimatedExpiryDate,
  }) async {
    try {
      final createdItem = await _repository.createInventoryItem(
        displayName: displayName,
        quantity: quantity,
        unit: unit,
        storageLocation: storageLocation,
        source: source,
        canonicalName: canonicalName,
        canonicalIngredientId: canonicalIngredientId,
        confidence: confidence,
        estimatedExpiryDate: estimatedExpiryDate,
      );

      final currentItems = state.valueOrNull ?? const <InventoryItem>[];
      state = AsyncValue.data([...currentItems, createdItem]);
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  Future<void> markUsed(String itemId) => _updateStatus(itemId, 'used');

  Future<void> markDiscarded(String itemId) => _updateStatus(itemId, 'discarded');

  Future<void> markFrozen(String itemId) => _updateStatus(itemId, 'frozen');

  Future<void> undoItem(String itemId) async {
    try {
      await _repository.undoItem(itemId);
      await loadItems();
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  Future<void> _updateStatus(String itemId, String status) async {
    final currentItems = state.valueOrNull ?? const <InventoryItem>[];
    try {
      await _repository.updateItemStatus(itemId, status);
      state = AsyncValue.data(
        currentItems
            .map(
              (item) => item.id == itemId ? item.copyWith(status: status) : item,
            )
            .toList(growable: false),
      );
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }
}

final inventoryProvider =
    StateNotifierProvider<InventoryNotifier, AsyncValue<List<InventoryItem>>>(
      (ref) => InventoryNotifier(ref.watch(inventoryRepositoryProvider)),
    );

final recommendationsProvider = FutureProvider<List<Recipe>>((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final recipeDao = ref.watch(appDatabaseProvider).recipeDao;

  final cached = await recipeDao.getAllRecipes();
  if (cached.isNotEmpty) {
    unawaited(_refreshRecipesInBackground(apiClient, recipeDao));
    return cached.map((recipe) => recipe.toDomain()).toList(growable: false);
  }

  final recipes = await apiClient.getRecommendations();
  await recipeDao.replaceAllRecipes(recipes);
  return recipes;
});

final mealPlanProvider = FutureProvider.family<MealPlan, int>((ref, days) async {
  final apiClient = ref.watch(apiClientProvider);
  final mealPlanDao = ref.watch(appDatabaseProvider).mealPlanDao;

  try {
    final plan = await apiClient.generatePlan(days: days);
    await mealPlanDao.saveMealPlan(plan);
    return plan;
  } catch (_) {
    final cached = await mealPlanDao.getLatestMealPlan();
    if (cached != null) {
      return cached.toDomain();
    }
    rethrow;
  }
});

final shoppingListProvider = FutureProvider<List<ShoppingItem>>((ref) async {
  final apiClient = ref.watch(apiClientProvider);
  final mealPlanDao = ref.watch(appDatabaseProvider).mealPlanDao;

  try {
    return await apiClient.getShoppingList();
  } catch (_) {
    final cached = await mealPlanDao.getLatestMealPlan();
    if (cached != null) {
      return cached.toDomain().shoppingList;
    }
    rethrow;
  }
});

Future<void> _refreshRecipesInBackground(
  ApiClient apiClient,
  RecipeDao recipeDao,
) async {
  try {
    final recipes = await apiClient.getRecommendations();
    await recipeDao.replaceAllRecipes(recipes);
  } catch (_) {
    // Silently fail and preserve cached data.
  }
}

/// A no-op repository used by [InventoryNotifier.withInitialData].
class _NoopRepository implements InventoryRepository {
  @override
  Future<List<InventoryItem>> getInventoryItems() async => const [];

  @override
  Future<List<InventoryItem>> syncInventoryItems() async => const [];

  @override
  Future<InventoryItem> createInventoryItem({
    required String displayName,
    required double quantity,
    required String unit,
    required String storageLocation,
    String? source,
    String? canonicalName,
    String? canonicalIngredientId,
    double? confidence,
    DateTime? estimatedExpiryDate,
  }) {
    throw UnimplementedError('_NoopRepository is for testing only');
  }

  @override
  Future<void> updateItemStatus(String id, String status) async {}

  @override
  Future<void> undoItem(String id) async {}
}
