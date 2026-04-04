import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fridgefriend_mobile/features/households/domain/household.dart';
import 'package:fridgefriend_mobile/features/households/presentation/household_screen.dart';
import 'package:fridgefriend_mobile/features/households/presentation/providers.dart';

void main() {
  testWidgets('HouseholdScreen shows empty state when no households', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          householdsProvider.overrideWith((ref) => Future.value([])),
        ],
        child: const MaterialApp(
          home: HouseholdScreen(),
        ),
      ),
    );

    // Initial loading state
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    await tester.pumpAndSettle();

    expect(find.text('You are not in any household.'), findsOneWidget);
    expect(find.text('Create Household'), findsOneWidget);
    expect(find.text('Join Household'), findsOneWidget);
  });

  testWidgets('HouseholdScreen shows household details when available', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          householdsProvider.overrideWith((ref) => Future.value([
            const Household(
              id: '1',
              name: 'My House',
              inviteCode: 'XYZ123',
              members: ['Alice', 'Bob'],
            ),
          ])),
        ],
        child: const MaterialApp(
          home: HouseholdScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Name: My House'), findsOneWidget);
    expect(find.text('Invite Code: XYZ123'), findsOneWidget);
    expect(find.text('Alice'), findsOneWidget);
    expect(find.text('Bob'), findsOneWidget);
  });
}
