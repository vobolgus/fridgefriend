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
    _draftItems = List.from(widget.items);
  }

  Future<void> _saveAll() async {
    for (final item in _draftItems) {
      await ref.read(inventoryProvider.notifier).addItem(
            displayName: item.displayName,
            quantity: item.quantity,
            unit: item.unit,
            storageLocation: item.storageLocation,
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
          ? const Center(child: Text('No items to review'))
          : ListView.builder(
              itemCount: _draftItems.length,
              itemBuilder: (context, index) {
                final item = _draftItems[index];
                return ListTile(
                  title: TextFormField(
                    initialValue: item.displayName,
                    decoration: const InputDecoration(labelText: 'Name'),
                    onChanged: (val) => _draftItems[index] = item.copyWith(displayName: val),
                  ),
                  subtitle: Row(
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
                    ],
                  ),
                  trailing: IconButton(
                    icon: const Icon(Icons.delete, color: Colors.red),
                    onPressed: () => _removeItem(index),
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
