import 'dart:async';

import 'package:drift/drift.dart';

import 'package:fridgefriend_mobile/core/network/api_client.dart';
import 'package:fridgefriend_mobile/database/app_database.dart';
import 'package:fridgefriend_mobile/database/daos/inventory_dao.dart';
import 'package:fridgefriend_mobile/database/sync_manager.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_repository.dart';

class InventoryRepositoryImpl implements InventoryRepository {
  InventoryRepositoryImpl(
    this._apiClient, {
    required InventoryDao inventoryDao,
    required SyncManager syncManager,
  }) : _inventoryDao = inventoryDao,
       _syncManager = syncManager;

  final ApiClient _apiClient;
  final InventoryDao _inventoryDao;
  final SyncManager _syncManager;

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
    try {
      final created = await _apiClient.createInventoryItem(
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
      await _cacheItems([created]);
      return created;
    } catch (_) {
      final localItem = InventoryItem(
        id: 'offline_${DateTime.now().microsecondsSinceEpoch}',
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
      await _inventoryDao.insertItem(_toCompanion(localItem));
      await _syncManager.queueCreate(localItem);
      return localItem;
    }
  }

  @override
  Future<List<InventoryItem>> getInventoryItems() async {
    final cached = await _loadCachedItems();
    unawaited(syncInventoryItems());
    return cached;
  }

  @override
  Future<List<InventoryItem>> syncInventoryItems() async {
    await _syncManager.flushPendingMutations();
    final remoteItems = await _apiClient.getInventoryItems();
    await _replaceCache(remoteItems);
    return remoteItems;
  }

  @override
  Future<void> updateItemStatus(String id, String status) async {
    await _inventoryDao.updateItemStatus(id, status);
    try {
      await _apiClient.updateItemStatus(id, status);
    } catch (_) {
      await _syncManager.queueStatusUpdate(itemId: id, status: status);
    }
  }

  @override
  Future<void> undoItem(String id) async {
    await _apiClient.undoItem(id);
  }

  Future<List<InventoryItem>> _loadCachedItems() async {
    final items = await _inventoryDao.getAllItems();
    return items
        .map(
          (item) => InventoryItem(
            id: item.id,
            displayName: item.displayName,
            quantity: item.quantity,
            unit: item.unit,
            storageLocation: item.storageLocation,
            estimatedExpiryDate: item.estimatedExpiryDate,
            confidence: item.confidence,
            status: item.status,
            source: item.source,
          ),
        )
        .toList(growable: false);
  }

  Future<void> _cacheItems(List<InventoryItem> items) async {
    for (final item in items) {
      await _inventoryDao.insertItem(_toCompanion(item));
    }
  }

  Future<void> _replaceCache(List<InventoryItem> items) async {
    await _inventoryDao.clearAll();
    await _cacheItems(items);
  }

  InventoryItemsTableCompanion _toCompanion(InventoryItem item) {
    return InventoryItemsTableCompanion.insert(
      id: item.id,
      displayName: item.displayName,
      quantity: item.quantity,
      unit: item.unit,
      storageLocation: item.storageLocation,
      estimatedExpiryDate: item.estimatedExpiryDate ?? DateTime.now(),
      confidence: item.confidence ?? 0.0,
      status: Value(item.status),
      source: Value(item.source),
    );
  }
}
