import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class InventoryScreen extends ConsumerWidget {
  const InventoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(title: const Text('Inventory')),
      body: const Center(child: Text('Inventory screen')),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push('/add-item'),
        child: const Icon(Icons.add),
      ),
    );
  }
}
