// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'app_database.dart';

// ignore_for_file: type=lint
class $InventoryItemsTableTable extends InventoryItemsTable
    with TableInfo<$InventoryItemsTableTable, InventoryItemsTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $InventoryItemsTableTable(this.attachedDatabase, [this._alias]);

  static const VerificationMeta _idMeta = VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );

  static const VerificationMeta _displayNameMeta =
      VerificationMeta('displayName');
  @override
  late final GeneratedColumn<String> displayName = GeneratedColumn<String>(
    'display_name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );

  static const VerificationMeta _quantityMeta = VerificationMeta('quantity');
  @override
  late final GeneratedColumn<double> quantity = GeneratedColumn<double>(
    'quantity',
    aliasedName,
    false,
    type: DriftSqlType.double,
    requiredDuringInsert: true,
  );

  static const VerificationMeta _unitMeta = VerificationMeta('unit');
  @override
  late final GeneratedColumn<String> unit = GeneratedColumn<String>(
    'unit',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );

  static const VerificationMeta _storageLocationMeta =
      VerificationMeta('storageLocation');
  @override
  late final GeneratedColumn<String> storageLocation = GeneratedColumn<String>(
    'storage_location',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );

  static const VerificationMeta _estimatedExpiryDateMeta =
      VerificationMeta('estimatedExpiryDate');
  @override
  late final GeneratedColumn<DateTime> estimatedExpiryDate =
      GeneratedColumn<DateTime>(
        'estimated_expiry_date',
        aliasedName,
        false,
        type: DriftSqlType.dateTime,
        requiredDuringInsert: true,
      );

  static const VerificationMeta _confidenceMeta = VerificationMeta('confidence');
  @override
  late final GeneratedColumn<double> confidence = GeneratedColumn<double>(
    'confidence',
    aliasedName,
    false,
    type: DriftSqlType.double,
    requiredDuringInsert: true,
  );

  static const VerificationMeta _statusMeta = VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
    'status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('active'),
  );

  static const VerificationMeta _sourceMeta = VerificationMeta('source');
  @override
  late final GeneratedColumn<String> source = GeneratedColumn<String>(
    'source',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('manual'),
  );

  @override
  List<GeneratedColumn> get $columns => [
    id,
    displayName,
    quantity,
    unit,
    storageLocation,
    estimatedExpiryDate,
    confidence,
    status,
    source,
  ];

  @override
  String get aliasedName => _alias ?? actualTableName;

  @override
  String get actualTableName => $name;

  static const String $name = 'inventory_items_table';

  @override
  VerificationContext validateIntegrity(
    Insertable<InventoryItemsTableData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('display_name')) {
      context.handle(
        _displayNameMeta,
        displayName.isAcceptableOrUnknown(
          data['display_name']!,
          _displayNameMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_displayNameMeta);
    }
    if (data.containsKey('quantity')) {
      context.handle(
        _quantityMeta,
        quantity.isAcceptableOrUnknown(data['quantity']!, _quantityMeta),
      );
    } else if (isInserting) {
      context.missing(_quantityMeta);
    }
    if (data.containsKey('unit')) {
      context.handle(
        _unitMeta,
        unit.isAcceptableOrUnknown(data['unit']!, _unitMeta),
      );
    } else if (isInserting) {
      context.missing(_unitMeta);
    }
    if (data.containsKey('storage_location')) {
      context.handle(
        _storageLocationMeta,
        storageLocation.isAcceptableOrUnknown(
          data['storage_location']!,
          _storageLocationMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_storageLocationMeta);
    }
    if (data.containsKey('estimated_expiry_date')) {
      context.handle(
        _estimatedExpiryDateMeta,
        estimatedExpiryDate.isAcceptableOrUnknown(
          data['estimated_expiry_date']!,
          _estimatedExpiryDateMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_estimatedExpiryDateMeta);
    }
    if (data.containsKey('confidence')) {
      context.handle(
        _confidenceMeta,
        confidence.isAcceptableOrUnknown(
          data['confidence']!,
          _confidenceMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_confidenceMeta);
    }
    if (data.containsKey('status')) {
      context.handle(
        _statusMeta,
        status.isAcceptableOrUnknown(data['status']!, _statusMeta),
      );
    }
    if (data.containsKey('source')) {
      context.handle(
        _sourceMeta,
        source.isAcceptableOrUnknown(data['source']!, _sourceMeta),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};

  @override
  InventoryItemsTableData map(
    Map<String, dynamic> data, {
    String? tablePrefix,
  }) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return InventoryItemsTableData(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}id'],
      )!,
      displayName: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}display_name'],
      )!,
      quantity: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}quantity'],
      )!,
      unit: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}unit'],
      )!,
      storageLocation: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}storage_location'],
      )!,
      estimatedExpiryDate: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}estimated_expiry_date'],
      )!,
      confidence: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}confidence'],
      )!,
      status: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}status'],
      )!,
      source: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}source'],
      )!,
    );
  }

  @override
  $InventoryItemsTableTable createAlias(String alias) {
    return $InventoryItemsTableTable(attachedDatabase, alias);
  }
}

