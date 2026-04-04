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
    String? displayName,
    double? quantity,
    String? unit,
    String? storageLocation,
    DateTime? estimatedExpiryDate,
    int? version,
  });

  Future<InventoryItem> updateItemStatus(String id, String status, {int? version});

  Future<void> undoItem(String id);
}
