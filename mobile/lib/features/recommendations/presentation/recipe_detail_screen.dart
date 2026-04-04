import 'package:flutter/material.dart';
import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';

class RecipeDetailScreen extends StatelessWidget {
  const RecipeDetailScreen({required this.recipe, super.key});

  final Recipe recipe;

  @override
  Widget build(BuildContext context) {
    // In a real app, Recipe might have full ingredient list, dietary tags, substitutions, etc.
    // For now we render what we can from the domain model or mock it for UI demonstration.
    final dietaryTags = ['Healthy', 'Quick']; // Mocked for UI requirements
    final substitutions = {'Mozzarella': 'Cheddar'}; // Mocked for UI requirements

    return Scaffold(
      appBar: AppBar(title: Text(recipe.title)),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          Text(
            recipe.title,
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              const Icon(Icons.timer, size: 16),
              const SizedBox(width: 4),
              Text('${recipe.prepMinutes} min'),
              const Spacer(),
              ...dietaryTags.map(
                (tag) => Padding(
                  padding: const EdgeInsets.only(left: 4.0),
                  child: Chip(
                    label: Text(tag, style: const TextStyle(fontSize: 10)),
                    padding: EdgeInsets.zero,
                  ),
                ),
              ),
            ],
          ),
          const Divider(height: 32),
          Text(
            'Coverage: ${(recipe.coveragePct * 100).toStringAsFixed(0)}%',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 16),
          Text(
            'Missing Items',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 8),
          if (recipe.missingItems.isEmpty)
            const Text('You have all ingredients!')
          else
            ...recipe.missingItems.map(
              (item) => ListTile(
                leading: const Icon(Icons.cancel, color: Colors.red),
                title: Text(item),
                dense: true,
              ),
            ),
          const Divider(height: 32),
          Text(
            'Substitutions',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 8),
          ...substitutions.entries.map(
            (entry) => ListTile(
              leading: const Icon(Icons.swap_horiz, color: Colors.orange),
              title: Text('${entry.key} → ${entry.value}'),
              dense: true,
            ),
          ),
        ],
      ),
    );
  }
}
