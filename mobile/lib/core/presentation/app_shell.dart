import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:fridgefriend_mobile/features/settings/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/households/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

class AppShell extends ConsumerWidget {
  const AppShell({required this.child, super.key});

  final Widget child;

  static const _destinations = <String>[
    '/',
    '/recipes',
    '/meal-plan',
    '/shopping-list',
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Trigger device token registration (fires once on first build after auth).
    ref.watch(deviceTokenRegistrationProvider);

    // Subscribe to household SSE events and refresh inventory on changes.
    _watchHouseholdEvents(ref);

    final location = GoRouterState.of(context).uri.path;
    final currentIndex = switch (location) {
      '/recipes' => 1,
      '/meal-plan' => 2,
      '/shopping-list' => 3,
      _ => 0,
    };

    return Scaffold(
      appBar: AppBar(
        title: const Text('FridgeFriend'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () => context.push('/settings'),
          ),
        ],
      ),
      body: child,
      floatingActionButton: currentIndex == 0
          ? FloatingActionButton(
              onPressed: () => _showAddOptions(context),
              child: const Icon(Icons.add),
            )
          : null,
      bottomNavigationBar: NavigationBar(
        selectedIndex: currentIndex,
        onDestinationSelected: (index) {
          context.go(_destinations[index]);
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.kitchen_outlined),
            selectedIcon: Icon(Icons.kitchen),
            label: 'Inventory',
          ),
          NavigationDestination(
            icon: Icon(Icons.restaurant_menu_outlined),
            selectedIcon: Icon(Icons.restaurant_menu),
            label: 'Recipes',
          ),
          NavigationDestination(
            icon: Icon(Icons.calendar_month_outlined),
            selectedIcon: Icon(Icons.calendar_month),
            label: 'Meal Plan',
          ),
          NavigationDestination(
            icon: Icon(Icons.shopping_cart_outlined),
            selectedIcon: Icon(Icons.shopping_cart),
            label: 'Shopping',
          ),
        ],
      ),
    );
  }

  /// Watches the first household's SSE stream and invalidates inventory/activity
  /// providers whenever an event arrives, giving real-time sync behavior.
  void _watchHouseholdEvents(WidgetRef ref) {
    final householdsAsync = ref.watch(householdsProvider);
    final households = householdsAsync.valueOrNull;
    if (households == null || households.isEmpty) return;

    final householdId = households.first.id;
    final eventsAsync = ref.watch(householdEventsProvider(householdId));
    eventsAsync.whenData((_) {
      // A new SSE event arrived — refresh inventory and activity log.
      ref.invalidate(inventoryProvider);
      ref.invalidate(activityLogProvider(householdId));
    });
  }

  void _showAddOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.qr_code_scanner),
              title: const Text('Scan Barcode'),
              onTap: () {
                Navigator.pop(context);
                context.push('/scan/barcode');
              },
            ),
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('Take Photo'),
              onTap: () {
                Navigator.pop(context);
                context.push('/scan/photo');
              },
            ),
            ListTile(
              leading: const Icon(Icons.edit),
              title: const Text('Manual Entry'),
              onTap: () {
                Navigator.pop(context);
                context.push('/add-item');
              },
            ),
          ],
        ),
      ),
    );
  }
}
