import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';
import 'package:fridgefriend_mobile/features/recommendations/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/recommendations/presentation/recipe_detail_screen.dart';

void main() {
  testWidgets('RecipeDetailScreen shows recipe details',
      (WidgetTester tester) async {
    const recipe = Recipe(
      id: '1',
      title: 'Pasta Bake',
      coveragePct: 0.8,
      score: 0.9,
      prepMinutes: 30,
      missingItems: ['Cheese'],
      substitutions: [],
      instructions: [
        {'number': 1, 'step': 'Boil pasta'},
      ],
      nutrition: {
        'calories': 500,
        'protein': 20,
        'fat': 15,
        'carbs': 70,
      },
      cuisines: ['Italian'],
      dietaryTags: ['Vegetarian'],
      servings: 4,
      summary: 'A delicious pasta bake',
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          savedRecipeProvider('1').overrideWith((ref) => Future.value(false)),
          recipeDetailProvider('1').overrideWith((ref) => Future.value(recipe)),
        ],
        child: const MaterialApp(
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
}
