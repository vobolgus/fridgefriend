import 'package:drift/drift.dart';

import 'package:fridgefriend_mobile/database/app_database.dart';

part 'inventory_dao.g.dart';

@DriftAccessor(tables: [InventoryItemsTable])
class InventoryDao extends DatabaseAccessor<AppDatabase>
    with _$InventoryDaoMixin {
  InventoryDao(super.db);

  Future<List<InventoryItemsTableData>> getAllItems() {
    return (select(inventoryItemsTable)
          ..where(
            (table) => table.status.isNotIn(const ['used', 'discarded']),
          ))
        .get();
  }

  Future<void> insertItem(InventoryItemsTableCompanion item) async {
    await into(inventoryItemsTable).insert(item);
  }

  Future<void> updateItemStatus(String id, String status) async {
    await (update(inventoryItemsTable)..where((table) => table.id.equals(id)))
        .write(InventoryItemsTableCompanion(status: Value(status)));
  }

  Future<void> deleteItem(String id) async {
    await (delete(inventoryItemsTable)..where((table) => table.id.equals(id)))
        .go();
  }

  Future<void> clearAll() async {
    await delete(inventoryItemsTable).go();
  }
}
