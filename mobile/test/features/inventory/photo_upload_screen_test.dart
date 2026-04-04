import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/photo_upload_screen.dart';

void main() {
  testWidgets('PhotoUploadScreen shows camera and gallery options',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(
          home: PhotoUploadScreen(),
        ),
      ),
    );

    expect(find.text('Scan Photo'), findsOneWidget);
    expect(find.text('Add via Photo'), findsOneWidget);
    expect(find.text('Camera'), findsOneWidget);
    expect(find.text('Gallery'), findsOneWidget);
  });
}
