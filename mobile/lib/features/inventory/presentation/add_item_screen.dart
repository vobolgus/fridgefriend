import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

class AddItemScreen extends ConsumerWidget {
  const AddItemScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final nameController = TextEditingController();
    final quantityController = TextEditingController();
    final unitController = TextEditingController();
    final storageController = TextEditingController();
    final formKey = GlobalKey<FormState>();

    return Scaffold(
      appBar: AppBar(title: const Text('Add Item')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: formKey,
          child: ListView(
            children: [
              TextFormField(
                controller: nameController,
                decoration: const InputDecoration(labelText: 'Item name'),
                validator: (value) =>
                    (value == null || value.trim().isEmpty) ? 'Enter a name' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: quantityController,
                decoration: const InputDecoration(labelText: 'Quantity'),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                validator: (value) {
                  final parsed = double.tryParse(value ?? '');
                  if (parsed == null || parsed <= 0) {
                    return 'Enter a valid quantity';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: unitController,
                decoration: const InputDecoration(labelText: 'Unit'),
                validator: (value) =>
                    (value == null || value.trim().isEmpty) ? 'Enter a unit' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: storageController,
                decoration: const InputDecoration(labelText: 'Storage location'),
                validator: (value) => (value == null || value.trim().isEmpty)
                    ? 'Enter a storage location'
                    : null,
              ),
              const SizedBox(height: 24),
              FilledButton(
                onPressed: () async {
                  if (!formKey.currentState!.validate()) {
                    return;
                  }

                  await ref.read(inventoryProvider.notifier).addItem(
                        displayName: nameController.text.trim(),
                        quantity: double.parse(quantityController.text.trim()),
                        unit: unitController.text.trim(),
                        storageLocation: storageController.text.trim(),
                      );

                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Item added')),
                    );
                    await Navigator.of(context).maybePop();
                  }
                },
                child: const Text('Save item'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
