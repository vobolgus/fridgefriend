import 'package:dio/dio.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fridgefriend_mobile/core/network/api_client.dart';
import 'package:fridgefriend_mobile/database/app_database.dart';
import 'package:fridgefriend_mobile/database/sync_manager.dart';
import 'package:fridgefriend_mobile/features/inventory/data/inventory_repository_impl.dart';

void main() {
  late AppDatabase database;
  late ApiClient apiClient;
  late SyncManager syncManager;
  late InventoryRepositoryImpl repository;

  setUp(() {
    database = AppDatabase.forTesting(NativeDatabase.memory());
    apiClient = ApiClient(baseUrl: 'https://example.test');
    syncManager = SyncManager(
      database: database,
      apiClient: apiClient,
      inventoryDao: database.inventoryDao,
    );
    repository = InventoryRepositoryImpl(
      apiClient,
      inventoryDao: database.inventoryDao,
      syncManager: syncManager,
    );
  });

  tearDown(() async {
    await database.close();
  });

  test('returns cached items first then syncs from api', () async {
    await database.inventoryDao.insertItem(
      InventoryItemsTableCompanion.insert(
        id: 'cached-item',
        displayName: 'Cached Milk',
        quantity: 1,
        unit: 'L',
        storageLocation: 'fridge',
        estimatedExpiryDate: DateTime(2026, 4, 10),
        confidence: 0.9,
      ),
    );

    apiClient.rawClient.httpClientAdapter = _FakeAdapter((options, _, __) async {
      if (options.path.endsWith('/items') && options.method == 'GET') {
        return ResponseBody.fromString(
          '[{"id":"remote-item","displayName":"Remote Milk","quantity":2,"unit":"L","storageLocation":"fridge","estimatedExpiryDate":"2026-04-12T00:00:00.000","confidence":0.95,"status":"active","source":"manual"}]',
          200,
          headers: {Headers.contentTypeHeader: ['application/json']},
        );
      }

      return ResponseBody.fromString('[]', 200);
    });

    final cachedItems = await repository.getInventoryItems();
    expect(cachedItems.single.displayName, 'Cached Milk');

    final syncedItems = await repository.syncInventoryItems();
    expect(syncedItems.single.displayName, 'Remote Milk');

    final storedItems = await database.inventoryDao.getAllItems();
    expect(storedItems.single.displayName, 'Remote Milk');
  });

  test('queues offline create and flushes later', () async {
    apiClient.rawClient.httpClientAdapter = _FakeAdapter((options, requestStream, __) async {
      if (options.path.endsWith('/items') && options.method == 'POST') {
        return ResponseBody.fromString('network error', 500);
      }
      return ResponseBody.fromString('[]', 200);
    });

    final offlineItem = await repository.createInventoryItem(
      displayName: 'Eggs',
      quantity: 12,
      unit: 'pcs',
      storageLocation: 'fridge',
    );

    expect(offlineItem.id, startsWith('offline_'));
    final queued = await syncManager.pendingMutations();
    expect(queued, hasLength(1));

    apiClient.rawClient.httpClientAdapter = _FakeAdapter((options, _, __) async {
      if (options.path.endsWith('/items') && options.method == 'POST') {
        return ResponseBody.fromString(
          '{"id":"server-item","displayName":"Eggs","quantity":12,"unit":"pcs","storageLocation":"fridge","estimatedExpiryDate":"2026-04-12T00:00:00.000","confidence":0.8,"status":"active","source":"manual"}',
          200,
          headers: {Headers.contentTypeHeader: ['application/json']},
        );
      }

      return ResponseBody.fromString('[]', 200);
    });

    await syncManager.flushPendingMutations();

    final pending = await syncManager.pendingMutations();
    expect(pending, isEmpty);
    final storedItems = await database.inventoryDao.getAllItems();
    expect(storedItems.single.id, 'server-item');
  });
}

typedef _AdapterHandler = Future<ResponseBody> Function(
  RequestOptions options,
  Stream<List<int>>? requestStream,
  Future<void>? cancelFuture,
);

class _FakeAdapter implements HttpClientAdapter {
  _FakeAdapter(this._handler);

  final _AdapterHandler _handler;

  @override
  void close({bool force = false}) {}

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<List<int>>? requestStream,
    Future<void>? cancelFuture,
  ) {
    return _handler(options, requestStream, cancelFuture);
  }
}
