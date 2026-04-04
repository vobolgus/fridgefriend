import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/barcode_scan_screen.dart';

void main() {
  testWidgets('BarcodeScanScreen shows manual entry',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(
          home: BarcodeScanScreen(),
        ),
      ),
    );

    expect(find.text('Scan Barcode'), findsOneWidget);
    expect(find.text('Manual Entry'), findsOneWidget);
    expect(find.text('Enter barcode number'), findsOneWidget);
    expect(find.byIcon(Icons.arrow_forward_rounded), findsOneWidget);
    expect(find.byType(TextField), findsOneWidget);
  });
}
