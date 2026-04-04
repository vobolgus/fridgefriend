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
    final testItem = InventoryItem(
      id: '1',
      displayName: 'Milk',
      quantity: 1,
      unit: 'L',
      storageLocation: 'Fridge',
      estimatedExpiryDate: DateTime.now().add(const Duration(days: 4)),
      confidence: 0.9,
      status: 'active',
      source: 'manual',
    );

    when(() => mockClient.getInventoryItems()).thenAnswer(
      (_) async => [testItem],
    );

    // Override inventoryProvider to start with data immediately (no async wait)
    final preloadedNotifier = InventoryNotifier.withInitialData([testItem]);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(mockClient),
          inventoryProvider.overrideWith((ref) => preloadedNotifier),
        ],
        child: const MaterialApp(home: InventoryScreen()),
      ),
    );
    await tester.pump();

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
        source: null,
        canonicalName: null,
        canonicalIngredientId: null,
        confidence: null,
        estimatedExpiryDate: null,
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
        source: null,
        canonicalName: null,
        canonicalIngredientId: null,
        confidence: null,
        estimatedExpiryDate: null,
      ),
    ).called(1);
    expect(find.text('Save item'), findsOneWidget);
  });

  testWidgets('AddItemScreen forwards scan metadata from initial item', (
    tester,
  ) async {
    final mockClient = MockApiClient();
    when(() => mockClient.getInventoryItems()).thenAnswer((_) async => const []);

    final draftItem = InventoryItem(
      id: 'draft-2',
      displayName: 'Greek Yogurt',
      quantity: 1,
      unit: 'container',
      storageLocation: 'fridge',
      estimatedExpiryDate: DateTime.parse('2026-04-12T00:00:00Z'),
      confidence: 0.82,
      status: 'active',
      source: 'barcode',
      canonicalName: 'Yogurt',
      canonicalIngredientId: 'ingredient-42',
    );

    when(
      () => mockClient.createInventoryItem(
        displayName: 'Greek Yogurt',
        quantity: 1.0,
        unit: 'container',
        storageLocation: 'fridge',
        source: 'barcode',
        canonicalName: 'Yogurt',
        canonicalIngredientId: 'ingredient-42',
        confidence: 0.82,
        estimatedExpiryDate: DateTime.parse('2026-04-12T00:00:00Z'),
      ),
    ).thenAnswer((_) async => draftItem);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(mockClient)],
        child: MaterialApp(home: AddItemScreen(initialItem: draftItem)),
      ),
    );

    await tester.tap(find.text('Save item'));
    await tester.pump();

    verify(
      () => mockClient.createInventoryItem(
        displayName: 'Greek Yogurt',
        quantity: 1.0,
        unit: 'container',
        storageLocation: 'fridge',
        source: 'barcode',
        canonicalName: 'Yogurt',
        canonicalIngredientId: 'ingredient-42',
        confidence: 0.82,
        estimatedExpiryDate: DateTime.parse('2026-04-12T00:00:00Z'),
      ),
    ).called(1);
  });

  testWidgets('AddItemScreen pre-fills values from scanned item', (
    tester,
  ) async {
    final mockClient = MockApiClient();
    when(() => mockClient.getInventoryItems()).thenAnswer((_) async => const []);

    final draftItem = InventoryItem(
      id: 'draft-1',
      displayName: 'Greek Yogurt',
      quantity: 1,
      unit: 'container',
      storageLocation: 'fridge',
      estimatedExpiryDate: DateTime.now().add(const Duration(days: 7)),
      confidence: 0.82,
      status: 'active',
      source: 'barcode',
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(mockClient)],
        child: MaterialApp(home: AddItemScreen(initialItem: draftItem)),
      ),
    );

    final fields = tester.widgetList<TextFormField>(find.byType(TextFormField)).toList();
    expect(fields[0].controller?.text, 'Greek Yogurt');
    expect(fields[1].controller?.text, '1');
    expect(fields[2].controller?.text, 'container');
    expect(fields[3].controller?.text, 'fridge');
  });

  testWidgets('InventoryScreen shows popup menu options and handles actions', (tester) async {
    final mockClient = MockApiClient();
    final testItem = InventoryItem(
      id: '1',
      displayName: 'Milk',
      quantity: 1,
      unit: 'L',
      storageLocation: 'Fridge',
      estimatedExpiryDate: DateTime.now().add(const Duration(days: 4)),
      confidence: 0.9,
      status: 'active',
      source: 'manual',
    );

    when(() => mockClient.getInventoryItems()).thenAnswer((_) async => [testItem]);

    final preloadedNotifier = InventoryNotifier.withInitialData([testItem]);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(mockClient),
          inventoryProvider.overrideWith((ref) => preloadedNotifier),
        ],
        child: const MaterialApp(home: Scaffold(body: InventoryScreen())),
      ),
    );
    await tester.pumpAndSettle();

    final menuFinder = find.byType(PopupMenuButton<String>);
    expect(menuFinder, findsOneWidget);
    await tester.tap(menuFinder);
    await tester.pumpAndSettle();

    expect(find.text('Mark Used'), findsOneWidget);
    expect(find.text('Mark Discarded'), findsOneWidget);
    expect(find.text('Mark Frozen'), findsOneWidget);

    await tester.tap(find.text('Mark Used'));
    await tester.pumpAndSettle();

    expect(find.text('Item marked as used'), findsOneWidget);
    expect(find.text('Undo'), findsOneWidget);
  });
}
