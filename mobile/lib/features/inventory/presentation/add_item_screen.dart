import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

class AddItemScreen extends ConsumerStatefulWidget {
  const AddItemScreen({this.initialItem, super.key});

  final InventoryItem? initialItem;

  @override
  ConsumerState<AddItemScreen> createState() => _AddItemScreenState();
}

class _AddItemScreenState extends ConsumerState<AddItemScreen> {
  late final TextEditingController _nameController;
  late final TextEditingController _quantityController;
  late final TextEditingController _unitController;
  late final TextEditingController _storageController;
  final _formKey = GlobalKey<FormState>();

  bool get _isEditing {
    final initialItem = widget.initialItem;
    if (initialItem == null) {
      return false;
    }

    return initialItem.id.isNotEmpty &&
        !initialItem.id.startsWith('offline_') &&
        !initialItem.id.startsWith('draft_') &&
        !initialItem.id.startsWith('draft-');
  }

  @override
  void initState() {
    super.initState();
    final initialItem = widget.initialItem;
    _nameController = TextEditingController(
      text: initialItem?.displayName ?? '',
    );
    _quantityController = TextEditingController(
      text: initialItem != null ? _formatQuantity(initialItem.quantity) : '',
    );
    _unitController = TextEditingController(text: initialItem?.unit ?? '');
    _storageController = TextEditingController(
      text: initialItem?.storageLocation ?? '',
    );
  }

  @override
  void dispose() {
    _nameController.dispose();
    _quantityController.dispose();
    _unitController.dispose();
    _storageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_isEditing ? 'Edit Item' : 'Add Item')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: ListView(
            children: [
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(labelText: 'Item name'),
                validator: (value) =>
                    (value == null || value.trim().isEmpty) ? 'Enter a name' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _quantityController,
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
                controller: _unitController,
                decoration: const InputDecoration(labelText: 'Unit'),
                validator: (value) =>
                    (value == null || value.trim().isEmpty) ? 'Enter a unit' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _storageController,
                decoration: const InputDecoration(labelText: 'Storage location'),
                validator: (value) => (value == null || value.trim().isEmpty)
                    ? 'Enter a storage location'
                    : null,
              ),
              const SizedBox(height: 24),
              FilledButton(
                onPressed: () async {
                  if (!_formKey.currentState!.validate()) {
                    return;
                  }

                  if (_isEditing) {
                    try {
                      await ref.read(inventoryProvider.notifier).editItem(
                            id: widget.initialItem!.id,
                            displayName: _nameController.text.trim(),
                            quantity: double.parse(_quantityController.text.trim()),
                            unit: _unitController.text.trim(),
                            storageLocation: _storageController.text.trim(),
                            version: widget.initialItem?.version,
                          );
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Item updated')),
                        );
                        await Navigator.of(context).maybePop();
                      }
                    } catch (e) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text(e.toString()),
                            backgroundColor: Colors.red,
                          ),
                        );
                      }
                    }
                  } else {
                    await ref.read(inventoryProvider.notifier).addItem(
                          displayName: _nameController.text.trim(),
                          quantity: double.parse(_quantityController.text.trim()),
                          unit: _unitController.text.trim(),
                          storageLocation: _storageController.text.trim(),
                          source: widget.initialItem?.source,
                          canonicalName: widget.initialItem?.canonicalName,
                          canonicalIngredientId:
                              widget.initialItem?.canonicalIngredientId,
                          confidence: widget.initialItem?.confidence,
                          estimatedExpiryDate:
                              widget.initialItem?.estimatedExpiryDate,
                        );
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Item added')),
                      );
                      await Navigator.of(context).maybePop();
                    }
                  }
                },
                child: Text(_isEditing ? 'Save changes' : 'Save item'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatQuantity(double quantity) {
    if (quantity == quantity.truncateToDouble()) {
      return quantity.toInt().toString();
    }

    return quantity.toString();
  }
}