class InventoryItemsTableData extends DataClass
    implements Insertable<InventoryItemsTableData> {
  final String id;
  final String displayName;
  final double quantity;
  final String unit;
  final String storageLocation;
  final DateTime estimatedExpiryDate;
  final double confidence;
  final String status;
  final String source;

  const InventoryItemsTableData({
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

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    return <String, Expression>{
      'id': Variable<String>(id),
      'display_name': Variable<String>(displayName),
      'quantity': Variable<double>(quantity),
      'unit': Variable<String>(unit),
      'storage_location': Variable<String>(storageLocation),
      'estimated_expiry_date': Variable<DateTime>(estimatedExpiryDate),
      'confidence': Variable<double>(confidence),
      'status': Variable<String>(status),
      'source': Variable<String>(source),
    };
  }

  InventoryItemsTableCompanion toCompanion(bool nullToAbsent) {
    return InventoryItemsTableCompanion(
      id: Value(id),
      displayName: Value(displayName),
      quantity: Value(quantity),
      unit: Value(unit),
      storageLocation: Value(storageLocation),
      estimatedExpiryDate: Value(estimatedExpiryDate),
      confidence: Value(confidence),
      status: Value(status),
      source: Value(source),
    );
  }

  factory InventoryItemsTableData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return InventoryItemsTableData(
      id: serializer.fromJson<String>(json['id']),
      displayName: serializer.fromJson<String>(json['displayName']),
      quantity: serializer.fromJson<double>(json['quantity']),
      unit: serializer.fromJson<String>(json['unit']),
      storageLocation: serializer.fromJson<String>(json['storageLocation']),
      estimatedExpiryDate: serializer.fromJson<DateTime>(
        json['estimatedExpiryDate'],
      ),
      confidence: serializer.fromJson<double>(json['confidence']),
      status: serializer.fromJson<String>(json['status']),
      source: serializer.fromJson<String>(json['source']),
    );
  }

  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'displayName': serializer.toJson<String>(displayName),
      'quantity': serializer.toJson<double>(quantity),
      'unit': serializer.toJson<String>(unit),
      'storageLocation': serializer.toJson<String>(storageLocation),
      'estimatedExpiryDate': serializer.toJson<DateTime>(estimatedExpiryDate),
      'confidence': serializer.toJson<double>(confidence),
      'status': serializer.toJson<String>(status),
      'source': serializer.toJson<String>(source),
    };
  }

  InventoryItemsTableData copyWith({
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
    return InventoryItemsTableData(
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

  @override
  String toString() {
    return (StringBuffer('InventoryItemsTableData(')
          ..write('id: $id, ')
          ..write('displayName: $displayName, ')
          ..write('quantity: $quantity, ')
          ..write('unit: $unit, ')
          ..write('storageLocation: $storageLocation, ')
          ..write('estimatedExpiryDate: $estimatedExpiryDate, ')
          ..write('confidence: $confidence, ')
          ..write('status: $status, ')
          ..write('source: $source')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    displayName,
    quantity,
    unit,
    storageLocation,
    estimatedExpiryDate,
    confidence,
    status,
    source,
  );

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is InventoryItemsTableData &&
          other.id == id &&
          other.displayName == displayName &&
          other.quantity == quantity &&
          other.unit == unit &&
          other.storageLocation == storageLocation &&
          other.estimatedExpiryDate == estimatedExpiryDate &&
          other.confidence == confidence &&
          other.status == status &&
          other.source == source);
}

class InventoryItemsTableCompanion
    extends UpdateCompanion<InventoryItemsTableData> {
  final Value<String> id;
  final Value<String> displayName;
  final Value<double> quantity;
  final Value<String> unit;
  final Value<String> storageLocation;
  final Value<DateTime> estimatedExpiryDate;
  final Value<double> confidence;
  final Value<String> status;
  final Value<String> source;

  const InventoryItemsTableCompanion({
    this.id = const Value.absent(),
    this.displayName = const Value.absent(),
    this.quantity = const Value.absent(),
    this.unit = const Value.absent(),
    this.storageLocation = const Value.absent(),
    this.estimatedExpiryDate = const Value.absent(),
    this.confidence = const Value.absent(),
    this.status = const Value.absent(),
    this.source = const Value.absent(),
  });

  InventoryItemsTableCompanion.insert({
    required String id,
    required String displayName,
    required double quantity,
    required String unit,
    required String storageLocation,
    required DateTime estimatedExpiryDate,
    required double confidence,
    this.status = const Value.absent(),
    this.source = const Value.absent(),
  })  : id = Value(id),
        displayName = Value(displayName),
        quantity = Value(quantity),
        unit = Value(unit),
        storageLocation = Value(storageLocation),
        estimatedExpiryDate = Value(estimatedExpiryDate),
        confidence = Value(confidence);

  static Insertable<InventoryItemsTableData> custom({
    Expression<String>? id,
    Expression<String>? displayName,
    Expression<double>? quantity,
    Expression<String>? unit,
    Expression<String>? storageLocation,
    Expression<DateTime>? estimatedExpiryDate,
    Expression<double>? confidence,
    Expression<String>? status,
    Expression<String>? source,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (displayName != null) 'display_name': displayName,
      if (quantity != null) 'quantity': quantity,
      if (unit != null) 'unit': unit,
      if (storageLocation != null) 'storage_location': storageLocation,
      if (estimatedExpiryDate != null)
        'estimated_expiry_date': estimatedExpiryDate,
      if (confidence != null) 'confidence': confidence,
      if (status != null) 'status': status,
      if (source != null) 'source': source,
    });
  }

  InventoryItemsTableCompanion copyWith({
    Value<String>? id,
    Value<String>? displayName,
    Value<double>? quantity,
    Value<String>? unit,
    Value<String>? storageLocation,
    Value<DateTime>? estimatedExpiryDate,
    Value<double>? confidence,
    Value<String>? status,
    Value<String>? source,
  }) {
    return InventoryItemsTableCompanion(
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

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (displayName.present) {
      map['display_name'] = Variable<String>(displayName.value);
    }
    if (quantity.present) {
      map['quantity'] = Variable<double>(quantity.value);
    }
    if (unit.present) {
      map['unit'] = Variable<String>(unit.value);
    }
    if (storageLocation.present) {
      map['storage_location'] = Variable<String>(storageLocation.value);
    }
    if (estimatedExpiryDate.present) {
      map['estimated_expiry_date'] =
          Variable<DateTime>(estimatedExpiryDate.value);
    }
    if (confidence.present) {
      map['confidence'] = Variable<double>(confidence.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (source.present) {
      map['source'] = Variable<String>(source.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('InventoryItemsTableCompanion(')
          ..write('id: $id, ')
          ..write('displayName: $displayName, ')
          ..write('quantity: $quantity, ')
          ..write('unit: $unit, ')
          ..write('storageLocation: $storageLocation, ')
          ..write('estimatedExpiryDate: $estimatedExpiryDate, ')
          ..write('confidence: $confidence, ')
          ..write('status: $status, ')
          ..write('source: $source')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);

  late final $InventoryItemsTableTable inventoryItemsTable =
      $InventoryItemsTableTable(this);
  late final InventoryDao inventoryDao = InventoryDao(this);

  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();

  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [inventoryItemsTable];
}
