import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:fridgefriend_mobile/core/network/api_client.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/meal_planning/domain/meal_plan.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/add_item_screen.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/inventory_screen.dart';
import 'package:fridgefriend_mobile/features/meal_planning/presentation/meal_plan_screen.dart';
import 'package:fridgefriend_mobile/features/meal_planning/presentation/shopping_list_screen.dart';
import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';
import 'package:fridgefriend_mobile/features/recommendations/presentation/recommendations_screen.dart';
import 'package:fridgefriend_mobile/router/app_router.dart';

class MockApiClient extends Mock implements ApiClient {}

void main() {
  Future<void> pumpRouterApp(
    WidgetTester tester,
    String initialLocation,
  ) async {
    final router = AppRouter.createRouter(initialLocation: initialLocation);
    final mockClient = MockApiClient();

    final inventoryItems = [
      InventoryItem(
        id: '1',
        displayName: 'Milk',
        quantity: 1,
        unit: 'L',
        storageLocation: 'Fridge',
        estimatedExpiryDate: DateTime.now().add(const Duration(days: 2)),
        confidence: 0.9,
        status: 'active',
        source: 'manual',
      ),
    ];
    when(() => mockClient.getInventoryItems()).thenAnswer((_) async => inventoryItems);
    
    // Create a mock notifier with initial data to bypass DB entirely
    final inventoryNotifier = InventoryNotifier.withInitialData(inventoryItems);

    when(() => mockClient.getRecommendations()).thenAnswer(
      (_) async => const [
        Recipe(
          id: 'recipe-1',
          title: 'Pasta Bake',
          coveragePct: 0.7,
          score: 0.88,
          prepMinutes: 30,
          missingItems: ['Mozzarella'],
        ),
      ],
    );
    when(() => mockClient.generatePlan()).thenAnswer(
      (_) async => MealPlan(
        planId: 'plan-1',
        days: [
          PlanDay(
            date: DateTime(2026, 4, 3),
            recipeId: 'recipe-1',
            recipeTitle: 'Pasta Bake',
          ),
        ],
        shoppingList: const [
          ShoppingItem(
            ingredientName: 'Mozzarella',
            quantity: 1,
            unit: 'bag',
          ),
        ],
      ),
    );
    when(() => mockClient.getShoppingList()).thenAnswer(
      (_) async => const [
        ShoppingItem(
          ingredientName: 'Mozzarella',
          quantity: 1,
          unit: 'bag',
        ),
      ],
    );
    when(
      () => mockClient.createInventoryItem(
        displayName: any(named: 'displayName'),
        quantity: any(named: 'quantity'),
        unit: any(named: 'unit'),
        storageLocation: any(named: 'storageLocation'),
      ),
    ).thenAnswer(
      (_) async => InventoryItem(
        id: '2',
        displayName: 'Eggs',
        quantity: 12,
        unit: 'pcs',
        storageLocation: 'Fridge',
        estimatedExpiryDate: DateTime.now().add(const Duration(days: 5)),
        confidence: 0.95,
        status: 'active',
        source: 'manual',
      ),
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(mockClient),
          inventoryProvider.overrideWith((ref) => inventoryNotifier),
        ],
        child: MaterialApp.router(routerConfig: router),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('home route resolves to inventory screen', (tester) async {
    await pumpRouterApp(tester, '/');

    expect(find.byType(InventoryScreen), findsOneWidget);
    expect(find.text('Milk'), findsOneWidget);
  });

  testWidgets('add-item route resolves to add item screen', (tester) async {
    await pumpRouterApp(tester, '/add-item');

    expect(find.byType(AddItemScreen), findsOneWidget);
    expect(find.text('Add Item'), findsOneWidget);
  });

  testWidgets('recipes route resolves to recommendations screen', (
    tester,
  ) async {
    await pumpRouterApp(tester, '/recipes');

    expect(find.byType(RecommendationsScreen), findsOneWidget);
    expect(find.text('Pasta Bake'), findsOneWidget);
  });

  testWidgets('meal-plan route resolves to meal plan screen', (tester) async {
    await pumpRouterApp(tester, '/meal-plan');

    expect(find.byType(MealPlanScreen), findsOneWidget);
    expect(find.text('Pasta Bake'), findsOneWidget);
  });

  testWidgets('shopping-list route resolves to shopping list screen', (
    tester,
  ) async {
    await pumpRouterApp(tester, '/shopping-list');

    expect(find.byType(ShoppingListScreen), findsOneWidget);
    expect(find.text('Mozzarella'), findsOneWidget);
  });
}
