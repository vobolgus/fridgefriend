import 'package:flutter_test/flutter_test.dart';

import 'package:fridgefriend_mobile/database/conflict_resolver.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';

void main() {
  InventoryItem buildItem({
    String id = 'item-1',
    String displayName = 'Milk',
    double quantity = 1,
    String unit = 'L',
    String storageLocation = 'fridge',
    DateTime? estimatedExpiryDate,
    String status = 'active',
    String source = 'manual',
    String? canonicalName = 'milk',
    String? canonicalIngredientId = 'ingredient-1',
    double? confidence = 0.9,
    int version = 1,
  }) {
    return InventoryItem(
      id: id,
      displayName: displayName,
      quantity: quantity,
      unit: unit,
      storageLocation: storageLocation,
      estimatedExpiryDate: estimatedExpiryDate ?? DateTime(2026, 4, 10),
      confidence: confidence,
      status: status,
      source: source,
      canonicalName: canonicalName,
      canonicalIngredientId: canonicalIngredientId,
      version: version,
    );
  }

  test('test_server_wins_on_same_field_conflict', () {
    final baseItem = buildItem(quantity: 1, version: 1);
    final localItem = buildItem(quantity: 2, version: 1);
    final serverItem = buildItem(quantity: 3, version: 2);

    final merged = ConflictResolver(baseItem: baseItem).resolve(
      serverItem,
      localItem,
      {'quantity'},
    );

    expect(merged.quantity, 3);
  });

  test('test_local_wins_on_untouched_server_field', () {
    final baseItem = buildItem(quantity: 1, version: 1);
    final localItem = buildItem(quantity: 2, version: 1);
    final serverItem = buildItem(quantity: 1, version: 2);

    final merged = ConflictResolver(baseItem: baseItem).resolve(
      serverItem,
      localItem,
      {'quantity'},
    );

    expect(merged.quantity, 2);
  });

  test('test_mixed_fields_merge', () {
    final baseItem = buildItem(displayName: 'Milk', quantity: 1, version: 1);
    final localItem = buildItem(displayName: 'Milk', quantity: 2, version: 1);
    final serverItem = buildItem(
      displayName: 'Organic Milk',
      quantity: 1,
      version: 2,
    );

    final merged = ConflictResolver(baseItem: baseItem).resolve(
      serverItem,
      localItem,
      {'quantity'},
    );

    expect(merged.displayName, 'Organic Milk');
    expect(merged.quantity, 2);
  });

  test('test_version_always_from_server', () {
    final baseItem = buildItem(version: 1);
    final localItem = buildItem(quantity: 2, version: 1);
    final serverItem = buildItem(quantity: 1, version: 7);

    final merged = ConflictResolver(baseItem: baseItem).resolve(
      serverItem,
      localItem,
      {'quantity'},
    );

    expect(merged.version, 7);
    expect(merged.id, serverItem.id);
  });

  test('test_empty_dirty_fields_uses_all_server', () {
    final baseItem = buildItem(version: 1);
    final localItem = buildItem(
      displayName: 'Local Milk',
      quantity: 4,
      storageLocation: 'freezer',
      version: 1,
    );
    final serverItem = buildItem(
      id: 'server-item',
      displayName: 'Server Milk',
      quantity: 3,
      storageLocation: 'pantry',
      status: 'used',
      canonicalName: 'whole milk',
      version: 6,
    );

    final merged = ConflictResolver(baseItem: baseItem).resolve(
      serverItem,
      localItem,
      <String>{},
    );

    expect(merged.id, serverItem.id);
    expect(merged.displayName, serverItem.displayName);
    expect(merged.quantity, serverItem.quantity);
    expect(merged.storageLocation, serverItem.storageLocation);
    expect(merged.status, serverItem.status);
    expect(merged.canonicalName, serverItem.canonicalName);
    expect(merged.version, serverItem.version);
  });
}
