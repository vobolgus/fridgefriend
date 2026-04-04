import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/ocr_review_screen.dart';

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
}
