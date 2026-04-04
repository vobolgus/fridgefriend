import 'dart:convert';

import 'package:drift/drift.dart';

import 'package:fridgefriend_mobile/core/network/api_client.dart';
import 'package:fridgefriend_mobile/database/app_database.dart';
import 'package:fridgefriend_mobile/database/daos/inventory_dao.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';

class QueuedMutation {
  const QueuedMutation({
    required this.id,
    required this.entityType,
    required this.entityId,
    required this.action,
    required this.payload,
    required this.createdAt,
  });

  final String id;
  final String entityType;
  final String entityId;
  final String action;
  final Map<String, dynamic> payload;
  final DateTime createdAt;
}

class SyncManager {
  SyncManager({
    required AppDatabase database,
    required ApiClient apiClient,
    required InventoryDao inventoryDao,
  }) : _database = database,
       _apiClient = apiClient,
       _inventoryDao = inventoryDao;

  final AppDatabase _database;
  final ApiClient _apiClient;
  final InventoryDao _inventoryDao;

  Future<void> queueCreate(InventoryItem item) {
    return _enqueue(
      entityType: 'inventory',
      entityId: item.id,
      action: 'create',
      payload: item.toJson(),
    );
  }

  Future<void> queueStatusUpdate({
    required String itemId,
    required String status,
    int? version,
  }) {
    return _enqueue(
      entityType: 'inventory',
      entityId: itemId,
      action: 'status_update',
      payload: {'id': itemId, 'status': status, if (version != null) 'version': version},
    );
  }

  Future<void> queueUpdate({
    required String itemId,
    String? displayName,
    double? quantity,
    String? unit,
    String? storageLocation,
    DateTime? estimatedExpiryDate,
    int? version,
  }) {
    return _enqueue(
      entityType: 'inventory',
      entityId: itemId,
      action: 'update',
      payload: {
        'id': itemId,
        if (displayName != null) 'displayName': displayName,
        if (quantity != null) 'quantity': quantity,
        if (unit != null) 'unit': unit,
        if (storageLocation != null) 'storageLocation': storageLocation,
        if (estimatedExpiryDate != null)
          'estimatedExpiryDate': estimatedExpiryDate.toIso8601String(),
        if (version != null) 'version': version,
      },
    );
  }

  Future<List<QueuedMutation>> pendingMutations() async {
    final rows = await _database.customSelect(
      'SELECT id, entity_type, entity_id, action, payload_json, created_at '
      'FROM offline_mutation_queue ORDER BY created_at ASC',
    ).get();

    return rows.map(_mapRow).toList(growable: false);
  }

  Future<void> flushPendingMutations() async {
    while (true) {
      final mutations = await pendingMutations();
      if (mutations.isEmpty) {
        return;
      }
      final mutation = mutations.first;

      if (mutation.entityType != 'inventory') {
        await _deleteMutation(mutation.id);
        continue;
      }

      if (mutation.action == 'create') {
        final syncedItem = await _apiClient.createInventoryItem(
          displayName: (mutation.payload['displayName'] ?? '').toString(),
          quantity: _toDouble(mutation.payload['quantity']),
          unit: (mutation.payload['unit'] ?? '').toString(),
          storageLocation: (mutation.payload['storageLocation'] ?? '').toString(),
          source: mutation.payload['source']?.toString(),
          canonicalName: mutation.payload['canonicalName']?.toString(),
          canonicalIngredientId:
              mutation.payload['canonicalIngredientId']?.toString(),
          confidence: mutation.payload['confidence'] == null
              ? null
              : _toDouble(mutation.payload['confidence']),
          estimatedExpiryDate: mutation.payload['estimatedExpiryDate'] == null
              ? null
              : DateTime.tryParse(
                  mutation.payload['estimatedExpiryDate'].toString(),
                ),
        );
        await _retargetPendingMutations(
          fromEntityId: mutation.entityId,
          toEntityId: syncedItem.id,
          version: syncedItem.version,
        );

        await _inventoryDao.deleteItem(mutation.entityId);
        await _inventoryDao.insertItem(_toCompanion(syncedItem));
        await _deleteMutation(mutation.id);
        continue;
      }

      if (mutation.action == 'status_update') {
        final statusVersion = mutation.payload['version'] is int
            ? mutation.payload['version'] as int
            : int.tryParse(mutation.payload['version']?.toString() ?? '');
        final syncedStatus = await _apiClient.updateItemStatus(
          mutation.entityId,
          (mutation.payload['status'] ?? '').toString(),
          version: statusVersion,
        );
        await _rebasePendingMutations(
          entityId: mutation.entityId,
          version: syncedStatus.version,
        );
        await _inventoryDao.insertItem(_toCompanion(syncedStatus));
        await _deleteMutation(mutation.id);
        continue;
      }

      if (mutation.action == 'update') {
        final syncedUpdate = await _apiClient.updateItem(
          id: mutation.entityId,
          displayName: mutation.payload['displayName']?.toString(),
          quantity: mutation.payload['quantity'] != null
              ? _toDouble(mutation.payload['quantity'])
              : null,
          unit: mutation.payload['unit']?.toString(),
          storageLocation: mutation.payload['storageLocation']?.toString(),
          estimatedExpiryDate: mutation.payload['estimatedExpiryDate'] != null
              ? DateTime.tryParse(
                  mutation.payload['estimatedExpiryDate'].toString(),
                )
              : null,
          version: mutation.payload['version'] is int
              ? mutation.payload['version'] as int
              : int.tryParse(mutation.payload['version']?.toString() ?? ''),
        );
        await _rebasePendingMutations(
          entityId: mutation.entityId,
          version: syncedUpdate.version,
        );
        await _inventoryDao.insertItem(_toCompanion(syncedUpdate));
        await _deleteMutation(mutation.id);
        continue;
      }

      await _deleteMutation(mutation.id);
    }
  }

