import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';

abstract class InventoryRepository {
  Future<List<InventoryItem>> getInventoryItems();

  Future<List<InventoryItem>> syncInventoryItems();

  Future<InventoryItem> createInventoryItem({
    required String displayName,
    required double quantity,
    required String unit,
    required String storageLocation,
  });

  Future<void> updateItemStatus(String id, String status);
}
