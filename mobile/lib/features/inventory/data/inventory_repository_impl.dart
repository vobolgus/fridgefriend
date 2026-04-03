import 'package:fridgefriend_mobile/core/network/api_client.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_repository.dart';

class InventoryRepositoryImpl implements InventoryRepository {
  const InventoryRepositoryImpl(this._apiClient);

  final ApiClient _apiClient;

  @override
  Future<InventoryItem> createInventoryItem({
    required String displayName,
    required double quantity,
    required String unit,
    required String storageLocation,
  }) {
    return _apiClient.createInventoryItem(
      displayName: displayName,
      quantity: quantity,
      unit: unit,
      storageLocation: storageLocation,
    );
  }

  @override
  Future<List<InventoryItem>> getInventoryItems() {
    return _apiClient.getInventoryItems();
  }

  @override
  Future<void> updateItemStatus(String id, String status) {
    return _apiClient.updateItemStatus(id, status);
  }
}
