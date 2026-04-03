import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AddItemScreen extends ConsumerWidget {
  const AddItemScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(title: const Text('Add Item')),
      body: const Center(child: Text('Add Item screen')),
    );
  }
}
