import 'package:drift/drift.dart';

import 'package:fridgefriend_mobile/database/daos/inventory_dao.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_repository.dart';

class DriftInventoryRepository implements InventoryRepository {
  DriftInventoryRepository(this._inventoryDao);

  final InventoryDao _inventoryDao;

  @override
  Future<List<InventoryItem>> getInventoryItems() async {
    final items = await _inventoryDao.getAllItems();

    return items.map(_mapToDomain).toList(growable: false);
  }

  @override
  Future<InventoryItem> createInventoryItem({
    required String displayName,
    required double quantity,
    required String unit,
    required String storageLocation,
  }) async {
    final item = InventoryItem(
      id: 'local_${DateTime.now().microsecondsSinceEpoch}',
      displayName: displayName,
      quantity: quantity,
      unit: unit,
      storageLocation: storageLocation,
      estimatedExpiryDate: DateTime.now().add(const Duration(days: 7)),
      confidence: 0.5,
      status: 'active',
      source: 'manual',
    );

    await _inventoryDao.insertItem(
      InventoryItemsTableCompanion.insert(
        id: item.id,
        displayName: item.displayName,
        quantity: item.quantity,
        unit: item.unit,
        storageLocation: item.storageLocation,
        estimatedExpiryDate: item.estimatedExpiryDate,
        confidence: item.confidence,
        status: Value(item.status),
        source: Value(item.source),
      ),
    );

    return item;
  }

  @override
  Future<void> updateItemStatus(String id, String status) {
    return _inventoryDao.updateItemStatus(id, status);
  }

  InventoryItem _mapToDomain(InventoryItemsTableData item) {
    return InventoryItem(
      id: item.id,
      displayName: item.displayName,
      quantity: item.quantity,
      unit: item.unit,
      storageLocation: item.storageLocation,
      estimatedExpiryDate: item.estimatedExpiryDate,
      confidence: item.confidence,
      status: item.status,
      source: item.source,
    );
  }
}
