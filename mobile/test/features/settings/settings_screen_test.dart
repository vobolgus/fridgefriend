import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:fridgefriend_mobile/core/network/api_client.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/settings/presentation/settings_screen.dart';

class MockApiClient extends Mock implements ApiClient {}

void main() {
  testWidgets('SettingsScreen renders correctly', (WidgetTester tester) async {
    final mockClient = MockApiClient();
    when(() => mockClient.getNotificationPreferences()).thenAnswer(
      (_) async => {'expiry_reminder_enabled': true},
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(mockClient)],
        child: const MaterialApp(
          home: SettingsScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Settings'), findsOneWidget);
    expect(find.text('Push Notifications'), findsOneWidget);
    expect(find.text('Sign Out'), findsOneWidget);
    expect(find.text('App Version'), findsOneWidget);
  });
}
