import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:fridgefriend_mobile/core/presentation/app_shell.dart';
import 'package:fridgefriend_mobile/features/auth/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/auth/presentation/sign_in_screen.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/add_item_screen.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/inventory_screen.dart';
import 'package:fridgefriend_mobile/features/meal_planning/presentation/meal_plan_screen.dart';
import 'package:fridgefriend_mobile/features/meal_planning/presentation/shopping_list_screen.dart';
import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';
import 'package:fridgefriend_mobile/features/recommendations/presentation/recipe_detail_screen.dart';
import 'package:fridgefriend_mobile/features/recommendations/presentation/recommendations_screen.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/barcode_scan_screen.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/photo_upload_screen.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/use_soon_screen.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/ocr_review_screen.dart';
import 'package:fridgefriend_mobile/features/households/presentation/household_screen.dart';
import 'package:fridgefriend_mobile/features/households/presentation/activity_log_screen.dart';
import 'package:fridgefriend_mobile/features/settings/presentation/settings_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authStateProvider);

  return AppRouter.createRouter(
    initialLocation: '/',
    redirect: (context, state) {
      final isAuth = authState.valueOrNull != null;
      final isGoingToSignIn = state.matchedLocation == '/sign-in';

      if (!isAuth && !isGoingToSignIn) {
        return '/sign-in';
      }
      
      if (isAuth && isGoingToSignIn) {
        return '/';
      }

      return null;
    },
  );
});

class AppRouter {
  static GoRouter createRouter({
    String initialLocation = '/',
    String? Function(BuildContext, GoRouterState)? redirect,
  }) {
    return GoRouter(
      initialLocation: initialLocation,
      redirect: redirect,
      routes: [
        GoRoute(
          path: '/sign-in',
          name: 'sign-in',
          builder: (context, state) => const SignInScreen(),
        ),
        ShellRoute(
          builder: (context, state, child) => AppShell(child: child),
          routes: [
            GoRoute(
              path: '/',
              name: 'inventory',
              builder: (context, state) => const InventoryScreen(),
            ),
            GoRoute(
              path: '/recipes',
              name: 'recipes',
              builder: (context, state) => const RecommendationsScreen(),
            ),
            GoRoute(
              path: '/meal-plan',
              name: 'meal-plan',
              builder: (context, state) => const MealPlanScreen(),
            ),
            GoRoute(
              path: '/shopping-list',
              name: 'shopping-list',
              builder: (context, state) => const ShoppingListScreen(),
            ),
          ],
        ),
        GoRoute(
          path: '/add-item',
          name: 'add-item',
          builder: (context, state) => AddItemScreen(
            initialItem: state.extra is InventoryItem
                ? state.extra! as InventoryItem
                : null,
          ),
        ),
        GoRoute(
          path: '/settings',
          name: 'settings',
          builder: (context, state) => const SettingsScreen(),
        ),
        GoRoute(
          path: '/household',
          name: 'household',
          builder: (context, state) => const HouseholdScreen(),
        ),
        GoRoute(
          path: '/activity-log',
          name: 'activity-log',
          builder: (context, state) {
            final householdId = state.extra as String? ?? '';
            return ActivityLogScreen(householdId: householdId);
          },
        ),
        GoRoute(
          path: '/scan/barcode',
          name: 'scan-barcode',
          builder: (context, state) => const BarcodeScanScreen(),
        ),
        GoRoute(
          path: '/scan/photo',
          name: 'scan-photo',
          builder: (context, state) => const PhotoUploadScreen(),
        ),
        GoRoute(
          path: '/scan/photo/review',
          name: 'scan-photo-review',
          builder: (context, state) {
            final extra = state.extra;
            final rawItems = switch (extra) {
              final List<dynamic> value => value,
              final Map<String, dynamic> value =>
                (value['draft_items'] ?? value['draftItems'] ?? value['items'])
                        as List<dynamic>? ??
                    const [],
              _ => const <dynamic>[],
            };
            final items = rawItems
                .whereType<InventoryItem>()
                .toList(growable: false);
            return OcrReviewScreen(items: items);
          },
        ),
        GoRoute(
          path: '/use-soon',
          name: 'use-soon',
          builder: (context, state) => const UseSoonScreen(),
        ),
        GoRoute(
          path: '/recipes/:id',
          name: 'recipe-detail',
          builder: (context, state) {
            final extra = state.extra;
            if (extra is Recipe) {
              return RecipeDetailScreen(recipe: extra);
            }
            return const RecommendationsScreen();
          },
        ),
      ],
    );
  }
}
