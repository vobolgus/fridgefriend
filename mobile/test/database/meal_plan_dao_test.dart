import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fridgefriend_mobile/database/app_database.dart';
import 'package:fridgefriend_mobile/database/daos/meal_plan_dao.dart';
import 'package:fridgefriend_mobile/features/meal_planning/domain/meal_plan.dart';

void main() {
  late AppDatabase database;
  late MealPlanDao dao;

  setUp(() {
    database = AppDatabase.forTesting(NativeDatabase.memory());
    dao = MealPlanDao(database);
  });

  tearDown(() async {
    await database.close();
  });

  test('stores latest meal plan payload', () async {
    await dao.saveMealPlan(
      MealPlan(
        planId: 'plan-1',
        days: [
          PlanDay(
            date: DateTime(2026, 4, 4),
            recipeId: 'recipe-1',
            recipeTitle: 'Pasta Night',
            prepMinutes: 25,
            imageUrl: 'https://example.test/pasta.jpg',
          ),
        ],
        shoppingList: const [
          ShoppingItem(
            ingredientName: 'tomatoes',
            quantity: 2,
            unit: 'count',
          ),
        ],
      ),
    );

    final record = await dao.getLatestMealPlan();

    expect(record, isNotNull);
    expect(record!.toDomain().planId, 'plan-1');
    expect(record.days.single.recipeTitle, 'Pasta Night');
    expect(record.days.single.prepMinutes, 25);
    expect(record.days.single.imageUrl, 'https://example.test/pasta.jpg');
    expect(record.shoppingList.single.ingredientName, 'tomatoes');
  });
}
