import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:fridgefriend_mobile/core/design/colors.dart';
import 'package:fridgefriend_mobile/core/design/spacing.dart';
import 'package:fridgefriend_mobile/router/app_router.dart';
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
    final location = GoRouterState.of(context).uri.path;

    // Only the main tab routes get the full shell chrome (AppBar,
    // BottomNav, FAB). Everything else renders as a full-screen page.
    // All routes live inside one ShellRoute to avoid the Flutter
    // navigator page-key assertion on cross-boundary navigation.
    if (!AppRouter.chromeRoutes.contains(location)) {
      return child;
    }

    ref.watch(deviceTokenRegistrationProvider);
    _watchHouseholdEvents(ref);

    final householdsAsync = ref.watch(householdsProvider);
    final households = householdsAsync.valueOrNull;
    final activeHousehold = households?.where((h) => h.isActive).firstOrNull ??
        households?.firstOrNull;
    final householdName = activeHousehold?.name;

    final currentIndex = switch (location) {
      '/recipes' => 1,
      '/meal-plan' => 2,
      '/shopping-list' => 3,
      _ => 0,
    };

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: AppColors.primary,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.kitchen_rounded,
                  size: 18, color: AppColors.textOnPrimary),
            ),
            const SizedBox(width: AppSpacing.sm),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'FridgeFriend',
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                        color: Theme.of(context).colorScheme.onSurface,
                      ),
                ),
                if (householdName != null)
                  Text(
                    householdName,
                    style: TextStyle(
                      fontFamily: 'Inter',
                      fontWeight: FontWeight.w500,
                      fontSize: 12,
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                  ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surfaceContainerHigh,
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.settings_outlined, size: 20),
            ),
            onPressed: () => context.push('/settings'),
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: child,
      floatingActionButton: currentIndex == 0
          ? _AnimatedFab(
              onPressed: () {
                HapticFeedback.mediumImpact();
                _showAddOptions(context);
              },
            )
          : null,
      bottomNavigationBar: NavigationBar(
        selectedIndex: currentIndex,
        onDestinationSelected: (index) {
          HapticFeedback.selectionClick();
          context.go(_destinations[index]);
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.kitchen_outlined),
            selectedIcon: Icon(Icons.kitchen_rounded),
            label: 'Inventory',
          ),
          NavigationDestination(
            icon: Icon(Icons.restaurant_menu_outlined),
            selectedIcon: Icon(Icons.restaurant_menu_rounded),
            label: 'Recipes',
          ),
          NavigationDestination(
            icon: Icon(Icons.calendar_month_outlined),
            selectedIcon: Icon(Icons.calendar_month_rounded),
            label: 'Plan',
          ),
          NavigationDestination(
            icon: Icon(Icons.shopping_cart_outlined),
            selectedIcon: Icon(Icons.shopping_cart_rounded),
            label: 'Shop',
          ),
        ],
      ),
    );
  }

  void _watchHouseholdEvents(WidgetRef ref) {
    final householdsAsync = ref.watch(householdsProvider);
    final households = householdsAsync.valueOrNull;
    if (households == null || households.isEmpty) return;

    final activeHousehold =
        households.where((h) => h.isActive).firstOrNull ?? households.first;
    final householdId = activeHousehold.id;

    ref.listen(householdEventsProvider(householdId), (previous, next) {
      next.whenData((_) {
        ref.invalidate(inventoryProvider);
        ref.invalidate(activityLogProvider(householdId));
        ref.invalidate(recommendationsProvider);
        ref.invalidate(mealPlanProvider);
        ref.invalidate(shoppingListProvider);
      });
    });
  }

  void _showAddOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.lg),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.secondaryContainer,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(Icons.qr_code_scanner_rounded,
                      color: Theme.of(context).colorScheme.onSecondaryContainer),
                ),
                title: const Text('Scan Barcode'),
                subtitle: const Text('Quick add with camera'),
                onTap: () {
                  HapticFeedback.lightImpact();
                  Navigator.pop(context);
                  context.push('/scan/barcode');
                },
              ),
              ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.tertiaryContainer,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(Icons.camera_alt_rounded,
                      color: Theme.of(context).colorScheme.onTertiaryContainer),
                ),
                title: const Text('Take Photo'),
                subtitle: const Text('AI-powered fridge scan'),
                onTap: () {
                  HapticFeedback.lightImpact();
                  Navigator.pop(context);
                  context.push('/scan/photo');
                },
              ),
              ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.primaryContainer,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(Icons.edit_rounded,
                      color: Theme.of(context).colorScheme.onPrimaryContainer),
                ),
                title: const Text('Manual Entry'),
                subtitle: const Text('Type in item details'),
                onTap: () {
                  HapticFeedback.lightImpact();
                  Navigator.pop(context);
                  context.push('/add-item');
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _AnimatedFab extends StatefulWidget {
  final VoidCallback onPressed;

  const _AnimatedFab({required this.onPressed});

  @override
  State<_AnimatedFab> createState() => _AnimatedFabState();
}

class _AnimatedFabState extends State<_AnimatedFab>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _scaleAnimation = CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOutBack,
    );
    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(
      scale: _scaleAnimation,
      child: FloatingActionButton(
        onPressed: widget.onPressed,
        child: const Icon(Icons.add_rounded, size: 28),
      ),
    );
  }
}
