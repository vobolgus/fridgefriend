import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fridgefriend_mobile/database/app_database.dart';
import 'package:fridgefriend_mobile/database/daos/recipe_dao.dart';
import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';

void main() {
  late AppDatabase database;
  late RecipeDao dao;

  setUp(() {
    database = AppDatabase.forTesting(NativeDatabase.memory());
    dao = RecipeDao(database);
  });

  tearDown(() async {
    await database.close();
  });

  test('stores and loads cached recipes', () async {
    await dao.replaceAllRecipes([
      const Recipe(
        id: 'recipe-1',
        title: 'Omelet',
        coveragePct: 0.75,
        score: 8.4,
        prepMinutes: 10,
        missingItems: ['cheese'],
      ),
    ]);

    final records = await dao.getAllRecipes();

    expect(records, hasLength(1));
    expect(records.single.toDomain().title, 'Omelet');
    expect(records.single.missingItems, ['cheese']);
  });
}
