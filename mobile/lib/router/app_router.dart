import 'package:go_router/go_router.dart';

import 'package:fridgefriend_mobile/core/presentation/app_shell.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/add_item_screen.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/inventory_screen.dart';
import 'package:fridgefriend_mobile/features/meal_planning/presentation/meal_plan_screen.dart';
import 'package:fridgefriend_mobile/features/meal_planning/presentation/shopping_list_screen.dart';
import 'package:fridgefriend_mobile/features/recommendations/presentation/recommendations_screen.dart';

class AppRouter {
  static GoRouter createRouter({String initialLocation = '/'}) {
    return GoRouter(
      initialLocation: initialLocation,
      routes: [
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
          builder: (context, state) => const AddItemScreen(),
        ),
      ],
    );
  }

  static final GoRouter router = createRouter();
}
