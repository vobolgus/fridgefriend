import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:go_router/go_router.dart';

import 'package:fridgefriend_mobile/core/network/api_client.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/add_item_screen.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/inventory_screen.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

class MockApiClient extends Mock implements ApiClient {}

class _TestInventoryNotifier extends InventoryNotifier {
  _TestInventoryNotifier(List<InventoryItem> items)
      : super.withInitialData(items);

  @override
  Future<void> addItem({
    required String displayName,
    required double quantity,
    required String unit,
    required String storageLocation,
    String? source,
    String? canonicalName,
    String? canonicalIngredientId,
    double? confidence,
    DateTime? estimatedExpiryDate,
  }) async {
    final createdItem = InventoryItem(
      id: 'created-item',
      displayName: displayName,
      quantity: quantity,
      unit: unit,
      storageLocation: storageLocation,
      estimatedExpiryDate: estimatedExpiryDate,
      confidence: confidence,
      status: 'active',
      source: source ?? 'manual',
      canonicalName: canonicalName,
      canonicalIngredientId: canonicalIngredientId,
    );
    final currentItems = state.valueOrNull ?? const <InventoryItem>[];
    state = AsyncValue.data([...currentItems, createdItem]);
  }
}

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
    final inventoryNotifier = _TestInventoryNotifier(const []);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          inventoryProvider.overrideWith((ref) => inventoryNotifier),
        ],
        child: const MaterialApp(home: AddItemScreen()),
      ),
    );

    await tester.enterText(find.byType(TextFormField).at(0), 'Eggs');
    await tester.enterText(find.byType(TextFormField).at(1), '12');
    await tester.enterText(find.byType(TextFormField).at(2), 'pcs');
    await tester.tap(find.text('Pantry'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Save Item'));
    await tester.pumpAndSettle();

    final savedItems = inventoryNotifier.state.requireValue;
    expect(savedItems, hasLength(1));
    expect(savedItems.single.displayName, 'Eggs');
    expect(savedItems.single.quantity, 12);
    expect(savedItems.single.unit, 'pcs');
    expect(savedItems.single.storageLocation, 'pantry');
    expect(find.text('Save Item'), findsOneWidget);
  });

  testWidgets('AddItemScreen forwards scan metadata from initial item', (
    tester,
  ) async {
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
    final inventoryNotifier = _TestInventoryNotifier(const []);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          inventoryProvider.overrideWith((ref) => inventoryNotifier),
        ],
        child: MaterialApp(home: AddItemScreen(initialItem: draftItem)),
      ),
    );

    await tester.tap(find.text('Save Item'));
    await tester.pumpAndSettle();

    final savedItem = inventoryNotifier.state.requireValue.single;
    expect(savedItem.displayName, 'Greek Yogurt');
    expect(savedItem.quantity, 1);
    expect(savedItem.unit, 'container');
    expect(savedItem.storageLocation, 'fridge');
    expect(savedItem.source, 'barcode');
    expect(savedItem.canonicalName, 'Yogurt');
    expect(savedItem.canonicalIngredientId, 'ingredient-42');
    expect(savedItem.confidence, 0.82);
    expect(
      savedItem.estimatedExpiryDate,
      DateTime.parse('2026-04-12T00:00:00Z'),
    );
  });

  testWidgets('AddItemScreen pre-fills values from scanned item', (
    tester,
  ) async {
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
        child: MaterialApp(home: AddItemScreen(initialItem: draftItem)),
      ),
    );

    final fields =
        tester.widgetList<TextFormField>(find.byType(TextFormField)).toList();
    expect(fields[0].controller?.text, 'Greek Yogurt');
    expect(fields[1].controller?.text, '1');
    expect(fields[2].controller?.text, 'container');
    final fridgeChip =
        tester.widget<ChoiceChip>(find.widgetWithText(ChoiceChip, 'Fridge'));
    expect(fridgeChip.selected, isTrue);
  });

  testWidgets('InventoryScreen shows popup menu options and handles actions',
      (tester) async {
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

    when(() => mockClient.getInventoryItems())
        .thenAnswer((_) async => [testItem]);

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

  testWidgets('InventoryScreen shows Use Soon entry for expiring items',
      (tester) async {
    final testItem = InventoryItem(
      id: '1',
      displayName: 'Milk',
      quantity: 1,
      unit: 'L',
      storageLocation: 'Fridge',
      estimatedExpiryDate: DateTime.now().add(const Duration(days: 1)),
      confidence: 0.9,
      status: 'active',
      source: 'manual',
    );

    final router = GoRouter(
      initialLocation: '/',
      routes: [
        GoRoute(
          path: '/',
          builder: (context, state) => const InventoryScreen(),
        ),
        GoRoute(
          path: '/use-soon',
          builder: (context, state) =>
              const Scaffold(body: Text('Use Soon Page')),
        ),
      ],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          inventoryProvider.overrideWith(
            (ref) => InventoryNotifier.withInitialData([testItem]),
          ),
        ],
        child: MaterialApp.router(routerConfig: router),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));

    expect(find.text('1 item expiring soon'), findsOneWidget);
    expect(find.text('Tap to see what to use first'), findsOneWidget);

    await tester.tap(find.text('1 item expiring soon'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));

    expect(find.text('Use Soon Page'), findsOneWidget);
  });
}
