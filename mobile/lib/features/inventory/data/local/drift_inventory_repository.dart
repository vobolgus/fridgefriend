import 'package:drift/drift.dart';

import 'package:fridgefriend_mobile/database/app_database.dart';
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
  Future<List<InventoryItem>> syncInventoryItems() => getInventoryItems();

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
  }) async {
    final item = InventoryItem(
      id: 'local_${DateTime.now().microsecondsSinceEpoch}',
      displayName: displayName,
      quantity: quantity,
      unit: unit,
      storageLocation: storageLocation,
      estimatedExpiryDate:
          estimatedExpiryDate ?? DateTime.now().add(const Duration(days: 7)),
      confidence: confidence ?? 0.5,
      status: 'active',
      source: source ?? 'manual',
      canonicalName: canonicalName,
      canonicalIngredientId: canonicalIngredientId,
    );

    await _inventoryDao.insertItem(
      InventoryItemsTableCompanion.insert(
        id: item.id,
        displayName: item.displayName,
        quantity: item.quantity,
        unit: item.unit,
        storageLocation: item.storageLocation,
        estimatedExpiryDate: item.estimatedExpiryDate!,
        confidence: item.confidence!,
        status: Value(item.status),
        source: Value(item.source),
        version: Value(item.version),
      ),
    );

    return item;
  }

  @override
  Future<InventoryItem> updateItem({
    required String id,
    String? displayName,
    double? quantity,
    String? unit,
    String? storageLocation,
    DateTime? estimatedExpiryDate,
    int? version,
  }) async {
    await _inventoryDao.updateItem(
      id: id,
      displayName: displayName,
      quantity: quantity,
      unit: unit,
      storageLocation: storageLocation,
      estimatedExpiryDate: estimatedExpiryDate,
      version: version,
    );

    final item = (await _inventoryDao.getAllItems())
        .where((entry) => entry.id == id)
        .map(_mapToDomain)
        .first;
    return item;
  }

  @override
  Future<InventoryItem> updateItemStatus(String id, String status,
      {int? version}) async {
    await _inventoryDao.updateItemStatus(id, status);
    final items = await _inventoryDao.getAllItems();
    final local = items.where((entry) => entry.id == id).firstOrNull;
    if (local != null) {
      return _mapToDomain(local);
    }
    return InventoryItem(
      id: id,
      displayName: '',
      quantity: 0,
      unit: '',
      storageLocation: '',
      status: status,
      source: 'manual',
    );
  }

  @override
  Future<void> undoItem(String id) async {}

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
      version: item.version,
    );
  }
}
