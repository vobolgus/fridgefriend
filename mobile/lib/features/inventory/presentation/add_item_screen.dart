import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fridgefriend_mobile/core/design/colors.dart';
import 'package:fridgefriend_mobile/core/design/spacing.dart';
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
    if (initialItem == null) return false;
    return initialItem.id.isNotEmpty &&
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
      text: initialItem?.storageLocation ?? 'fridge',
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
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Text(
          _isEditing ? 'Edit Item' : 'Add Item',
          style:
              const TextStyle(fontFamily: 'Inter', fontWeight: FontWeight.w800),
        ),
        backgroundColor: AppColors.surface,
        elevation: 0,
      ),
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: ListView(
            padding: AppSpacing.screenPadding,
            children: [
              const Text(
                'ITEM DETAILS',
                style: TextStyle(
                  fontFamily: 'Inter',
                  fontWeight: FontWeight.w800,
                  color: AppColors.textSecondary,
                  letterSpacing: 1.2,
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: AppSpacing.md),
              TextFormField(
                controller: _nameController,
                style: const TextStyle(
                    fontFamily: 'Inter',
                    fontWeight: FontWeight.w600,
                    fontSize: 16),
                decoration: const InputDecoration(
                  labelText: 'Item name',
                  prefixIcon: Icon(Icons.fastfood_rounded),
                ),
                validator: (value) => (value == null || value.trim().isEmpty)
                    ? 'Enter a name'
                    : null,
              ),
              const SizedBox(height: AppSpacing.lg),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _quantityController,
                      style: const TextStyle(
                          fontFamily: 'Inter',
                          fontWeight: FontWeight.w600,
                          fontSize: 16),
                      decoration: const InputDecoration(labelText: 'Quantity'),
                      keyboardType:
                          const TextInputType.numberWithOptions(decimal: true),
                      validator: (value) {
                        final parsed = double.tryParse(value ?? '');
                        if (parsed == null || parsed <= 0) {
                          return 'Invalid quantity';
                        }
                        return null;
                      },
                    ),
                  ),
                  const SizedBox(width: AppSpacing.md),
                  Expanded(
                    child: TextFormField(
                      controller: _unitController,
                      style: const TextStyle(
                          fontFamily: 'Inter',
                          fontWeight: FontWeight.w600,
                          fontSize: 16),
                      decoration: const InputDecoration(
                          labelText: 'Unit (e.g. pcs, kg)'),
                      validator: (value) =>
                          (value == null || value.trim().isEmpty)
                              ? 'Enter a unit'
                              : null,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.xl),
              const Text(
                'STORAGE LOCATION',
                style: TextStyle(
                  fontFamily: 'Inter',
                  fontWeight: FontWeight.w800,
                  color: AppColors.textSecondary,
                  letterSpacing: 1.2,
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: AppSpacing.md),
              Wrap(
                spacing: AppSpacing.sm,
                runSpacing: AppSpacing.sm,
                children: ['fridge', 'freezer', 'pantry', 'counter'].map((loc) {
                  final isSelected =
                      _storageController.text.toLowerCase() == loc;
                  return ChoiceChip(
                    label: Text(
                      loc[0].toUpperCase() + loc.substring(1),
                      style: TextStyle(
                        fontFamily: 'Inter',
                        fontWeight: FontWeight.bold,
                        color: isSelected
                            ? AppColors.textOnPrimary
                            : AppColors.textPrimary,
                      ),
                    ),
                    selected: isSelected,
                    selectedColor: AppColors.primary,
                    backgroundColor: AppColors.surface,
                    shape: RoundedRectangleBorder(
                        borderRadius:
                            BorderRadius.circular(AppSpacing.chipRadius)),
                    onSelected: (selected) {
                      if (selected) {
                        setState(() {
                          _storageController.text = loc;
                        });
                      }
                    },
                  );
                }).toList(),
              ),
              const SizedBox(height: AppSpacing.xxxl),
            ],
          ),
        ),
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: AppSpacing.screenPadding,
          child: FilledButton(
            style: FilledButton.styleFrom(
              minimumSize: const Size.fromHeight(56),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(AppSpacing.buttonRadius)),
            ),
            onPressed: () async {
              HapticFeedback.mediumImpact();
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
                      const SnackBar(
                          content: Text('Item updated',
                              style: TextStyle(fontFamily: 'Inter'))),
                    );
                    await Navigator.of(context).maybePop();
                  }
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(e.toString(),
                            style: const TextStyle(fontFamily: 'Inter')),
                        backgroundColor: AppColors.error,
                      ),
                    );
                  }
                }
              } else {
                try {
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
                      const SnackBar(
                          content: Text('Item added',
                              style: TextStyle(fontFamily: 'Inter'))),
                    );
                    await Navigator.of(context).maybePop();
                  }
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(e.toString(),
                            style: const TextStyle(fontFamily: 'Inter')),
                        backgroundColor: AppColors.error,
                      ),
                    );
                  }
                }
              }
            },
            child: Text(
              _isEditing ? 'Save Changes' : 'Save Item',
              style: const TextStyle(
                  fontFamily: 'Inter',
                  fontSize: 16,
                  fontWeight: FontWeight.bold),
            ),
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
