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
            Household(
              id: '1',
              name: 'My House',
              inviteCode: 'XYZ123',
              members: [
                const HouseholdMember(id: '1', userId: 'u1', email: 'alice@test.com', role: 'owner'),
                const HouseholdMember(id: '2', userId: 'u2', email: 'bob@test.com', role: 'member'),
              ],
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
    expect(find.text('alice@test.com'), findsOneWidget);
    expect(find.text('bob@test.com'), findsOneWidget);
  });
}
