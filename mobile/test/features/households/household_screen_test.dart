import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:fridgefriend_mobile/database/app_database.dart';
import 'package:fridgefriend_mobile/database/sync_manager.dart';
import 'package:fridgefriend_mobile/features/households/domain/household.dart';
import 'package:fridgefriend_mobile/features/households/data/household_repository.dart';
import 'package:fridgefriend_mobile/features/households/presentation/household_screen.dart';
import 'package:fridgefriend_mobile/features/households/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart'
    as inventory_providers;

class MockHouseholdRepository extends Mock implements HouseholdRepository {}

class MockSyncManager extends Mock implements SyncManager {}

void main() {
  testWidgets('HouseholdScreen shows empty state when no households',
      (WidgetTester tester) async {
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

    expect(find.text('No households yet'), findsOneWidget);
    expect(
      find.text(
          'Create or join a household to share inventory and plan meals together.'),
      findsOneWidget,
    );
    expect(find.text('Create'), findsOneWidget);
    expect(find.text('Join'), findsOneWidget);
  });

  testWidgets('HouseholdScreen shows household details when available',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          householdsProvider.overrideWith((ref) => Future.value([
                Household(
                  id: '1',
                  name: 'My House',
                  inviteCode: 'XYZ123',
                  members: [
                    const HouseholdMember(
                        id: '1',
                        userId: 'u1',
                        email: 'alice@test.com',
                        role: 'owner'),
                    const HouseholdMember(
                        id: '2',
                        userId: 'u2',
                        email: 'bob@test.com',
                        role: 'member'),
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

    expect(find.text('YOUR HOUSEHOLDS'), findsOneWidget);
    expect(find.text('My House'), findsOneWidget);
    expect(find.text('2 members'), findsOneWidget);
    expect(find.text('Invite Code:'), findsOneWidget);
    expect(find.text('XYZ123'), findsOneWidget);
    expect(find.text('ACTIVE'), findsOneWidget);
    expect(find.text('Activity'), findsOneWidget);
  });

  testWidgets('HouseholdScreen lets users switch active household',
      (WidgetTester tester) async {
    final repository = MockHouseholdRepository();
    when(() => repository.setActiveHousehold('2')).thenAnswer((_) async {});

    final testDb = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(testDb.close);

    final mockSync = MockSyncManager();
    when(() => mockSync.pendingMutations()).thenAnswer((_) async => []);
    when(() => mockSync.flushPendingMutations()).thenAnswer((_) async {});

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          householdsProvider.overrideWith((ref) => Future.value([
                Household(
                  id: '1',
                  name: 'Home',
                  inviteCode: 'HOME1',
                  members: const [
                    HouseholdMember(
                        id: '1',
                        userId: 'u1',
                        email: 'alice@test.com',
                        role: 'owner'),
                  ],
                  isActive: true,
                ),
                Household(
                  id: '2',
                  name: 'Cabin',
                  inviteCode: 'CABIN2',
                  members: const [
                    HouseholdMember(
                        id: '2',
                        userId: 'u2',
                        email: 'bob@test.com',
                        role: 'member'),
                  ],
                ),
              ])),
          householdRepositoryProvider.overrideWithValue(repository),
          inventory_providers.appDatabaseProvider.overrideWithValue(testDb),
          inventory_providers.syncManagerProvider.overrideWithValue(mockSync),
        ],
        child: const MaterialApp(home: HouseholdScreen()),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Switch'), findsOneWidget);

    await tester.tap(find.text('Switch'));
    await tester.pumpAndSettle();

    verify(() => repository.setActiveHousehold('2')).called(1);
    expect(find.text('Cabin is now active'), findsOneWidget);
  });
}
