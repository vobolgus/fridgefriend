import 'package:flutter/material.dart';
import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';

class RecipeDetailScreen extends StatelessWidget {
  const RecipeDetailScreen({required this.recipe, super.key});

  final Recipe recipe;

  @override
  Widget build(BuildContext context) {
    // In a real app, Recipe might have full ingredient list, dietary tags, substitutions, etc.
    // For now we render what we can from the domain model or mock it for UI demonstration.
    final substitutions = recipe.substitutions;

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
          if (substitutions.isEmpty)
            const Text('No substitutions suggested')
          else
            ...substitutions.map(
              (sub) => ListTile(
                leading: const Icon(Icons.swap_horiz, color: Colors.orange),
                title: Text(sub),
                dense: true,
              ),
            ),
        ],
      ),
    );
  }
}
