class InventoryItem {
  const InventoryItem({
    required this.id,
    required this.displayName,
    required this.quantity,
    required this.unit,
    required this.storageLocation,
    required this.status,
    required this.source,
    this.estimatedExpiryDate,
    this.confidence,
    this.canonicalName,
    this.canonicalIngredientId,
  });

  final String id;
  final String displayName;
  final double quantity;
  final String unit;
  final String storageLocation;
  final DateTime? estimatedExpiryDate;
  final double? confidence;
  final String status;
  final String source;
  final String? canonicalName;
  final String? canonicalIngredientId;

  String get urgencyBucket {
    if (estimatedExpiryDate == null) return 'safe_later';
    final daysLeft = estimatedExpiryDate!.difference(DateTime.now()).inDays;
    if (daysLeft < 0) return 'expired';
    if (daysLeft <= 1) return 'today';
    if (daysLeft <= 7) return 'this_week';
    return 'safe_later';
  }

  InventoryItem copyWith({
    String? id,
    String? displayName,
    double? quantity,
    String? unit,
    String? storageLocation,
    DateTime? estimatedExpiryDate,
    double? confidence,
    String? status,
    String? source,
    String? canonicalName,
    String? canonicalIngredientId,
  }) {
    return InventoryItem(
      id: id ?? this.id,
      displayName: displayName ?? this.displayName,
      quantity: quantity ?? this.quantity,
      unit: unit ?? this.unit,
      storageLocation: storageLocation ?? this.storageLocation,
      estimatedExpiryDate: estimatedExpiryDate ?? this.estimatedExpiryDate,
      confidence: confidence ?? this.confidence,
      status: status ?? this.status,
      source: source ?? this.source,
      canonicalName: canonicalName ?? this.canonicalName,
      canonicalIngredientId: canonicalIngredientId ?? this.canonicalIngredientId,
    );
  }

  factory InventoryItem.fromJson(Map<String, dynamic> json) {
    final rawExpiry = json['estimatedExpiryDate'] ?? json['estimated_expiry_date'];
    final rawConfidence = json['confidence'];

    return InventoryItem(
      id: (json['itemId'] ?? json['item_id'] ?? json['id'] ?? '').toString(),
      displayName: (json['displayName'] ?? json['display_name'] ?? '').toString(),
      quantity: _asDouble(json['quantity']),
      unit: (json['unit'] ?? '').toString(),
      storageLocation: (json['storageLocation'] ?? json['storage_location'] ?? '').toString(),
      estimatedExpiryDate: rawExpiry != null
          ? DateTime.tryParse(rawExpiry.toString())
          : null,
      confidence: rawConfidence != null ? _asDouble(rawConfidence) : null,
      status: (json['status'] ?? 'active').toString(),
      source: (json['source'] ?? 'manual').toString(),
      canonicalName:
          (json['canonicalName'] ?? json['canonical_name'])?.toString(),
      canonicalIngredientId:
          (json['canonicalIngredientId'] ?? json['canonical_ingredient_id'])
              ?.toString(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'itemId': id,
      'displayName': displayName,
      'quantity': quantity,
      'unit': unit,
      'storageLocation': storageLocation,
      if (estimatedExpiryDate != null)
        'estimatedExpiryDate': estimatedExpiryDate!.toIso8601String(),
      if (confidence != null) 'confidence': confidence,
      'status': status,
      'source': source,
      'canonicalName': canonicalName,
      'canonicalIngredientId': canonicalIngredientId,
    };
  }

  static double _asDouble(Object? value) {
    if (value is num) {
      return value.toDouble();
    }

    return double.tryParse(value?.toString() ?? '') ?? 0;
  }
}
