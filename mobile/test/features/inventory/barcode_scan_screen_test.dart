import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/barcode_scan_screen.dart';

void main() {
  testWidgets('BarcodeScanScreen shows manual entry', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: BarcodeScanScreen(),
      ),
    );

    expect(find.text('Scan Barcode'), findsOneWidget);
    expect(find.text('Or enter manually:'), findsOneWidget);
    expect(find.text('Submit'), findsOneWidget);
    expect(find.byType(TextField), findsOneWidget);
  });
}
