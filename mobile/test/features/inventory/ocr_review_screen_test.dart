import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:mocktail/mocktail.dart';

import 'package:fridgefriend_mobile/core/network/api_client.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/ocr_review_screen.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

class MockApiClient extends Mock implements ApiClient {}

void main() {
  testWidgets('OcrReviewScreen shows list of items and save button', (WidgetTester tester) async {
    final items = [
      InventoryItem(
        id: '1',
        displayName: 'Test Item',
        quantity: 1,
        unit: 'kg',
        storageLocation: 'fridge',
        estimatedExpiryDate: DateTime.now(),
        confidence: 0.9,
        status: 'active',
        source: 'scan',
      ),
    ];

    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          home: OcrReviewScreen(items: items),
        ),
      ),
    );

    expect(find.text('Review Items'), findsOneWidget);
    expect(find.text('Test Item'), findsOneWidget);
    expect(find.text('1.0'), findsOneWidget);
    expect(find.text('Confirm and Save'), findsOneWidget);
  });

  testWidgets('OcrReviewScreen saves OCR metadata with photo source', (
    WidgetTester tester,
  ) async {
    final mockClient = MockApiClient();
    final item = InventoryItem(
      id: 'draft-1',
      displayName: 'Spinach',
      quantity: 2,
      unit: 'bags',
      storageLocation: 'fridge',
      estimatedExpiryDate: DateTime.parse('2026-04-08T00:00:00Z'),
      confidence: 0.75,
      status: 'active',
      source: 'photo',
      canonicalName: 'spinach',
      canonicalIngredientId: 'ingredient-spinach',
    );

    when(() => mockClient.getInventoryItems()).thenAnswer((_) async => const []);
    when(
      () => mockClient.createInventoryItem(
        displayName: 'Spinach',
        quantity: 2.0,
        unit: 'bags',
        storageLocation: 'fridge',
        source: 'photo',
        canonicalName: 'spinach',
        canonicalIngredientId: 'ingredient-spinach',
        confidence: 0.75,
        estimatedExpiryDate: DateTime.parse('2026-04-08T00:00:00Z'),
      ),
    ).thenAnswer((_) async => item);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(mockClient)],
        child: MaterialApp.router(
          routerConfig: GoRouter(
            initialLocation: '/',
            routes: [
              GoRoute(
                path: '/',
                builder: (context, state) => OcrReviewScreen(items: [item]),
              ),
            ],
          ),
        ),
      ),
    );

    await tester.tap(find.text('Confirm and Save'));
    await tester.pump();

    verify(
      () => mockClient.createInventoryItem(
        displayName: 'Spinach',
        quantity: 2.0,
        unit: 'bags',
        storageLocation: 'fridge',
        source: 'photo',
        canonicalName: 'spinach',
        canonicalIngredientId: 'ingredient-spinach',
        confidence: 0.75,
      ),
    ).called(1);
  });
}
