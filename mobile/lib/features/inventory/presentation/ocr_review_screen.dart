import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

class OcrReviewScreen extends ConsumerStatefulWidget {
  const OcrReviewScreen({required this.items, super.key});

  final List<InventoryItem> items;

  @override
  ConsumerState<OcrReviewScreen> createState() => _OcrReviewScreenState();
}

class _OcrReviewScreenState extends ConsumerState<OcrReviewScreen> {
  late List<InventoryItem> _draftItems;

  @override
  void initState() {
    super.initState();
    _draftItems = widget.items
        .where((item) => item.displayName.trim().isNotEmpty)
        .toList();
  }

  bool _validate() {
    for (final item in _draftItems) {
      if (item.displayName.trim().isEmpty || item.quantity <= 0) {
        return false;
      }
    }
    return true;
  }

  Future<void> _saveAll() async {
    if (!_validate()) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('All items must have a name and quantity greater than zero')),
      );
      return;
    }
    for (final item in _draftItems) {
      final storage = item.storageLocation.isNotEmpty
          ? item.storageLocation
          : 'fridge';
      await ref.read(inventoryProvider.notifier).addItem(
            displayName: item.displayName,
            quantity: item.quantity,
            unit: item.unit,
            storageLocation: storage,
            source: 'photo',
            canonicalName: item.canonicalName,
            canonicalIngredientId: item.canonicalIngredientId,
            confidence: item.confidence,
          );
    }
    if (mounted) {
      context.go('/');
    }
  }

  void _removeItem(int index) {
    setState(() {
      _draftItems.removeAt(index);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Review Items')),
      body: _draftItems.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('No items detected'),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => context.pushReplacement('/add-item'),
                    child: const Text('Add Manually'),
                  ),
                ],
              ),
            )
          : ListView.builder(
              itemCount: _draftItems.length,
              itemBuilder: (context, index) {
                final item = _draftItems[index];
                return Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: TextFormField(
                              initialValue: item.displayName,
                              decoration: const InputDecoration(labelText: 'Name'),
                              onChanged: (val) => _draftItems[index] = item.copyWith(displayName: val),
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.delete, color: Colors.red),
                            onPressed: () => _removeItem(index),
                          ),
                        ],
                      ),
                      Row(
                        children: [
                          Expanded(
                            child: TextFormField(
                              initialValue: item.quantity.toString(),
                              decoration: const InputDecoration(labelText: 'Qty'),
                              keyboardType: TextInputType.number,
                              onChanged: (val) => _draftItems[index] = item.copyWith(quantity: double.tryParse(val) ?? item.quantity),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: TextFormField(
                              initialValue: item.unit,
                              decoration: const InputDecoration(labelText: 'Unit'),
                              onChanged: (val) => _draftItems[index] = item.copyWith(unit: val),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: TextFormField(
                              initialValue: item.storageLocation.isNotEmpty ? item.storageLocation : 'fridge',
                              decoration: const InputDecoration(labelText: 'Storage'),
                              onChanged: (val) => _draftItems[index] = item.copyWith(storageLocation: val),
                            ),
                          ),
                        ],
                      ),
                      const Divider(),
                    ],
                  ),
                );
              },
            ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: ElevatedButton(
            onPressed: _draftItems.isEmpty ? null : _saveAll,
            child: const Text('Confirm and Save'),
          ),
        ),
      ),
    );
  }
}
