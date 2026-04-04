import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';

class ConflictResolver {
  ConflictResolver({required InventoryItem baseItem}) : _baseItem = baseItem;

  final InventoryItem _baseItem;

  InventoryItem resolve(
    InventoryItem serverItem,
    InventoryItem localItem,
    Set<String> dirtyFields,
  ) {
    return InventoryItem(
      id: serverItem.id,
      displayName: _resolveField<String>(
        fieldName: 'displayName',
        serverValue: serverItem.displayName,
        localValue: localItem.displayName,
        baseValue: _baseItem.displayName,
        dirtyFields: dirtyFields,
      ),
      quantity: _resolveField<double>(
        fieldName: 'quantity',
        serverValue: serverItem.quantity,
        localValue: localItem.quantity,
        baseValue: _baseItem.quantity,
        dirtyFields: dirtyFields,
      ),
      unit: _resolveField<String>(
        fieldName: 'unit',
        serverValue: serverItem.unit,
        localValue: localItem.unit,
        baseValue: _baseItem.unit,
        dirtyFields: dirtyFields,
      ),
      storageLocation: _resolveField<String>(
        fieldName: 'storageLocation',
        serverValue: serverItem.storageLocation,
        localValue: localItem.storageLocation,
        baseValue: _baseItem.storageLocation,
        dirtyFields: dirtyFields,
      ),
      estimatedExpiryDate: _resolveField<DateTime?>(
        fieldName: 'estimatedExpiryDate',
        serverValue: serverItem.estimatedExpiryDate,
        localValue: localItem.estimatedExpiryDate,
        baseValue: _baseItem.estimatedExpiryDate,
        dirtyFields: dirtyFields,
      ),
      confidence: serverItem.confidence,
      status: _resolveField<String>(
        fieldName: 'status',
        serverValue: serverItem.status,
        localValue: localItem.status,
        baseValue: _baseItem.status,
        dirtyFields: dirtyFields,
      ),
      source: serverItem.source,
      canonicalName: _resolveField<String?>(
        fieldName: 'canonicalName',
        serverValue: serverItem.canonicalName,
        localValue: localItem.canonicalName,
        baseValue: _baseItem.canonicalName,
        dirtyFields: dirtyFields,
      ),
      canonicalIngredientId: serverItem.canonicalIngredientId,
      version: serverItem.version,
    );
  }

  T _resolveField<T>({
    required String fieldName,
    required T serverValue,
    required T localValue,
    required T baseValue,
    required Set<String> dirtyFields,
  }) {
    if (!dirtyFields.contains(fieldName)) {
      return serverValue;
    }

    return _isEqual(serverValue, baseValue) ? localValue : serverValue;
  }

  bool _isEqual(Object? left, Object? right) {
    if (left is DateTime? && right is DateTime?) {
      if (left == null || right == null) {
        return left == right;
      }

      return left.isAtSameMomentAs(right);
    }

    return left == right;
  }
}
