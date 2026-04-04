import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mocktail/mocktail.dart';

import 'package:fridgefriend_mobile/app.dart';
import 'package:fridgefriend_mobile/features/auth/domain/auth_service.dart';
import 'package:fridgefriend_mobile/features/auth/presentation/providers.dart';
import 'package:fridgefriend_mobile/core/network/api_client.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

import 'package:fridgefriend_mobile/core/presentation/providers/theme_provider.dart';

class MockApiClient extends Mock implements ApiClient {}

class MockAuthService extends Mock implements AuthService {}

void main() {
  testWidgets('App renders without crashing', (tester) async {
    final mockClient = MockApiClient();
    final mockAuthService = MockAuthService();
    when(() => mockAuthService.authStateChanges)
        .thenAnswer((_) => Stream.value(null));
    when(() => mockAuthService.getToken()).thenAnswer((_) async => null);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          apiClientProvider.overrideWithValue(mockClient),
          authServiceProvider.overrideWithValue(mockAuthService),
          themeModeProvider.overrideWith((ref) => ThemeMode.light),
        ],
        child: const MyApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
