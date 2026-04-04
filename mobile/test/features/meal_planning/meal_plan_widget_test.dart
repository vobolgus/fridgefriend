import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:fridgefriend_mobile/core/network/api_client.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/meal_planning/domain/meal_plan.dart';
import 'package:fridgefriend_mobile/features/meal_planning/presentation/meal_plan_screen.dart';
import 'package:fridgefriend_mobile/features/meal_planning/presentation/shopping_list_screen.dart';

class MockApiClient extends Mock implements ApiClient {}

void main() {
  testWidgets('MealPlanScreen shows day picker and generates plan', (tester) async {
    final mockClient = MockApiClient();
    when(() => mockClient.generatePlan(days: any(named: 'days'))).thenAnswer(
      (_) async => MealPlan(
        planId: 'plan-1',
        days: [
          PlanDay(
            date: DateTime(2026, 4, 3),
            recipeId: 'recipe-1',
            recipeTitle: 'Veggie Stir Fry',
          ),
        ],
        shoppingList: const [],
      ),
    );
    when(() => mockClient.getShoppingList()).thenAnswer(
      (_) async => const [
        ShoppingItem(
          ingredientName: 'Tofu',
          quantity: 1,
          unit: 'block',
        ),
      ],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(mockClient)],
        child: const MaterialApp(home: MealPlanScreen()),
      ),
    );

    expect(find.text('Select days and generate plan'), findsOneWidget);

    await tester.tap(find.byType(DropdownButton<int>));
    await tester.pumpAndSettle();
    
    // the dropdown item '5 days' appears twice when menu is open: one in the button, one in the menu
    await tester.tap(find.text('5 days').last);
    await tester.pumpAndSettle();

    await tester.tap(find.text('Generate Plan'));
    await tester.pumpAndSettle();

    verify(() => mockClient.generatePlan(days: 5)).called(1);
    expect(find.text('Veggie Stir Fry'), findsOneWidget);
    expect(find.text('2026-04-03'), findsOneWidget);
  });

  testWidgets('ShoppingListScreen shows shopping items', (tester) async {
    final mockClient = MockApiClient();
    when(() => mockClient.getShoppingList()).thenAnswer(
      (_) async => const [
        ShoppingItem(
          ingredientName: 'Tofu',
          quantity: 1,
          unit: 'block',
        ),
      ],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(mockClient)],
        child: const MaterialApp(home: ShoppingListScreen()),
      ),
    );
    await tester.pump();

    expect(find.text('Tofu'), findsOneWidget);
    expect(find.text('1.0 block'), findsOneWidget);
  });
}
