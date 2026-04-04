import 'dart:async';

import 'package:drift/drift.dart';
import 'package:dio/dio.dart';

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
    if (displayName.trim().isEmpty || quantity <= 0) {
      throw ArgumentError('Item must have a non-empty name and positive quantity');
    }
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
    } on DioException catch (e) {
      if (!_isConnectivityError(e)) rethrow;
      final now = DateTime.now();
      final idempotencyKey = 'create_item_${now.microsecondsSinceEpoch}';
      final localItem = InventoryItem(
        id: 'offline_${now.microsecondsSinceEpoch}',
        displayName: displayName,
        quantity: quantity,
        unit: unit,
        storageLocation: storageLocation,
        estimatedExpiryDate:
            estimatedExpiryDate ?? now.add(const Duration(days: 7)),
        confidence: confidence ?? 0.5,
        status: 'active',
        source: source ?? 'manual',
        canonicalName: canonicalName,
        canonicalIngredientId: canonicalIngredientId,
      );
      await _inventoryDao.insertItem(_toCompanion(localItem));
      await _syncManager.queueCreate(localItem, idempotencyKey: idempotencyKey);
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
    final remaining = await _syncManager.pendingMutations();
    final remoteItems = await _apiClient.getInventoryItems();
    if (remaining.isEmpty) {
      await _replaceCache(remoteItems);
      return remoteItems;
    }
    // Merge: keep local offline items alongside server items
    // Snapshot offline items before replacing cache
    final allLocal = await _inventoryDao.getAllItems();
    final offlineSnapshot = <String, InventoryItemsTableData>{};
    for (final m in remaining.where((m) => m.action == 'create')) {
      final local = allLocal.where((i) => i.id == m.entityId).firstOrNull;
      if (local != null) {
        offlineSnapshot[m.entityId] = local;
      }
    }
    await _replaceCache(remoteItems);
    // Re-insert offline-created items with full field fidelity
    for (final m in remaining.where((m) => m.action == 'create')) {
      final snapshot = offlineSnapshot[m.entityId];
      if (snapshot != null) {
        await _inventoryDao.insertItem(InventoryItemsTableCompanion.insert(
          id: snapshot.id,
          displayName: snapshot.displayName,
          quantity: snapshot.quantity,
          unit: snapshot.unit,
          storageLocation: snapshot.storageLocation,
          estimatedExpiryDate: snapshot.estimatedExpiryDate,
          confidence: snapshot.confidence,
          status: Value(snapshot.status),
          source: Value(snapshot.source),
          canonicalName: Value(snapshot.canonicalName),
          canonicalIngredientId: Value(snapshot.canonicalIngredientId),
          version: Value(snapshot.version),
        ));
      } else {
        // Fallback: reconstruct from payload
        final p = m.payload;
        final item = InventoryItem(
          id: m.entityId,
          displayName: (p['displayName'] ?? '').toString(),
          quantity: double.tryParse(p['quantity']?.toString() ?? '') ?? 0,
          unit: (p['unit'] ?? '').toString(),
          storageLocation: (p['storageLocation'] ?? '').toString(),
          estimatedExpiryDate: p['estimatedExpiryDate'] != null
              ? DateTime.tryParse(p['estimatedExpiryDate'].toString())
              : null,
          confidence: p['confidence'] != null
              ? double.tryParse(p['confidence'].toString())
              : null,
          status: (p['status'] ?? 'active').toString(),
          source: (p['source'] ?? 'manual').toString(),
          canonicalName: p['canonicalName']?.toString(),
          canonicalIngredientId: p['canonicalIngredientId']?.toString(),
        );
        await _inventoryDao.insertItem(_toCompanion(item));
      }
    }
    return _loadCachedItems();
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
    try {
      final updated = await _apiClient.updateItem(
        id: id,
        displayName: displayName,
        quantity: quantity,
        unit: unit,
        storageLocation: storageLocation,
        estimatedExpiryDate: estimatedExpiryDate,
        version: version,
      );
      await _cacheItems([updated]);
      return updated;
    } on DioException catch (e) {
      if (e.response?.statusCode == 409) {
        throw StateError('Item was modified by another user. Please refresh and try again.');
      }
      if (!_isConnectivityError(e)) rethrow;

      final items = await _inventoryDao.getAllItems();
      final existing = items.where((item) => item.id == id).firstOrNull;
      if (existing == null) {
        rethrow;
      }

      final updatedLocal = InventoryItem(
        id: id,
        displayName: displayName ?? existing.displayName,
        quantity: quantity ?? existing.quantity,
        unit: unit ?? existing.unit,
        storageLocation: storageLocation ?? existing.storageLocation,
        estimatedExpiryDate: estimatedExpiryDate ?? existing.estimatedExpiryDate,
        confidence: existing.confidence,
        status: existing.status,
        source: existing.source,
        canonicalName: existing.canonicalName,
        canonicalIngredientId: existing.canonicalIngredientId,
        version: version ?? existing.version,
      );
      await _inventoryDao.insertItem(_toCompanion(updatedLocal));
      await _syncManager.queueUpdate(
        itemId: id,
        displayName: displayName,
        quantity: quantity,
        unit: unit,
        storageLocation: storageLocation,
        estimatedExpiryDate: estimatedExpiryDate,
        version: version,
      );
      return updatedLocal;
    }
  }

  @override
  Future<InventoryItem> updateItemStatus(String id, String status, {int? version}) async {
    final allItems = await _inventoryDao.getAllItems();
    final previousStatus = allItems
        .where((item) => item.id == id)
        .map((item) => item.status)
        .firstOrNull ?? 'active';

    await _inventoryDao.updateItemStatus(id, status);
    try {
      final updated = await _apiClient.updateItemStatus(id, status, version: version);
      await _cacheItems([updated]);
      return updated;
    } on DioException catch (e) {
      if (e.response?.statusCode == 409) {
        await _inventoryDao.updateItemStatus(id, previousStatus);
        throw StateError('Item was modified by another user. Please refresh and try again.');
      }
      if (!_isConnectivityError(e)) {
        await _inventoryDao.updateItemStatus(id, previousStatus);
        rethrow;
      }
      await _syncManager.queueStatusUpdate(itemId: id, status: status, version: version);
      return _localItemFallback(id, status);
    }
  }

  Future<InventoryItem> _localItemFallback(String id, String status) async {
    final items = await _inventoryDao.getAllItems();
    final local = items.where((item) => item.id == id).firstOrNull;
    if (local != null) {
      return InventoryItem(
        id: local.id,
        displayName: local.displayName,
        quantity: local.quantity,
        unit: local.unit,
        storageLocation: local.storageLocation,
        estimatedExpiryDate: local.estimatedExpiryDate,
        confidence: local.confidence,
        status: local.status,
        source: local.source,
        canonicalName: local.canonicalName,
        canonicalIngredientId: local.canonicalIngredientId,
        version: local.version,
      );
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
            canonicalName: item.canonicalName,
            canonicalIngredientId: item.canonicalIngredientId,
            version: item.version,
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

  static bool _isConnectivityError(DioException e) {
    if (e.response == null) return true;
    final status = e.response?.statusCode ?? 0;
    if (status >= 500) return true;
    return e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.sendTimeout ||
        e.type == DioExceptionType.receiveTimeout ||
        e.type == DioExceptionType.connectionError;
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
      canonicalName: Value(item.canonicalName),
      canonicalIngredientId: Value(item.canonicalIngredientId),
      version: Value(item.version),
    );
  }
}
