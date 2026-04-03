import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mocktail/mocktail.dart';

import 'package:fridgefriend_mobile/app.dart';
import 'package:fridgefriend_mobile/core/network/api_client.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/meal_planning/domain/meal_plan.dart';

class MockApiClient extends Mock implements ApiClient {}

void main() {
  testWidgets('App renders without crashing', (tester) async {
    final mockClient = MockApiClient();
    when(() => mockClient.getInventoryItems()).thenAnswer((_) async => const []);
    when(() => mockClient.getRecommendations()).thenAnswer((_) async => const []);
    when(
      () => mockClient.generatePlan(),
    ).thenAnswer((_) async => const MealPlan(planId: 'plan', days: [], shoppingList: []));
    when(() => mockClient.getShoppingList()).thenAnswer((_) async => const []);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(mockClient)],
        child: const MyApp(),
      ),
    );
    await tester.pump();

    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
