import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:fridgefriend_mobile/core/network/api_client.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';
import 'package:fridgefriend_mobile/features/recommendations/presentation/recommendations_screen.dart';

class MockApiClient extends Mock implements ApiClient {}

void main() {
  testWidgets('RecommendationsScreen shows recipe cards', (tester) async {
    final mockClient = MockApiClient();
    when(() => mockClient.getRecommendations()).thenAnswer(
      (_) async => const [
        Recipe(
          id: 'recipe-1',
          title: 'Creamy Pasta',
          coveragePct: 0.8,
          score: 0.9,
          prepMinutes: 20,
          missingItems: ['Parmesan'],
          substitutions: const [],
        ),
      ],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(mockClient)],
        child: const MaterialApp(home: RecommendationsScreen()),
      ),
    );
    await tester.pump();

    expect(find.text('Creamy Pasta'), findsOneWidget);
    expect(find.text('Coverage: 80%'), findsOneWidget);
    expect(find.text('20 min'), findsOneWidget);
    expect(find.text('1 missing'), findsOneWidget);
    expect(find.text('Parmesan'), findsOneWidget);
  });
}
