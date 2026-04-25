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
        substitutions: const [],
      ),
    ]);

    final records = await dao.getAllRecipes();

    expect(records, hasLength(1));
    expect(records.single.toDomain().title, 'Omelet');
    expect(records.single.missingItems, ['cheese']);
  });

  test('preserves imageUrl across save and read', () async {
    const recipe = Recipe(
      id: 'recipe-image',
      title: 'Tomato Soup',
      coveragePct: 0.5,
      score: 0.42,
      prepMinutes: 20,
      missingItems: ['basil'],
      substitutions: [],
      imageUrl: 'https://img.spoonacular.com/recipes/716429-556x370.jpg',
      ingredients: [],
    );

    await dao.replaceAllRecipes([recipe]);

    final records = await dao.getAllRecipes();

    expect(records, hasLength(1));
    expect(
      records.single.toDomain().imageUrl,
      equals(recipe.imageUrl),
      reason: 'imageUrl must survive cache round-trip.',
    );
  });

  test('preserves ingredients across save and read', () async {
    const recipe = Recipe(
      id: 'recipe-ingredients',
      title: 'Scrambled Eggs',
      coveragePct: 0,
      score: 0.1,
      prepMinutes: 10,
      missingItems: ['eggs', 'butter'],
      substitutions: [],
      ingredients: [
        {'canonical_name': 'eggs', 'quantity': 2.0, 'unit': 'unit'},
        {'canonical_name': 'butter', 'quantity': 1.0, 'unit': 'tbsp'},
      ],
    );

    await dao.replaceAllRecipes([recipe]);

    final records = await dao.getAllRecipes();
    final loadedRecipe = records.single.toDomain();

    expect(records, hasLength(1));
    expect(
      loadedRecipe.ingredients,
      hasLength(2),
      reason: 'ingredients must survive cache round-trip.',
    );
    expect(loadedRecipe.ingredients[0]['canonical_name'], equals('eggs'));
    expect(loadedRecipe.ingredients[1]['canonical_name'], equals('butter'));
  });
}
