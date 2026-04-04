import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';

abstract class InventoryRepository {
  Future<List<InventoryItem>> getInventoryItems();

  Future<List<InventoryItem>> syncInventoryItems();

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
  });

  Future<InventoryItem> updateItem({
    required String id,
    double? quantity,
    String? unit,
    String? storageLocation,
    DateTime? estimatedExpiryDate,
  });

  Future<void> updateItemStatus(String id, String status);

  Future<void> undoItem(String id);
}
