import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fridgefriend_mobile/features/inventory/presentation/add_item_screen.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/inventory_screen.dart';
import 'package:fridgefriend_mobile/features/meal_planning/presentation/meal_plan_screen.dart';
import 'package:fridgefriend_mobile/features/meal_planning/presentation/shopping_list_screen.dart';
import 'package:fridgefriend_mobile/features/recommendations/presentation/recommendations_screen.dart';
import 'package:fridgefriend_mobile/router/app_router.dart';

void main() {
  Future<void> pumpRouterApp(
    WidgetTester tester,
    String initialLocation,
  ) async {
    final router = AppRouter.createRouter(initialLocation: initialLocation);

    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp.router(routerConfig: router),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('home route resolves to inventory screen', (tester) async {
    await pumpRouterApp(tester, '/');

    expect(find.byType(InventoryScreen), findsOneWidget);
    expect(find.text('Inventory screen'), findsOneWidget);
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
    expect(find.text('Recommendations screen'), findsOneWidget);
  });

  testWidgets('meal-plan route resolves to meal plan screen', (tester) async {
    await pumpRouterApp(tester, '/meal-plan');

    expect(find.byType(MealPlanScreen), findsOneWidget);
    expect(find.text('Meal Plan screen'), findsOneWidget);
  });

  testWidgets('shopping-list route resolves to shopping list screen', (
    tester,
  ) async {
    await pumpRouterApp(tester, '/shopping-list');

    expect(find.byType(ShoppingListScreen), findsOneWidget);
    expect(find.text('Shopping List screen'), findsOneWidget);
  });
}
