import 'dart:io';

import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import 'package:fridgefriend_mobile/database/daos/inventory_dao.dart';

part 'app_database.g.dart';

class InventoryItemsTable extends Table {
  TextColumn get id => text()();

  TextColumn get displayName => text()();

  RealColumn get quantity => real()();

  TextColumn get unit => text()();

  TextColumn get storageLocation => text()();

  DateTimeColumn get estimatedExpiryDate => dateTime()();

  RealColumn get confidence => real()();

  TextColumn get status => text().withDefault(const Constant('active'))();

  TextColumn get source => text().withDefault(const Constant('manual'))();

  @override
  Set<Column<Object>> get primaryKey => {id};
}

@DriftDatabase(tables: [InventoryItemsTable], daos: [InventoryDao])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());

  AppDatabase.forTesting(QueryExecutor executor) : super(executor);

  @override
  int get schemaVersion => 1;
}

LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    final documentsDirectory = await getApplicationDocumentsDirectory();
    final file = File(
      p.join(documentsDirectory.path, 'fridgefriend_inventory.sqlite'),
    );

    return NativeDatabase.createInBackground(file);
  });
}
