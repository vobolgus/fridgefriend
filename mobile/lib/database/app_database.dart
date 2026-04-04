import 'dart:io';

import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:flutter/widgets.dart' as widgets;
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import 'package:fridgefriend_mobile/database/daos/inventory_dao.dart';
import 'package:fridgefriend_mobile/database/daos/meal_plan_dao.dart';
import 'package:fridgefriend_mobile/database/daos/recipe_dao.dart';

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

class RecipesTable extends Table {
  TextColumn get id => text()();

  TextColumn get title => text()();

  RealColumn get coveragePct => real().withDefault(const Constant(0))();

  RealColumn get score => real().withDefault(const Constant(0))();

  IntColumn get prepMinutes => integer().withDefault(const Constant(0))();

  TextColumn get missingItemsJson => text().withDefault(const Constant('[]'))();

  DateTimeColumn get syncedAt =>
      dateTime().withDefault(currentDateAndTime)();

  @override
  Set<Column<Object>> get primaryKey => {id};
}

class MealPlansTable extends Table {
  TextColumn get id => text()();

  TextColumn get daysJson => text().withDefault(const Constant('[]'))();

  TextColumn get shoppingListJson => text().withDefault(const Constant('[]'))();

  DateTimeColumn get syncedAt =>
      dateTime().withDefault(currentDateAndTime)();

  @override
  Set<Column<Object>> get primaryKey => {id};
}

@DriftDatabase(tables: [InventoryItemsTable], daos: [InventoryDao])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());

  AppDatabase.forTesting(QueryExecutor executor) : super(executor);

  late final RecipeDao recipeDao = RecipeDao(this);
  late final MealPlanDao mealPlanDao = MealPlanDao(this);

  @override
  int get schemaVersion => 2;

  @override
  MigrationStrategy get migration => MigrationStrategy(
    onCreate: (Migrator migrator) async {
      await migrator.createAll();
      await _ensureAuxiliaryTables();
    },
    onUpgrade: (Migrator migrator, int from, int to) async {
      if (from < 2) {
        await _ensureAuxiliaryTables();
      }
    },
    beforeOpen: (details) async {
      await _ensureAuxiliaryTables();
    },
  );

  Future<void> _ensureAuxiliaryTables() async {
    await customStatement('''
      CREATE TABLE IF NOT EXISTS recipes_cache (
        id TEXT PRIMARY KEY NOT NULL,
        title TEXT NOT NULL,
        coverage_pct REAL NOT NULL DEFAULT 0,
        score REAL NOT NULL DEFAULT 0,
        prep_minutes INTEGER NOT NULL DEFAULT 0,
        missing_items_json TEXT NOT NULL DEFAULT '[]',
        substitutions_json TEXT NOT NULL DEFAULT '[]',
        synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
      )
    ''');

    try {
      await customStatement(
        "ALTER TABLE recipes_cache ADD COLUMN substitutions_json TEXT NOT NULL DEFAULT '[]'",
      );
    } catch (_) {
      // Column already exists.
    }

    await customStatement('''
      CREATE TABLE IF NOT EXISTS meal_plans_cache (
        id TEXT PRIMARY KEY NOT NULL,
        days_json TEXT NOT NULL DEFAULT '[]',
        shopping_list_json TEXT NOT NULL DEFAULT '[]',
        synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
      )
    ''');

    await customStatement('''
      CREATE TABLE IF NOT EXISTS offline_mutation_queue (
        id TEXT PRIMARY KEY NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        action TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
      )
    ''');
  }
}

LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    if (_isTestEnvironment()) {
      return NativeDatabase.memory();
    }

    final documentsDirectory = await getApplicationDocumentsDirectory();
    final file = File(
      p.join(documentsDirectory.path, 'fridgefriend_inventory.sqlite'),
    );

    return NativeDatabase.createInBackground(file);
  });
}

bool _isTestEnvironment() {
  final binding = widgets.WidgetsBinding.instance;
  if (binding == null) {
    return false;
  }

  final bindingType = binding.runtimeType.toString();
  return bindingType.contains('TestWidgetsFlutterBinding') ||
      bindingType.contains('AutomatedTestWidgetsFlutterBinding') ||
      bindingType.contains('LiveTestWidgetsFlutterBinding');
}
