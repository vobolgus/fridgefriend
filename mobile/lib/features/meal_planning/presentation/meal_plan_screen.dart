import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

class MealPlanScreen extends ConsumerStatefulWidget {
  const MealPlanScreen({super.key});

  @override
  ConsumerState<MealPlanScreen> createState() => _MealPlanScreenState();
}

class _MealPlanScreenState extends ConsumerState<MealPlanScreen> {
  int _selectedDays = 7;
  int? _generatedDays;

  @override
  Widget build(BuildContext context) {
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
                  onPressed: () {
                    setState(() => _generatedDays = _selectedDays);
                  },
                  child: const Text('Generate Plan'),
                ),
              ],
            ),
          ),
          Expanded(
            child: _generatedDays == null
                ? const Center(child: Text('Select days and generate plan'))
                : _buildPlanList(ref.watch(mealPlanProvider(_generatedDays!))),
          ),
        ],
      ),
    );
  }

  Widget _buildPlanList(AsyncValue plan) {
    return plan.when(
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
    );
  }

  String _formatDate(DateTime date) {
    final month = date.month.toString().padLeft(2, '0');
    final day = date.day.toString().padLeft(2, '0');
    return '${date.year}-$month-$day';
  }
}
