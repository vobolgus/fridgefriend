import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

class MealPlanScreen extends ConsumerWidget {
  const MealPlanScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final plan = ref.watch(mealPlanProvider);

    return Scaffold(
      body: plan.when(
        data: (mealPlan) {
          if (mealPlan.days.isEmpty) {
            return const Center(child: Text('No meal plan available'));
          }

          return ListView.builder(
            itemCount: mealPlan.days.length,
            itemBuilder: (context, index) {
              final day = mealPlan.days[index];

              return ListTile(
                leading: const Icon(Icons.calendar_today_outlined),
                title: Text(day.recipeTitle),
                subtitle: Text(_formatDate(day.date)),
              );
            },
          );
        },
        error: (error, _) => Center(child: Text('Failed to load meal plan: $error')),
        loading: () => const Center(child: CircularProgressIndicator()),
      ),
    );
  }

  String _formatDate(DateTime date) {
    final month = date.month.toString().padLeft(2, '0');
    final day = date.day.toString().padLeft(2, '0');
    return '${date.year}-$month-$day';
  }
}
