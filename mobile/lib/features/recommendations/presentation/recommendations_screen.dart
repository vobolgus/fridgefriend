import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

class RecommendationsScreen extends ConsumerWidget {
  const RecommendationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recommendations = ref.watch(recommendationsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Recipes')),
      body: recommendations.when(
        data: (recipes) {
          if (recipes.isEmpty) {
            return const Center(child: Text('No recipe recommendations yet'));
          }

          return ListView.builder(
            itemCount: recipes.length,
            itemBuilder: (context, index) {
              final recipe = recipes[index];
              final missingItems = recipe.missingItems.isEmpty
                  ? 'Nothing missing'
                  : recipe.missingItems.join(', ');

              return Card(
                margin: const EdgeInsets.all(12),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        recipe.title,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      Text('Coverage: ${(recipe.coveragePct * 100).toStringAsFixed(0)}%'),
                      Text('Prep time: ${recipe.prepMinutes} min'),
                      Text('Missing items: $missingItems'),
                    ],
                  ),
                ),
              );
            },
          );
        },
        error: (error, _) => Center(child: Text('Failed to load recipes: $error')),
        loading: () => const Center(child: CircularProgressIndicator()),
      ),
    );
  }
}
