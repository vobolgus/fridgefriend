import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fridgefriend_mobile/database/app_database.dart';
import 'package:fridgefriend_mobile/database/daos/inventory_dao.dart';

void main() {
  late AppDatabase db;
  late InventoryDao dao;

  InventoryItemsTableCompanion buildItem({
    required String id,
    required String displayName,
    String status = 'active',
  }) {
    return InventoryItemsTableCompanion.insert(
      id: id,
      displayName: displayName,
      quantity: 1,
      unit: 'pcs',
      storageLocation: 'fridge',
      estimatedExpiryDate: DateTime(2026, 4, 10),
      confidence: 0.9,
      status: Value(status),
      source: const Value('manual'),
    );
  }

  setUp(() {
    db = AppDatabase.forTesting(NativeDatabase.memory());
    dao = InventoryDao(db);
  });

  tearDown(() async {
    await db.close();
  });

  test('insert and read inventory item', () async {
    await dao.insertItem(buildItem(id: 'item-1', displayName: 'Milk'));

    final items = await dao.getAllItems();

    expect(items, hasLength(1));
    expect(items.single.id, 'item-1');
    expect(items.single.displayName, 'Milk');
    expect(items.single.quantity, 1);
    expect(items.single.unit, 'pcs');
    expect(items.single.storageLocation, 'fridge');
    expect(items.single.status, 'active');
    expect(items.single.source, 'manual');
  });

  test('update item status', () async {
    await dao.insertItem(buildItem(id: 'item-2', displayName: 'Yogurt'));

    await dao.updateItemStatus('item-2', 'used');

    final updatedItem = await (db.select(db.inventoryItemsTable)
          ..where((table) => table.id.equals('item-2')))
        .getSingle();

    expect(updatedItem.status, 'used');
  });

  test('delete item', () async {
    await dao.insertItem(buildItem(id: 'item-3', displayName: 'Spinach'));

    await dao.deleteItem('item-3');

    final rows = await db.select(db.inventoryItemsTable).get();

    expect(rows, isEmpty);
  });

  test('active items filter excludes used/discarded', () async {
    await dao.insertItem(buildItem(id: 'active-item', displayName: 'Eggs'));
    await dao.insertItem(
      buildItem(id: 'used-item', displayName: 'Cheese', status: 'used'),
    );
    await dao.insertItem(
      buildItem(
        id: 'discarded-item',
        displayName: 'Lettuce',
        status: 'discarded',
      ),
    );

    final items = await dao.getAllItems();

    expect(items.map((item) => item.id), ['active-item']);
  });
}
