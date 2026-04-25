import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:fridgefriend_mobile/core/design/colors.dart';
import 'package:fridgefriend_mobile/core/design/spacing.dart';
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
        const SnackBar(
            content: Text('All items must have a name and quantity > 0',
                style: TextStyle(fontFamily: 'Inter'))),
      );
      return;
    }
    var savedCount = 0;
    for (final item in _draftItems) {
      final storage =
          item.storageLocation.isNotEmpty ? item.storageLocation : 'fridge';
      try {
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
        savedCount++;
      } catch (_) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
                content: Text('Failed to save "${item.displayName}"',
                    style: const TextStyle(fontFamily: 'Inter')),
                backgroundColor: AppColors.error),
          );
        }
        return;
      }
    }
    if (mounted && savedCount == _draftItems.length) {
      context.go('/');
    }
  }

  void _removeItem(int index) {
    setState(() {
      _draftItems.removeAt(index);
    });
  }

  Widget _buildConfidenceBadge(double? confidence) {
    if (confidence == null) return const SizedBox.shrink();
    Color color;
    if (confidence > 0.7) {
      color = AppColors.safeLater;
    } else if (confidence >= 0.4) {
      color = AppColors.thisWeek;
    } else {
      color = AppColors.error;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(AppSpacing.chipRadius),
        border: Border.all(color: color, width: 1.5),
      ),
      child: Text(
        '${(confidence * 100).toInt()}% Match',
        style: TextStyle(
            fontFamily: 'Inter',
            color: color,
            fontSize: 12,
            fontWeight: FontWeight.w800),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: Text('Review ${_draftItems.length} Items',
            style: const TextStyle(
                fontFamily: 'Inter', fontWeight: FontWeight.w800)),
        elevation: 0,
      ),
      body: _draftItems.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                   Text('No items detected',
                       style: TextStyle(
                           fontFamily: 'Inter',
                           fontSize: 18,
                           fontWeight: FontWeight.w600,
                           color: cs.onSurfaceVariant)),
                  const SizedBox(height: AppSpacing.lg),
                  FilledButton.icon(
                    onPressed: () => context.pushReplacement('/add-item'),
                    icon: const Icon(Icons.add_rounded),
                    label: const Text('Add Manually',
                        style: TextStyle(
                            fontFamily: 'Inter', fontWeight: FontWeight.bold)),
                  ),
                ],
              ),
            )
          : ListView.separated(
              padding: AppSpacing.screenPadding,
              itemCount: _draftItems.length,
              separatorBuilder: (_, __) =>
                  const SizedBox(height: AppSpacing.lg),
              itemBuilder: (context, index) {
                final item = _draftItems[index];
                return Container(
                  padding: AppSpacing.cardPadding,
                   decoration: BoxDecoration(
                     color: cs.surfaceContainer,
                     borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
                     border: Border.all(color: cs.outlineVariant, width: 2),
                    boxShadow: [
                      BoxShadow(
                          color: Theme.of(context)
                              .colorScheme
                              .shadow
                              .withValues(alpha: 0.12),
                          blurRadius: 4,
                          offset: const Offset(0, 2))
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(
                            child: TextFormField(
                              initialValue: item.displayName,
                               style: TextStyle(
                                   fontFamily: 'Inter',
                                   fontWeight: FontWeight.w800,
                                   fontSize: 20,
                                   color: cs.onSurface),
                              decoration: const InputDecoration(
                                  labelText: 'Name',
                                  labelStyle: TextStyle(
                                      fontWeight: FontWeight.normal,
                                      fontSize: 14)),
                              onChanged: (val) => _draftItems[index] =
                                  item.copyWith(displayName: val),
                            ),
                          ),
                          const SizedBox(width: AppSpacing.sm),
                          IconButton(
                            icon: const Icon(Icons.delete_outline_rounded,
                                color: AppColors.error, size: 28),
                            onPressed: () => _removeItem(index),
                          ),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.md),
                      Row(
                        children: [
                          Expanded(
                            flex: 2,
                            child: TextFormField(
                              initialValue: item.quantity.toString(),
                              style: const TextStyle(
                                  fontFamily: 'Inter',
                                  fontWeight: FontWeight.w600),
                              decoration:
                                  const InputDecoration(labelText: 'Qty'),
                              keyboardType: TextInputType.number,
                              onChanged: (val) => _draftItems[index] =
                                  item.copyWith(
                                      quantity: double.tryParse(val) ??
                                          item.quantity),
                            ),
                          ),
                          const SizedBox(width: AppSpacing.sm),
                          Expanded(
                            flex: 3,
                            child: TextFormField(
                              initialValue: item.unit,
                              style: const TextStyle(
                                  fontFamily: 'Inter',
                                  fontWeight: FontWeight.w600),
                              decoration:
                                  const InputDecoration(labelText: 'Unit'),
                              onChanged: (val) =>
                                  _draftItems[index] = item.copyWith(unit: val),
                            ),
                          ),
                          const SizedBox(width: AppSpacing.sm),
                          Expanded(
                            flex: 4,
                            child: TextFormField(
                              initialValue: item.storageLocation.isNotEmpty
                                  ? item.storageLocation
                                  : 'fridge',
                              style: const TextStyle(
                                  fontFamily: 'Inter',
                                  fontWeight: FontWeight.w600),
                              decoration:
                                  const InputDecoration(labelText: 'Storage'),
                              onChanged: (val) => _draftItems[index] =
                                  item.copyWith(storageLocation: val),
                            ),
                          ),
                        ],
                      ),
                      if (item.confidence != null) ...[
                        const SizedBox(height: AppSpacing.md),
                        _buildConfidenceBadge(item.confidence),
                      ],
                    ],
                  ),
                );
              },
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
            onPressed: _draftItems.isEmpty ? null : _saveAll,
            child: const Text('Save All Items',
                style: TextStyle(
                    fontFamily: 'Inter',
                    fontSize: 18,
                    fontWeight: FontWeight.w800)),
          ),
        ),
      ),
    );
  }
}