  Future<void> _retargetPendingMutations({
    required String fromEntityId,
    required String toEntityId,
    required int version,
  }) async {
    final queued = await pendingMutations();
    for (final m in queued.where(
      (m) => m.entityType == 'inventory' && m.entityId == fromEntityId,
    )) {
      final payload = Map<String, dynamic>.from(m.payload);
      payload['id'] = toEntityId;
      if (m.action != 'create') {
        payload['version'] = version;
      }
      await _database.customStatement(
        'UPDATE offline_mutation_queue SET entity_id = ?, payload_json = ? WHERE id = ?',
        <Object?>[toEntityId, jsonEncode(payload), m.id],
      );
    }
  }

  Future<void> _rebasePendingMutations({
    required String entityId,
    required int version,
  }) async {
    final queued = await pendingMutations();
    for (final m in queued.where(
      (m) =>
          m.entityType == 'inventory' &&
          m.entityId == entityId &&
          m.action != 'create',
    )) {
      final payload = Map<String, dynamic>.from(m.payload);
      payload['version'] = version;
      await _database.customStatement(
        'UPDATE offline_mutation_queue SET payload_json = ? WHERE id = ?',
        <Object?>[jsonEncode(payload), m.id],
      );
    }
  }

  Future<void> clearPendingMutations() {
    return _database.customStatement('DELETE FROM offline_mutation_queue');
  }

  Future<void> _enqueue({
    required String entityType,
    required String entityId,
    required String action,
    required Map<String, dynamic> payload,
  }) {
    final now = DateTime.now();
    final id = '${entityType}_${action}_${now.microsecondsSinceEpoch}';
    return _database.customStatement(
      'INSERT OR REPLACE INTO offline_mutation_queue '
      '(id, entity_type, entity_id, action, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)',
      <Object?>[
        id,
        entityType,
        entityId,
        action,
        jsonEncode(payload),
        now.toIso8601String(),
      ],
    );
  }

  Future<void> _deleteMutation(String id) {
    return _database.customStatement(
      'DELETE FROM offline_mutation_queue WHERE id = ?',
      <Object?>[id],
    );
  }

  QueuedMutation _mapRow(QueryRow row) {
    return QueuedMutation(
      id: row.read<String>('id'),
      entityType: row.read<String>('entity_type'),
      entityId: row.read<String>('entity_id'),
      action: row.read<String>('action'),
      payload: Map<String, dynamic>.from(
        jsonDecode(row.read<String>('payload_json')) as Map,
      ),
      createdAt:
          DateTime.tryParse(row.read<String>('created_at')) ??
          DateTime.fromMillisecondsSinceEpoch(0),
    );
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

  double _toDouble(Object? value) {
    if (value is num) {
      return value.toDouble();
    }

    return double.tryParse(value?.toString() ?? '') ?? 0;
  }
}
