import 'dart:convert';

import 'package:drift/drift.dart';

import 'package:fridgefriend_mobile/database/app_database.dart';
import 'package:fridgefriend_mobile/features/meal_planning/domain/meal_plan.dart';

class CachedMealPlanRecord {
  const CachedMealPlanRecord({
    required this.id,
    required this.days,
    required this.shoppingList,
    required this.syncedAt,
  });

  final String id;
  final List<PlanDay> days;
  final List<ShoppingItem> shoppingList;
  final DateTime syncedAt;

  MealPlan toDomain() {
    return MealPlan(planId: id, days: days, shoppingList: shoppingList);
  }
}

class MealPlanDao {
  MealPlanDao(this._db);

  final AppDatabase _db;

  Future<CachedMealPlanRecord?> getLatestMealPlan() async {
    final rows = await _db.customSelect(
      'SELECT id, days_json, shopping_list_json, synced_at '
      'FROM meal_plans_cache ORDER BY synced_at DESC LIMIT 1',
    ).get();

    if (rows.isEmpty) {
      return null;
    }

    return _mapRow(rows.single);
  }

  Future<void> saveMealPlan(MealPlan mealPlan) async {
    await _db.transaction(() async {
      await _db.customStatement('DELETE FROM meal_plans_cache');
      await _db.customStatement(
        'INSERT OR REPLACE INTO meal_plans_cache '
        '(id, days_json, shopping_list_json, synced_at) VALUES (?, ?, ?, ?)',
        <Object?>[
          mealPlan.planId,
          jsonEncode(
            mealPlan.days.map((day) => day.toJson()).toList(growable: false),
          ),
          jsonEncode(
            mealPlan.shoppingList
                .map((item) => item.toJson())
                .toList(growable: false),
          ),
          DateTime.now().toIso8601String(),
        ],
      );
    });
  }

  Future<void> clear() => _db.customStatement('DELETE FROM meal_plans_cache');

  CachedMealPlanRecord _mapRow(QueryRow row) {
    final daysJson = row.read<String>('days_json');
    final shoppingListJson = row.read<String>('shopping_list_json');
    final syncedAtRaw = row.read<String>('synced_at');

    return CachedMealPlanRecord(
      id: row.read<String>('id'),
      days: (jsonDecode(daysJson) as List<dynamic>)
          .whereType<Map<String, dynamic>>()
          .map(PlanDay.fromJson)
          .toList(growable: false),
      shoppingList: (jsonDecode(shoppingListJson) as List<dynamic>)
          .whereType<Map<String, dynamic>>()
          .map(ShoppingItem.fromJson)
          .toList(growable: false),
      syncedAt: DateTime.tryParse(syncedAtRaw) ?? DateTime.fromMillisecondsSinceEpoch(0),
    );
  }
}
