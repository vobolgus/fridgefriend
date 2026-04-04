import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';
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
      substitutions: const [],
    );

    await tester.pumpWidget(
      const MaterialApp(
        home: RecipeDetailScreen(recipe: recipe),
      ),
    );

    expect(find.text('Pasta Bake'), findsWidgets);
    expect(find.text('30 min'), findsOneWidget);
    expect(find.text('Ingredient Coverage'), findsOneWidget);
    expect(find.text('80%'), findsOneWidget);
    expect(find.text('Cheese'), findsOneWidget);
    expect(find.text('Substitutions'), findsOneWidget);
    expect(find.text('No substitutions suggested'), findsOneWidget);
  });
}
