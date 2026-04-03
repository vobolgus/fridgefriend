import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fridgefriend_mobile/core/network/api_client.dart';
import 'package:fridgefriend_mobile/features/inventory/data/inventory_repository_impl.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_repository.dart';
import 'package:fridgefriend_mobile/features/meal_planning/domain/meal_plan.dart';
import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

final inventoryRepositoryProvider = Provider<InventoryRepository>(
  (ref) => InventoryRepositoryImpl(ref.watch(apiClientProvider)),
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
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  Future<void> addItem({
    required String displayName,
    required double quantity,
    required String unit,
    required String storageLocation,
  }) async {
    try {
      final createdItem = await _repository.createInventoryItem(
        displayName: displayName,
        quantity: quantity,
        unit: unit,
        storageLocation: storageLocation,
      );

      final currentItems = state.valueOrNull ?? const <InventoryItem>[];
      state = AsyncValue.data([...currentItems, createdItem]);
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  Future<void> markUsed(String itemId) => _updateStatus(itemId, 'used');

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

final recommendationsProvider = FutureProvider<List<Recipe>>((ref) {
  return ref.watch(apiClientProvider).getRecommendations();
});

final mealPlanProvider = FutureProvider<MealPlan>((ref) {
  return ref.watch(apiClientProvider).generatePlan();
});

final shoppingListProvider = FutureProvider<List<ShoppingItem>>((ref) {
  return ref.watch(apiClientProvider).getShoppingList();
});

/// A no-op repository used by [InventoryNotifier.withInitialData].
class _NoopRepository implements InventoryRepository {
  @override
  Future<List<InventoryItem>> getInventoryItems() async => const [];

  @override
  Future<InventoryItem> createInventoryItem({
    required String displayName,
    required double quantity,
    required String unit,
    required String storageLocation,
  }) {
    throw UnimplementedError('_NoopRepository is for testing only');
  }

  @override
  Future<void> updateItemStatus(String id, String status) {
    throw UnimplementedError('_NoopRepository is for testing only');
  }
}
