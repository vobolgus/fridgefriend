import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:fridgefriend_mobile/core/presentation/app_shell.dart';
import 'package:fridgefriend_mobile/features/auth/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/auth/presentation/sign_in_screen.dart';
import 'package:fridgefriend_mobile/features/onboarding/presentation/onboarding_screen.dart';
import 'package:fridgefriend_mobile/features/onboarding/presentation/providers.dart';
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
  final isOnboardingComplete = ref.watch(onboardingCompleteProvider);

  return AppRouter.createRouter(
    initialLocation: '/',
    redirect: (context, state) {
      final isAuth = authState.valueOrNull != null;
      final isGoingToSignIn = state.matchedLocation == '/sign-in';
      final isGoingToOnboarding = state.matchedLocation == '/onboarding';

      if (!isAuth && !isOnboardingComplete && !isGoingToOnboarding) {
        return '/onboarding';
      }

      if (!isAuth && isOnboardingComplete && !isGoingToSignIn) {
        return '/sign-in';
      }

      if (isAuth && (isGoingToSignIn || isGoingToOnboarding)) {
        return '/';
      }

      return null;
    },
  );
});

class AppRouter {
  static Page<dynamic> _fadeTransitionPage(
      BuildContext context, GoRouterState state, Widget child) {
    return CustomTransitionPage<void>(
      key: state.pageKey,
      child: child,
      transitionDuration: const Duration(milliseconds: 200),
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        return FadeTransition(opacity: animation, child: child);
      },
    );
  }

  static Page<dynamic> _slideRightTransitionPage(
      BuildContext context, GoRouterState state, Widget child) {
    return CustomTransitionPage<void>(
      key: state.pageKey,
      child: child,
      transitionDuration: const Duration(milliseconds: 300),
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        const begin = Offset(1.0, 0.0);
        const end = Offset.zero;
        const curve = Curves.easeOutCubic;
        final tween =
            Tween(begin: begin, end: end).chain(CurveTween(curve: curve));
        return SlideTransition(
          position: animation.drive(tween),
          child: child,
        );
      },
    );
  }

  static Page<dynamic> _slideUpTransitionPage(
      BuildContext context, GoRouterState state, Widget child) {
    return CustomTransitionPage<void>(
      key: state.pageKey,
      child: child,
      transitionDuration: const Duration(milliseconds: 350),
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        const begin = Offset(0.0, 1.0);
        const end = Offset.zero;
        const curve = Curves.easeOutCubic;
        final tween =
            Tween(begin: begin, end: end).chain(CurveTween(curve: curve));
        return SlideTransition(
          position: animation.drive(tween),
          child: child,
        );
      },
    );
  }

  static GoRouter createRouter({
    String initialLocation = '/',
    String? Function(BuildContext, GoRouterState)? redirect,
  }) {
    return GoRouter(
      initialLocation: initialLocation,
      redirect: redirect,
      routes: [
        GoRoute(
          path: '/onboarding',
          name: 'onboarding',
          builder: (context, state) => const OnboardingScreen(),
        ),
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
              pageBuilder: (context, state) =>
                  _fadeTransitionPage(context, state, const InventoryScreen()),
            ),
            GoRoute(
              path: '/recipes',
              name: 'recipes',
              pageBuilder: (context, state) => _fadeTransitionPage(
                  context, state, const RecommendationsScreen()),
            ),
            GoRoute(
              path: '/meal-plan',
              name: 'meal-plan',
              pageBuilder: (context, state) =>
                  _fadeTransitionPage(context, state, const MealPlanScreen()),
            ),
            GoRoute(
              path: '/shopping-list',
              name: 'shopping-list',
              pageBuilder: (context, state) => _fadeTransitionPage(
                  context, state, const ShoppingListScreen()),
            ),
          ],
        ),
        GoRoute(
          path: '/add-item',
          name: 'add-item',
          pageBuilder: (context, state) => _slideRightTransitionPage(
            context,
            state,
            AddItemScreen(
              initialItem: state.extra is InventoryItem
                  ? state.extra! as InventoryItem
                  : null,
            ),
          ),
        ),
        GoRoute(
          path: '/settings',
          name: 'settings',
          pageBuilder: (context, state) =>
              _slideRightTransitionPage(context, state, const SettingsScreen()),
        ),
        GoRoute(
          path: '/household',
          name: 'household',
          pageBuilder: (context, state) => _slideRightTransitionPage(
              context, state, const HouseholdScreen()),
        ),
        GoRoute(
          path: '/activity-log',
          name: 'activity-log',
          pageBuilder: (context, state) {
            final extra = state.extra;
            final householdId = extra is String ? extra : '';
            return _slideRightTransitionPage(
                context, state, ActivityLogScreen(householdId: householdId));
          },
        ),
        GoRoute(
          path: '/scan/barcode',
          name: 'scan-barcode',
          pageBuilder: (context, state) => _slideRightTransitionPage(
              context, state, const BarcodeScanScreen()),
        ),
        GoRoute(
          path: '/scan/photo',
          name: 'scan-photo',
          pageBuilder: (context, state) => _slideRightTransitionPage(
              context, state, const PhotoUploadScreen()),
        ),
        GoRoute(
          path: '/scan/photo/review',
          name: 'scan-photo-review',
          pageBuilder: (context, state) {
            final extra = state.extra;
            final rawItems = switch (extra) {
              final List<dynamic> value => value,
              final Map<String, dynamic> value => () {
                  final candidate = value['draft_items'] ??
                      value['draftItems'] ??
                      value['items'];
                  return candidate is List ? candidate : const <dynamic>[];
                }(),
              _ => const <dynamic>[],
            };
            final items =
                rawItems.whereType<InventoryItem>().toList(growable: false);
            return _slideRightTransitionPage(
                context, state, OcrReviewScreen(items: items));
          },
        ),
        GoRoute(
          path: '/use-soon',
          name: 'use-soon',
          pageBuilder: (context, state) =>
              _slideRightTransitionPage(context, state, const UseSoonScreen()),
        ),
        GoRoute(
          path: '/recipes/:id',
          name: 'recipe-detail',
          pageBuilder: (context, state) {
            final extra = state.extra;
            if (extra is Recipe) {
              return _slideUpTransitionPage(
                  context, state, RecipeDetailScreen(recipe: extra));
            }
            return _slideUpTransitionPage(
                context, state, const RecommendationsScreen());
          },
        ),
      ],
    );
  }
}
