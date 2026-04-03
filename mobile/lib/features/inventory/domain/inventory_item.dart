class InventoryItem {
  const InventoryItem({
    required this.id,
    required this.displayName,
    required this.quantity,
    required this.unit,
    required this.storageLocation,
    required this.estimatedExpiryDate,
    required this.confidence,
    required this.status,
    required this.source,
  });

  final String id;
  final String displayName;
  final double quantity;
  final String unit;
  final String storageLocation;
  final DateTime estimatedExpiryDate;
  final double confidence;
  final String status;
  final String source;

  String get urgencyBucket {
    final daysLeft = estimatedExpiryDate.difference(DateTime.now()).inDays;
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
    );
  }

  factory InventoryItem.fromJson(Map<String, dynamic> json) {
    return InventoryItem(
      id: (json['itemId'] ?? json['id'] ?? '').toString(),
      displayName: (json['displayName'] ?? '').toString(),
      quantity: _asDouble(json['quantity']),
      unit: (json['unit'] ?? '').toString(),
      storageLocation: (json['storageLocation'] ?? '').toString(),
      estimatedExpiryDate: DateTime.tryParse(
            (json['estimatedExpiryDate'] ?? '').toString(),
          ) ??
          DateTime.now(),
      confidence: _asDouble(json['confidence']),
      status: (json['status'] ?? 'active').toString(),
      source: (json['source'] ?? 'manual').toString(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'itemId': id,
      'displayName': displayName,
      'quantity': quantity,
      'unit': unit,
      'storageLocation': storageLocation,
      'estimatedExpiryDate': estimatedExpiryDate.toIso8601String(),
      'confidence': confidence,
      'status': status,
      'source': source,
    };
  }

  static double _asDouble(Object? value) {
    if (value is num) {
      return value.toDouble();
    }

    return double.tryParse(value?.toString() ?? '') ?? 0;
  }
}
