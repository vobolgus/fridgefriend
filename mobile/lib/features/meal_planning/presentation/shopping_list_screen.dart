import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

class ShoppingListScreen extends ConsumerWidget {
  const ShoppingListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final shoppingItems = ref.watch(shoppingListProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Shopping List')),
      body: shoppingItems.when(
        data: (items) {
          if (items.isEmpty) {
            return const Center(child: Text('Shopping list is empty'));
          }

          return ListView.builder(
            itemCount: items.length,
            itemBuilder: (context, index) {
              final item = items[index];
              return CheckboxListTile(
                value: false,
                onChanged: (_) {},
                title: Text(item.ingredientName),
                subtitle: Text('${item.quantity} ${item.unit}'),
              );
            },
          );
        },
        error: (error, _) => Center(
          child: Text('Failed to load shopping list: $error'),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
      ),
    );
  }
}
