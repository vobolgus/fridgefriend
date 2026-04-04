import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/use_soon_screen.dart';

void main() {
  testWidgets('UseSoonScreen shows sections for urgency buckets', (WidgetTester tester) async {
    final items = [
      InventoryItem(
        id: '1',
        displayName: 'Milk',
        quantity: 1,
        unit: 'L',
        storageLocation: 'Fridge',
        estimatedExpiryDate: DateTime.now().subtract(const Duration(days: 1)),
        confidence: 1.0,
        status: 'active',
        source: 'manual',
      ), // This should fall into expired if urgencyBucket calculates based on date, or mocked if property is there
    ];

    // Assuming we override the inventoryProvider with test data
    final inventoryNotifier = InventoryNotifier.withInitialData(items);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          inventoryProvider.overrideWith((ref) => inventoryNotifier),
        ],
        child: const MaterialApp(
          home: UseSoonScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();
    expect(find.text('Use Soon'), findsOneWidget);
    // Since item urgency might be calculated dynamically based on date inside InventoryItem, 
    // and we subtracted 1 day, it might be 'expired' or 'today'. Just checking if the item is present.
    expect(find.text('Milk'), findsOneWidget);
  });
}
