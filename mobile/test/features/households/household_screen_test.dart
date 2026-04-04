import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:fridgefriend_mobile/features/households/domain/household.dart';
import 'package:fridgefriend_mobile/features/households/data/household_repository.dart';
import 'package:fridgefriend_mobile/features/households/presentation/household_screen.dart';
import 'package:fridgefriend_mobile/features/households/presentation/providers.dart';

class MockHouseholdRepository extends Mock implements HouseholdRepository {}

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
              isActive: true,
            ),
          ])),
        ],
        child: const MaterialApp(
          home: HouseholdScreen(),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Your Households'), findsOneWidget);
    expect(find.text('My House'), findsOneWidget);
    expect(find.text('2 members • Invite Code: XYZ123'), findsOneWidget);
    expect(find.text('Active'), findsOneWidget);
    expect(find.text('alice@test.com'), findsOneWidget);
    expect(find.text('bob@test.com'), findsOneWidget);
  });

  testWidgets('HouseholdScreen lets users switch active household', (WidgetTester tester) async {
    final repository = MockHouseholdRepository();
    when(() => repository.setActiveHousehold('2')).thenAnswer((_) async {});

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          householdsProvider.overrideWith((ref) => Future.value([
            Household(
              id: '1',
              name: 'Home',
              inviteCode: 'HOME1',
              members: const [
                HouseholdMember(id: '1', userId: 'u1', email: 'alice@test.com', role: 'owner'),
              ],
              isActive: true,
            ),
            Household(
              id: '2',
              name: 'Cabin',
              inviteCode: 'CABIN2',
              members: const [
                HouseholdMember(id: '2', userId: 'u2', email: 'bob@test.com', role: 'member'),
              ],
            ),
          ])),
          householdRepositoryProvider.overrideWithValue(repository),
        ],
        child: const MaterialApp(home: HouseholdScreen()),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Set Active'), findsOneWidget);

    await tester.tap(find.text('Set Active'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    verify(() => repository.setActiveHousehold('2')).called(1);
    expect(find.text('Cabin is now active'), findsOneWidget);
  });
}
