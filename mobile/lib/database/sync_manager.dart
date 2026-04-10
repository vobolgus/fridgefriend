import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:drift/drift.dart';

import 'package:fridgefriend_mobile/core/network/api_client.dart';
import 'package:fridgefriend_mobile/database/app_database.dart';
import 'package:fridgefriend_mobile/database/conflict_resolver.dart';
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
  })  : _database = database,
        _apiClient = apiClient,
        _inventoryDao = inventoryDao;

  final AppDatabase _database;
  final ApiClient _apiClient;
  final InventoryDao _inventoryDao;
  bool _isFlushing = false;

  Future<void> queueCreate(InventoryItem item, {String? idempotencyKey}) {
    final payload = item.toJson();
    if (idempotencyKey != null) {
      payload['_idempotencyKey'] = idempotencyKey;
    }
    return _enqueue(
      entityType: 'inventory',
      entityId: item.id,
      action: 'create',
      payload: payload,
    );
  }

  Future<void> queueStatusUpdate({
    required InventoryItem baseItem,
    required String status,
    int? version,
  }) {
    final localItem = baseItem.copyWith(status: status, version: version);

    return _enqueue(
      entityType: 'inventory',
      entityId: baseItem.id,
      action: 'status_update',
      payload: {
        ...localItem.toJson(),
        'id': baseItem.id,
        'base': baseItem.toJson(),
        'dirty_fields': const ['status'],
        if (version != null) 'version': version,
      },
    );
  }

  Future<void> queueUpdate({
    required String itemId,
    required InventoryItem oldItem,
    String? displayName,
    double? quantity,
    String? unit,
    String? storageLocation,
    DateTime? estimatedExpiryDate,
    int? version,
  }) {
    final payload = {
      'id': itemId,
      'displayName': displayName ?? oldItem.displayName,
      'quantity': quantity ?? oldItem.quantity,
      'unit': unit ?? oldItem.unit,
      'storageLocation': storageLocation ?? oldItem.storageLocation,
      'estimatedExpiryDate':
          (estimatedExpiryDate ?? oldItem.estimatedExpiryDate)
              ?.toIso8601String(),
      'status': oldItem.status,
      'source': oldItem.source,
      'canonicalName': oldItem.canonicalName,
      'canonicalIngredientId': oldItem.canonicalIngredientId,
      'base': oldItem.toJson(),
      'dirty_fields': _dirtyFields(
        oldItem: oldItem,
        newItem: oldItem.copyWith(
          displayName: displayName,
          quantity: quantity,
          unit: unit,
          storageLocation: storageLocation,
          estimatedExpiryDate: estimatedExpiryDate,
        ),
      ).toList(growable: false),
      if (version != null) 'version': version,
    };

    if (payload['estimatedExpiryDate'] == null) {
      payload.remove('estimatedExpiryDate');
    }

    return _enqueue(
      entityType: 'inventory',
      entityId: itemId,
      action: 'update',
      payload: payload,
    );
  }

  Future<List<QueuedMutation>> pendingMutations() async {
    final rows = await _database
        .customSelect(
          'SELECT id, entity_type, entity_id, action, payload_json, created_at '
          'FROM offline_mutation_queue ORDER BY created_at ASC',
        )
        .get();

    return rows.map(_mapRow).toList(growable: false);
  }

  Future<void> flushPendingMutations() async {
    if (_isFlushing) {
      return;
    }

    _isFlushing = true;
    try {
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

        try {
          if (mutation.action == 'create') {
            final syncedItem = await _apiClient.createInventoryItem(
              displayName: (mutation.payload['displayName'] ?? '').toString(),
              quantity: _toDouble(mutation.payload['quantity']),
              unit: (mutation.payload['unit'] ?? '').toString(),
              storageLocation:
                  (mutation.payload['storageLocation'] ?? '').toString(),
              source: mutation.payload['source']?.toString(),
              canonicalName: mutation.payload['canonicalName']?.toString(),
              canonicalIngredientId:
                  mutation.payload['canonicalIngredientId']?.toString(),
              confidence: mutation.payload['confidence'] == null
                  ? null
                  : _toDouble(mutation.payload['confidence']),
              estimatedExpiryDate:
                  mutation.payload['estimatedExpiryDate'] == null
                      ? null
                      : DateTime.tryParse(
                          mutation.payload['estimatedExpiryDate'].toString(),
                        ),
              idempotencyKey: mutation.payload['_idempotencyKey']?.toString(),
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
            final localStatusItem = _itemFromPayload(mutation.payload);
            final syncedStatus = await _applyWithConflictResolution(
              mutation: mutation,
              submit: (item, version) => _apiClient.updateItemStatus(
                item.id,
                item.status,
                version: version,
              ),
              localItem: localStatusItem,
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
            final localUpdateItem = _itemFromPayload(mutation.payload);
            final syncedUpdate = await _applyWithConflictResolution(
              mutation: mutation,
              submit: (item, version) => _apiClient.updateItem(
                id: item.id,
                displayName: item.displayName,
                quantity: item.quantity,
                unit: item.unit,
                storageLocation: item.storageLocation,
                estimatedExpiryDate: item.estimatedExpiryDate,
                version: version,
              ),
              localItem: localUpdateItem,
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
        } on DioException catch (e) {
          final statusCode = e.response?.statusCode;
          if (statusCode != null &&
              statusCode >= 400 &&
              statusCode < 500 &&
              statusCode != 401) {
            await _deleteMutation(mutation.id);
            continue;
          }
          return;
        } catch (_) {
          return;
        }

        await _deleteMutation(mutation.id);
      }
    } finally {
      _isFlushing = false;
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

  Future<InventoryItem> _applyWithConflictResolution({
    required QueuedMutation mutation,
    required Future<InventoryItem> Function(InventoryItem item, int? version)
        submit,
    required InventoryItem localItem,
    required int? version,
  }) async {
    try {
      return await submit(localItem, version);
    } on DioException catch (error) {
      if (error.response?.statusCode != 409) {
        rethrow;
      }

      final serverItem = await _fetchServerItem(mutation.entityId);
      final resolver =
          ConflictResolver(baseItem: _baseItemFromPayload(mutation.payload));
      final dirtyFields = _dirtyFieldsFromPayload(mutation.payload);
      final mergedItem = resolver.resolve(serverItem, localItem, dirtyFields);

      try {
        return await submit(mergedItem, serverItem.version);
      } on DioException catch (retryError) {
        if (retryError.response?.statusCode == 409) {
          throw _UnresolvedConflictException();
        }
        rethrow;
      }
    }
  }

  Future<InventoryItem> _fetchServerItem(String itemId) async {
    final items = await _apiClient.getInventoryItems();
    return items.firstWhere((item) => item.id == itemId);
  }

  InventoryItem _baseItemFromPayload(Map<String, dynamic> payload) {
    final base = payload['base'];
    if (base is Map<String, dynamic>) {
      return InventoryItem.fromJson(base);
    }
    if (base is Map) {
      return InventoryItem.fromJson(Map<String, dynamic>.from(base));
    }

    return _itemFromPayload(payload);
  }

  Set<String> _dirtyFieldsFromPayload(Map<String, dynamic> payload) {
    final value = payload['dirty_fields'];
    if (value is List) {
      return value.map((entry) => entry.toString()).toSet();
    }

    return const <String>{};
  }

  InventoryItem _itemFromPayload(Map<String, dynamic> payload) {
    return InventoryItem(
      id: (payload['id'] ?? payload['itemId'] ?? '').toString(),
      displayName: (payload['displayName'] ?? '').toString(),
      quantity: _toDouble(payload['quantity']),
      unit: (payload['unit'] ?? '').toString(),
      storageLocation: (payload['storageLocation'] ?? '').toString(),
      estimatedExpiryDate: payload['estimatedExpiryDate'] == null
          ? null
          : DateTime.tryParse(payload['estimatedExpiryDate'].toString()),
      confidence: payload['confidence'] == null
          ? null
          : _toDouble(payload['confidence']),
      status: (payload['status'] ?? 'active').toString(),
      source: (payload['source'] ?? 'manual').toString(),
      canonicalName: payload['canonicalName']?.toString(),
      canonicalIngredientId: payload['canonicalIngredientId']?.toString(),
      version: payload['version'] is int
          ? payload['version'] as int
          : int.tryParse(payload['version']?.toString() ?? '') ?? 1,
    );
  }

  Set<String> _dirtyFields({
    required InventoryItem oldItem,
    required InventoryItem newItem,
  }) {
    final fields = <String>{};

    if (oldItem.displayName != newItem.displayName) {
      fields.add('displayName');
    }
    if (oldItem.quantity != newItem.quantity) {
      fields.add('quantity');
    }
    if (oldItem.unit != newItem.unit) {
      fields.add('unit');
    }
    if (oldItem.storageLocation != newItem.storageLocation) {
      fields.add('storageLocation');
    }
    if (!_dateTimeEquals(
        oldItem.estimatedExpiryDate, newItem.estimatedExpiryDate)) {
      fields.add('estimatedExpiryDate');
    }
    if (oldItem.status != newItem.status) {
      fields.add('status');
    }
    if (oldItem.canonicalName != newItem.canonicalName) {
      fields.add('canonicalName');
    }

    return fields;
  }

  bool _dateTimeEquals(DateTime? left, DateTime? right) {
    if (left == null || right == null) {
      return left == right;
    }

    return left.isAtSameMomentAs(right);
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
      createdAt: DateTime.tryParse(row.read<String>('created_at')) ??
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

class _UnresolvedConflictException implements Exception {}
