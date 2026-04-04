import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/meal_planning/domain/meal_plan.dart';

class MealPlanScreen extends ConsumerStatefulWidget {
  const MealPlanScreen({super.key});

  @override
  ConsumerState<MealPlanScreen> createState() => _MealPlanScreenState();
}

class _MealPlanScreenState extends ConsumerState<MealPlanScreen> {
  int _selectedDays = 7;

  @override
  Widget build(BuildContext context) {
    final planState = ref.watch(mealPlanProvider);

    return Scaffold(
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              children: [
                const Text('Days:'),
                const SizedBox(width: 16),
                DropdownButton<int>(
                  value: _selectedDays,
                  items: [3, 4, 5, 6, 7]
                      .map((days) => DropdownMenuItem(
                            value: days,
                            child: Text('$days days'),
                          ))
                      .toList(),
                  onChanged: (value) {
                    if (value != null) {
                      setState(() => _selectedDays = value);
                    }
                  },
                ),
                const Spacer(),
                ElevatedButton(
                  onPressed: planState is AsyncLoading
                      ? null
                      : () {
                          ref.read(mealPlanProvider.notifier).generatePlan(days: _selectedDays);
                        },
                  child: const Text('Generate Plan'),
                ),
              ],
            ),
          ),
          Expanded(
            child: _buildPlanContent(planState),
          ),
        ],
      ),
    );
  }

  Widget _buildPlanContent(AsyncValue<MealPlan?> planState) {
    return planState.when(
      data: (mealPlan) {
        if (mealPlan == null || mealPlan.days.isEmpty) {
          return const Center(
            child: Text('No meal plan yet. Select days and generate one!'),
          );
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
    );
  }

  String _formatDate(DateTime date) {
    final month = date.month.toString().padLeft(2, '0');
    final day = date.day.toString().padLeft(2, '0');
    return '${date.year}-$month-$day';
  }
}
