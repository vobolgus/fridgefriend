import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:fridgefriend_mobile/core/network/api_client.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/add_item_screen.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/inventory_screen.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

class MockApiClient extends Mock implements ApiClient {}

void main() {
  testWidgets('InventoryScreen shows item names and urgency badge', (
    tester,
  ) async {
    final mockClient = MockApiClient();
    when(() => mockClient.getInventoryItems()).thenAnswer(
      (_) async => [
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
      ],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(mockClient)],
        child: const MaterialApp(home: InventoryScreen()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Milk'), findsOneWidget);
    expect(find.text('This Week'), findsOneWidget);
  });

  testWidgets('AddItemScreen submits item details', (tester) async {
    final mockClient = MockApiClient();
    when(() => mockClient.getInventoryItems()).thenAnswer((_) async => const []);
    when(
      () => mockClient.createInventoryItem(
        displayName: 'Eggs',
        quantity: 12.0,
        unit: 'pcs',
        storageLocation: 'Fridge',
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
        overrides: [apiClientProvider.overrideWithValue(mockClient)],
        child: const MaterialApp(home: AddItemScreen()),
      ),
    );

    await tester.enterText(find.byType(TextFormField).at(0), 'Eggs');
    await tester.enterText(find.byType(TextFormField).at(1), '12');
    await tester.enterText(find.byType(TextFormField).at(2), 'pcs');
    await tester.enterText(find.byType(TextFormField).at(3), 'Fridge');
    await tester.tap(find.text('Save item'));
    await tester.pump();

    verify(
      () => mockClient.createInventoryItem(
        displayName: 'Eggs',
        quantity: 12.0,
        unit: 'pcs',
        storageLocation: 'Fridge',
      ),
    ).called(1);
    expect(find.text('Save item'), findsOneWidget);
  });
}
