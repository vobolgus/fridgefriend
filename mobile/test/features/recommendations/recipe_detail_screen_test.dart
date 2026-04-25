import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';
import 'package:fridgefriend_mobile/features/recommendations/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/recommendations/presentation/recipe_detail_screen.dart';

void main() {
  Recipe buildRecipe({List<String> missingItems = const ['Cheese']}) {
    return Recipe(
      id: '1',
      title: 'Pasta Bake',
      coveragePct: 0.8,
      score: 0.9,
      prepMinutes: 30,
      missingItems: missingItems,
      substitutions: const [],
      instructions: const [
        {'number': 1, 'step': 'Boil pasta'},
      ],
      nutrition: const {
        'calories': 500,
        'protein': 20,
        'fat': 15,
        'carbs': 70,
      },
      cuisines: const ['Italian'],
      dietaryTags: const ['Vegetarian'],
      servings: 4,
      summary: 'A delicious pasta bake',
      ingredients: const [
        {'name': 'pasta', 'amount': 200, 'unit': 'g'},
      ],
    );
  }

  testWidgets('RecipeDetailScreen shows recipe details',
      (WidgetTester tester) async {
    final recipe = buildRecipe();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          savedRecipeProvider('1').overrideWith((ref) => Future.value(false)),
          recipeDetailProvider('1').overrideWith((ref) => Future.value(recipe)),
        ],
        child: MaterialApp(
          home: RecipeDetailScreen(recipe: recipe),
        ),
      ),
    );

    expect(find.text('Pasta Bake'), findsWidgets);
    expect(find.text('30 min'), findsOneWidget);
    expect(find.text('Ingredient Coverage'), findsOneWidget);
    expect(find.text('80%'), findsOneWidget);
    expect(find.text('Cheese'), findsOneWidget);
    expect(find.text('Substitutions'), findsOneWidget);
    expect(find.text('No substitutions suggested'), findsOneWidget);

    // New fields
    expect(find.text('Instructions'), findsOneWidget);
    expect(find.text('Boil pasta'), findsOneWidget);
    expect(find.text('Nutrition'), findsOneWidget);
    expect(find.text('500'), findsOneWidget);
    expect(find.text('20g'), findsOneWidget);
    expect(find.text('Italian'), findsOneWidget);
    expect(find.text('Vegetarian'), findsOneWidget);
    expect(find.text('4 servings'), findsOneWidget);
    expect(find.text('A delicious pasta bake'), findsOneWidget);
  });

  testWidgets(
      'add_missing_to_shopping_list_button_visible_when_missing_items_nonempty',
      (WidgetTester tester) async {
    final recipe = buildRecipe(missingItems: const ['eggs', 'butter']);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          savedRecipeProvider('1').overrideWith((ref) => Future.value(false)),
          recipeDetailProvider('1').overrideWith((ref) => Future.value(recipe)),
        ],
        child: MaterialApp(
          home: RecipeDetailScreen(recipe: recipe),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(
      find.textContaining(
        RegExp('shopping list', caseSensitive: false),
        findRichText: true,
      ),
      findsOneWidget,
    );
  });

  testWidgets('add_missing_to_shopping_list_button_hidden_when_no_missing_items',
      (WidgetTester tester) async {
    final recipe = buildRecipe(missingItems: const []);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          savedRecipeProvider('1').overrideWith((ref) => Future.value(false)),
          recipeDetailProvider('1').overrideWith((ref) => Future.value(recipe)),
        ],
        child: MaterialApp(
          home: RecipeDetailScreen(recipe: recipe),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(
      find.textContaining(
        RegExp('shopping list', caseSensitive: false),
        findRichText: true,
      ),
      findsNothing,
    );
  });
}
