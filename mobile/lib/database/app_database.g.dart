// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'app_database.dart';

// ignore_for_file: type=lint
class $InventoryItemsTableTable extends InventoryItemsTable
    with TableInfo<$InventoryItemsTableTable, InventoryItemsTableData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $InventoryItemsTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _displayNameMeta =
      const VerificationMeta('displayName');
  @override
  late final GeneratedColumn<String> displayName = GeneratedColumn<String>(
      'display_name', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _quantityMeta =
      const VerificationMeta('quantity');
  @override
  late final GeneratedColumn<double> quantity = GeneratedColumn<double>(
      'quantity', aliasedName, false,
      type: DriftSqlType.double, requiredDuringInsert: true);
  static const VerificationMeta _unitMeta = const VerificationMeta('unit');
  @override
  late final GeneratedColumn<String> unit = GeneratedColumn<String>(
      'unit', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _storageLocationMeta =
      const VerificationMeta('storageLocation');
  @override
  late final GeneratedColumn<String> storageLocation = GeneratedColumn<String>(
      'storage_location', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _canonicalNameMeta =
      const VerificationMeta('canonicalName');
  @override
  late final GeneratedColumn<String> canonicalName = GeneratedColumn<String>(
      'canonical_name', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _canonicalIngredientIdMeta =
      const VerificationMeta('canonicalIngredientId');
  @override
  late final GeneratedColumn<String> canonicalIngredientId =
      GeneratedColumn<String>('canonical_ingredient_id', aliasedName, true,
          type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _estimatedExpiryDateMeta =
      const VerificationMeta('estimatedExpiryDate');
  @override
  late final GeneratedColumn<DateTime> estimatedExpiryDate =
      GeneratedColumn<DateTime>('estimated_expiry_date', aliasedName, false,
          type: DriftSqlType.dateTime, requiredDuringInsert: true);
  static const VerificationMeta _confidenceMeta =
      const VerificationMeta('confidence');
  @override
  late final GeneratedColumn<double> confidence = GeneratedColumn<double>(
      'confidence', aliasedName, false,
      type: DriftSqlType.double, requiredDuringInsert: true);
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
      'status', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant('active'));
  static const VerificationMeta _sourceMeta = const VerificationMeta('source');
  @override
  late final GeneratedColumn<String> source = GeneratedColumn<String>(
      'source', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant('manual'));
  static const VerificationMeta _versionMeta =
      const VerificationMeta('version');
  @override
  late final GeneratedColumn<int> version = GeneratedColumn<int>(
      'version', aliasedName, false,
      type: DriftSqlType.int,
      requiredDuringInsert: false,
      defaultValue: const Constant(1));
  @override
  List<GeneratedColumn> get $columns => [
        id,
        displayName,
        quantity,
        unit,
        storageLocation,
        canonicalName,
        canonicalIngredientId,
        estimatedExpiryDate,
        confidence,
        status,
        source,
        version
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'inventory_items_table';
  @override
  VerificationContext validateIntegrity(
      Insertable<InventoryItemsTableData> instance,
      {bool isInserting = false}) {
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
              data['display_name']!, _displayNameMeta));
    } else if (isInserting) {
      context.missing(_displayNameMeta);
    }
    if (data.containsKey('quantity')) {
      context.handle(_quantityMeta,
          quantity.isAcceptableOrUnknown(data['quantity']!, _quantityMeta));
    } else if (isInserting) {
      context.missing(_quantityMeta);
    }
    if (data.containsKey('unit')) {
      context.handle(
          _unitMeta, unit.isAcceptableOrUnknown(data['unit']!, _unitMeta));
    } else if (isInserting) {
      context.missing(_unitMeta);
    }
    if (data.containsKey('storage_location')) {
      context.handle(
          _storageLocationMeta,
          storageLocation.isAcceptableOrUnknown(
              data['storage_location']!, _storageLocationMeta));
    } else if (isInserting) {
      context.missing(_storageLocationMeta);
    }
    if (data.containsKey('canonical_name')) {
      context.handle(
          _canonicalNameMeta,
          canonicalName.isAcceptableOrUnknown(
              data['canonical_name']!, _canonicalNameMeta));
    }
    if (data.containsKey('canonical_ingredient_id')) {
      context.handle(
          _canonicalIngredientIdMeta,
          canonicalIngredientId.isAcceptableOrUnknown(
              data['canonical_ingredient_id']!, _canonicalIngredientIdMeta));
    }
    if (data.containsKey('estimated_expiry_date')) {
      context.handle(
          _estimatedExpiryDateMeta,
          estimatedExpiryDate.isAcceptableOrUnknown(
              data['estimated_expiry_date']!, _estimatedExpiryDateMeta));
    } else if (isInserting) {
      context.missing(_estimatedExpiryDateMeta);
    }
    if (data.containsKey('confidence')) {
      context.handle(
          _confidenceMeta,
          confidence.isAcceptableOrUnknown(
              data['confidence']!, _confidenceMeta));
    } else if (isInserting) {
      context.missing(_confidenceMeta);
    }
    if (data.containsKey('status')) {
      context.handle(_statusMeta,
          status.isAcceptableOrUnknown(data['status']!, _statusMeta));
    }
    if (data.containsKey('source')) {
      context.handle(_sourceMeta,
          source.isAcceptableOrUnknown(data['source']!, _sourceMeta));
    }
    if (data.containsKey('version')) {
      context.handle(_versionMeta,
          version.isAcceptableOrUnknown(data['version']!, _versionMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  InventoryItemsTableData map(Map<String, dynamic> data,
      {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return InventoryItemsTableData(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      displayName: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}display_name'])!,
      quantity: attachedDatabase.typeMapping
          .read(DriftSqlType.double, data['${effectivePrefix}quantity'])!,
      unit: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}unit'])!,
      storageLocation: attachedDatabase.typeMapping.read(
          DriftSqlType.string, data['${effectivePrefix}storage_location'])!,
      canonicalName: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}canonical_name']),
      canonicalIngredientId: attachedDatabase.typeMapping.read(
          DriftSqlType.string,
          data['${effectivePrefix}canonical_ingredient_id']),
      estimatedExpiryDate: attachedDatabase.typeMapping.read(
          DriftSqlType.dateTime,
          data['${effectivePrefix}estimated_expiry_date'])!,
      confidence: attachedDatabase.typeMapping
          .read(DriftSqlType.double, data['${effectivePrefix}confidence'])!,
      status: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}status'])!,
      source: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}source'])!,
      version: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}version'])!,
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
  final String? canonicalName;
  final String? canonicalIngredientId;
  final DateTime estimatedExpiryDate;
  final double confidence;
  final String status;
  final String source;
  final int version;
  const InventoryItemsTableData(
      {required this.id,
      required this.displayName,
      required this.quantity,
      required this.unit,
      required this.storageLocation,
      this.canonicalName,
      this.canonicalIngredientId,
      required this.estimatedExpiryDate,
      required this.confidence,
      required this.status,
      required this.source,
      required this.version});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['display_name'] = Variable<String>(displayName);
    map['quantity'] = Variable<double>(quantity);
    map['unit'] = Variable<String>(unit);
    map['storage_location'] = Variable<String>(storageLocation);
    if (!nullToAbsent || canonicalName != null) {
      map['canonical_name'] = Variable<String>(canonicalName);
    }
    if (!nullToAbsent || canonicalIngredientId != null) {
      map['canonical_ingredient_id'] = Variable<String>(canonicalIngredientId);
    }
    map['estimated_expiry_date'] = Variable<DateTime>(estimatedExpiryDate);
    map['confidence'] = Variable<double>(confidence);
    map['status'] = Variable<String>(status);
    map['source'] = Variable<String>(source);
    map['version'] = Variable<int>(version);
    return map;
  }

  InventoryItemsTableCompanion toCompanion(bool nullToAbsent) {
    return InventoryItemsTableCompanion(
      id: Value(id),
      displayName: Value(displayName),
      quantity: Value(quantity),
      unit: Value(unit),
      storageLocation: Value(storageLocation),
      canonicalName: canonicalName == null && nullToAbsent
          ? const Value.absent()
          : Value(canonicalName),
      canonicalIngredientId: canonicalIngredientId == null && nullToAbsent
          ? const Value.absent()
          : Value(canonicalIngredientId),
      estimatedExpiryDate: Value(estimatedExpiryDate),
      confidence: Value(confidence),
      status: Value(status),
      source: Value(source),
      version: Value(version),
    );
  }

  factory InventoryItemsTableData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return InventoryItemsTableData(
      id: serializer.fromJson<String>(json['id']),
      displayName: serializer.fromJson<String>(json['displayName']),
      quantity: serializer.fromJson<double>(json['quantity']),
      unit: serializer.fromJson<String>(json['unit']),
      storageLocation: serializer.fromJson<String>(json['storageLocation']),
      canonicalName: serializer.fromJson<String?>(json['canonicalName']),
      canonicalIngredientId:
          serializer.fromJson<String?>(json['canonicalIngredientId']),
      estimatedExpiryDate:
          serializer.fromJson<DateTime>(json['estimatedExpiryDate']),
      confidence: serializer.fromJson<double>(json['confidence']),
      status: serializer.fromJson<String>(json['status']),
      source: serializer.fromJson<String>(json['source']),
      version: serializer.fromJson<int>(json['version']),
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
      'canonicalName': serializer.toJson<String?>(canonicalName),
      'canonicalIngredientId':
          serializer.toJson<String?>(canonicalIngredientId),
      'estimatedExpiryDate': serializer.toJson<DateTime>(estimatedExpiryDate),
      'confidence': serializer.toJson<double>(confidence),
      'status': serializer.toJson<String>(status),
      'source': serializer.toJson<String>(source),
      'version': serializer.toJson<int>(version),
    };
  }

  InventoryItemsTableData copyWith(
          {String? id,
          String? displayName,
          double? quantity,
          String? unit,
          String? storageLocation,
          Value<String?> canonicalName = const Value.absent(),
          Value<String?> canonicalIngredientId = const Value.absent(),
          DateTime? estimatedExpiryDate,
          double? confidence,
          String? status,
          String? source,
          int? version}) =>
      InventoryItemsTableData(
        id: id ?? this.id,
        displayName: displayName ?? this.displayName,
        quantity: quantity ?? this.quantity,
        unit: unit ?? this.unit,
        storageLocation: storageLocation ?? this.storageLocation,
        canonicalName:
            canonicalName.present ? canonicalName.value : this.canonicalName,
        canonicalIngredientId: canonicalIngredientId.present
            ? canonicalIngredientId.value
            : this.canonicalIngredientId,
        estimatedExpiryDate: estimatedExpiryDate ?? this.estimatedExpiryDate,
        confidence: confidence ?? this.confidence,
        status: status ?? this.status,
        source: source ?? this.source,
        version: version ?? this.version,
      );
  InventoryItemsTableData copyWithCompanion(InventoryItemsTableCompanion data) {
    return InventoryItemsTableData(
      id: data.id.present ? data.id.value : this.id,
      displayName:
          data.displayName.present ? data.displayName.value : this.displayName,
      quantity: data.quantity.present ? data.quantity.value : this.quantity,
      unit: data.unit.present ? data.unit.value : this.unit,
      storageLocation: data.storageLocation.present
          ? data.storageLocation.value
          : this.storageLocation,
      canonicalName: data.canonicalName.present
          ? data.canonicalName.value
          : this.canonicalName,
      canonicalIngredientId: data.canonicalIngredientId.present
          ? data.canonicalIngredientId.value
          : this.canonicalIngredientId,
      estimatedExpiryDate: data.estimatedExpiryDate.present
          ? data.estimatedExpiryDate.value
          : this.estimatedExpiryDate,
      confidence:
          data.confidence.present ? data.confidence.value : this.confidence,
      status: data.status.present ? data.status.value : this.status,
      source: data.source.present ? data.source.value : this.source,
      version: data.version.present ? data.version.value : this.version,
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
          ..write('canonicalName: $canonicalName, ')
          ..write('canonicalIngredientId: $canonicalIngredientId, ')
          ..write('estimatedExpiryDate: $estimatedExpiryDate, ')
          ..write('confidence: $confidence, ')
          ..write('status: $status, ')
          ..write('source: $source, ')
          ..write('version: $version')
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
      canonicalName,
      canonicalIngredientId,
      estimatedExpiryDate,
      confidence,
      status,
      source,
      version);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is InventoryItemsTableData &&
          other.id == this.id &&
          other.displayName == this.displayName &&
          other.quantity == this.quantity &&
          other.unit == this.unit &&
          other.storageLocation == this.storageLocation &&
          other.canonicalName == this.canonicalName &&
          other.canonicalIngredientId == this.canonicalIngredientId &&
          other.estimatedExpiryDate == this.estimatedExpiryDate &&
          other.confidence == this.confidence &&
          other.status == this.status &&
          other.source == this.source &&
          other.version == this.version);
}

class InventoryItemsTableCompanion
    extends UpdateCompanion<InventoryItemsTableData> {
  final Value<String> id;
  final Value<String> displayName;
  final Value<double> quantity;
  final Value<String> unit;
  final Value<String> storageLocation;
  final Value<String?> canonicalName;
  final Value<String?> canonicalIngredientId;
  final Value<DateTime> estimatedExpiryDate;
  final Value<double> confidence;
  final Value<String> status;
  final Value<String> source;
  final Value<int> version;
  final Value<int> rowid;
  const InventoryItemsTableCompanion({
    this.id = const Value.absent(),
    this.displayName = const Value.absent(),
    this.quantity = const Value.absent(),
    this.unit = const Value.absent(),
    this.storageLocation = const Value.absent(),
    this.canonicalName = const Value.absent(),
    this.canonicalIngredientId = const Value.absent(),
    this.estimatedExpiryDate = const Value.absent(),
    this.confidence = const Value.absent(),
    this.status = const Value.absent(),
    this.source = const Value.absent(),
    this.version = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  InventoryItemsTableCompanion.insert({
    required String id,
    required String displayName,
    required double quantity,
    required String unit,
    required String storageLocation,
    this.canonicalName = const Value.absent(),
    this.canonicalIngredientId = const Value.absent(),
    required DateTime estimatedExpiryDate,
    required double confidence,
    this.status = const Value.absent(),
    this.source = const Value.absent(),
    this.version = const Value.absent(),
    this.rowid = const Value.absent(),
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
    Expression<String>? canonicalName,
    Expression<String>? canonicalIngredientId,
    Expression<DateTime>? estimatedExpiryDate,
    Expression<double>? confidence,
    Expression<String>? status,
    Expression<String>? source,
    Expression<int>? version,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (displayName != null) 'display_name': displayName,
      if (quantity != null) 'quantity': quantity,
      if (unit != null) 'unit': unit,
      if (storageLocation != null) 'storage_location': storageLocation,
      if (canonicalName != null) 'canonical_name': canonicalName,
      if (canonicalIngredientId != null)
        'canonical_ingredient_id': canonicalIngredientId,
      if (estimatedExpiryDate != null)
        'estimated_expiry_date': estimatedExpiryDate,
      if (confidence != null) 'confidence': confidence,
      if (status != null) 'status': status,
      if (source != null) 'source': source,
      if (version != null) 'version': version,
      if (rowid != null) 'rowid': rowid,
    });
  }

  InventoryItemsTableCompanion copyWith(
      {Value<String>? id,
      Value<String>? displayName,
      Value<double>? quantity,
      Value<String>? unit,
      Value<String>? storageLocation,
      Value<String?>? canonicalName,
      Value<String?>? canonicalIngredientId,
      Value<DateTime>? estimatedExpiryDate,
      Value<double>? confidence,
      Value<String>? status,
      Value<String>? source,
      Value<int>? version,
      Value<int>? rowid}) {
    return InventoryItemsTableCompanion(
      id: id ?? this.id,
      displayName: displayName ?? this.displayName,
      quantity: quantity ?? this.quantity,
      unit: unit ?? this.unit,
      storageLocation: storageLocation ?? this.storageLocation,
      canonicalName: canonicalName ?? this.canonicalName,
      canonicalIngredientId:
          canonicalIngredientId ?? this.canonicalIngredientId,
      estimatedExpiryDate: estimatedExpiryDate ?? this.estimatedExpiryDate,
      confidence: confidence ?? this.confidence,
      status: status ?? this.status,
      source: source ?? this.source,
      version: version ?? this.version,
      rowid: rowid ?? this.rowid,
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
    if (canonicalName.present) {
      map['canonical_name'] = Variable<String>(canonicalName.value);
    }
    if (canonicalIngredientId.present) {
      map['canonical_ingredient_id'] =
          Variable<String>(canonicalIngredientId.value);
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
    if (version.present) {
      map['version'] = Variable<int>(version.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
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
          ..write('canonicalName: $canonicalName, ')
          ..write('canonicalIngredientId: $canonicalIngredientId, ')
          ..write('estimatedExpiryDate: $estimatedExpiryDate, ')
          ..write('confidence: $confidence, ')
          ..write('status: $status, ')
          ..write('source: $source, ')
          ..write('version: $version, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $SavedRecipesTableTable extends SavedRecipesTable
    with TableInfo<$SavedRecipesTableTable, SavedRecipeRecord> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $SavedRecipesTableTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _recipeIdMeta =
      const VerificationMeta('recipeId');
  @override
  late final GeneratedColumn<String> recipeId = GeneratedColumn<String>(
      'recipe_id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _recipeTitleMeta =
      const VerificationMeta('recipeTitle');
  @override
  late final GeneratedColumn<String> recipeTitle = GeneratedColumn<String>(
      'recipe_title', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _imageUrlMeta =
      const VerificationMeta('imageUrl');
  @override
  late final GeneratedColumn<String> imageUrl = GeneratedColumn<String>(
      'image_url', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _savedAtMeta =
      const VerificationMeta('savedAt');
  @override
  late final GeneratedColumn<DateTime> savedAt = GeneratedColumn<DateTime>(
      'saved_at', aliasedName, false,
      type: DriftSqlType.dateTime,
      requiredDuringInsert: false,
      defaultValue: currentDateAndTime);
  @override
  List<GeneratedColumn> get $columns =>
      [recipeId, recipeTitle, imageUrl, savedAt];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'saved_recipes_table';
  @override
  VerificationContext validateIntegrity(Insertable<SavedRecipeRecord> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('recipe_id')) {
      context.handle(_recipeIdMeta,
          recipeId.isAcceptableOrUnknown(data['recipe_id']!, _recipeIdMeta));
    } else if (isInserting) {
      context.missing(_recipeIdMeta);
    }
    if (data.containsKey('recipe_title')) {
      context.handle(
          _recipeTitleMeta,
          recipeTitle.isAcceptableOrUnknown(
              data['recipe_title']!, _recipeTitleMeta));
    } else if (isInserting) {
      context.missing(_recipeTitleMeta);
    }
    if (data.containsKey('image_url')) {
      context.handle(_imageUrlMeta,
          imageUrl.isAcceptableOrUnknown(data['image_url']!, _imageUrlMeta));
    }
    if (data.containsKey('saved_at')) {
      context.handle(_savedAtMeta,
          savedAt.isAcceptableOrUnknown(data['saved_at']!, _savedAtMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {recipeId};
  @override
  SavedRecipeRecord map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return SavedRecipeRecord(
      recipeId: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}recipe_id'])!,
      recipeTitle: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}recipe_title'])!,
      imageUrl: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}image_url']),
      savedAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}saved_at'])!,
    );
  }

  @override
  $SavedRecipesTableTable createAlias(String alias) {
    return $SavedRecipesTableTable(attachedDatabase, alias);
  }
}

class SavedRecipeRecord extends DataClass
    implements Insertable<SavedRecipeRecord> {
  final String recipeId;
  final String recipeTitle;
  final String? imageUrl;
  final DateTime savedAt;
  const SavedRecipeRecord(
      {required this.recipeId,
      required this.recipeTitle,
      this.imageUrl,
      required this.savedAt});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['recipe_id'] = Variable<String>(recipeId);
    map['recipe_title'] = Variable<String>(recipeTitle);
    if (!nullToAbsent || imageUrl != null) {
      map['image_url'] = Variable<String>(imageUrl);
    }
    map['saved_at'] = Variable<DateTime>(savedAt);
    return map;
  }

  SavedRecipesTableCompanion toCompanion(bool nullToAbsent) {
    return SavedRecipesTableCompanion(
      recipeId: Value(recipeId),
      recipeTitle: Value(recipeTitle),
      imageUrl: imageUrl == null && nullToAbsent
          ? const Value.absent()
          : Value(imageUrl),
      savedAt: Value(savedAt),
    );
  }

  factory SavedRecipeRecord.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return SavedRecipeRecord(
      recipeId: serializer.fromJson<String>(json['recipeId']),
      recipeTitle: serializer.fromJson<String>(json['recipeTitle']),
      imageUrl: serializer.fromJson<String?>(json['imageUrl']),
      savedAt: serializer.fromJson<DateTime>(json['savedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'recipeId': serializer.toJson<String>(recipeId),
      'recipeTitle': serializer.toJson<String>(recipeTitle),
      'imageUrl': serializer.toJson<String?>(imageUrl),
      'savedAt': serializer.toJson<DateTime>(savedAt),
    };
  }

  SavedRecipeRecord copyWith(
          {String? recipeId,
          String? recipeTitle,
          Value<String?> imageUrl = const Value.absent(),
          DateTime? savedAt}) =>
      SavedRecipeRecord(
        recipeId: recipeId ?? this.recipeId,
        recipeTitle: recipeTitle ?? this.recipeTitle,
        imageUrl: imageUrl.present ? imageUrl.value : this.imageUrl,
        savedAt: savedAt ?? this.savedAt,
      );
  SavedRecipeRecord copyWithCompanion(SavedRecipesTableCompanion data) {
    return SavedRecipeRecord(
      recipeId: data.recipeId.present ? data.recipeId.value : this.recipeId,
      recipeTitle:
          data.recipeTitle.present ? data.recipeTitle.value : this.recipeTitle,
      imageUrl: data.imageUrl.present ? data.imageUrl.value : this.imageUrl,
      savedAt: data.savedAt.present ? data.savedAt.value : this.savedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('SavedRecipeRecord(')
          ..write('recipeId: $recipeId, ')
          ..write('recipeTitle: $recipeTitle, ')
          ..write('imageUrl: $imageUrl, ')
          ..write('savedAt: $savedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(recipeId, recipeTitle, imageUrl, savedAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is SavedRecipeRecord &&
          other.recipeId == this.recipeId &&
          other.recipeTitle == this.recipeTitle &&
          other.imageUrl == this.imageUrl &&
          other.savedAt == this.savedAt);
}

class SavedRecipesTableCompanion extends UpdateCompanion<SavedRecipeRecord> {
  final Value<String> recipeId;
  final Value<String> recipeTitle;
  final Value<String?> imageUrl;
  final Value<DateTime> savedAt;
  final Value<int> rowid;
  const SavedRecipesTableCompanion({
    this.recipeId = const Value.absent(),
    this.recipeTitle = const Value.absent(),
    this.imageUrl = const Value.absent(),
    this.savedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  SavedRecipesTableCompanion.insert({
    required String recipeId,
    required String recipeTitle,
    this.imageUrl = const Value.absent(),
    this.savedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : recipeId = Value(recipeId),
        recipeTitle = Value(recipeTitle);
  static Insertable<SavedRecipeRecord> custom({
    Expression<String>? recipeId,
    Expression<String>? recipeTitle,
    Expression<String>? imageUrl,
    Expression<DateTime>? savedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (recipeId != null) 'recipe_id': recipeId,
      if (recipeTitle != null) 'recipe_title': recipeTitle,
      if (imageUrl != null) 'image_url': imageUrl,
      if (savedAt != null) 'saved_at': savedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  SavedRecipesTableCompanion copyWith(
      {Value<String>? recipeId,
      Value<String>? recipeTitle,
      Value<String?>? imageUrl,
      Value<DateTime>? savedAt,
      Value<int>? rowid}) {
    return SavedRecipesTableCompanion(
      recipeId: recipeId ?? this.recipeId,
      recipeTitle: recipeTitle ?? this.recipeTitle,
      imageUrl: imageUrl ?? this.imageUrl,
      savedAt: savedAt ?? this.savedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (recipeId.present) {
      map['recipe_id'] = Variable<String>(recipeId.value);
    }
    if (recipeTitle.present) {
      map['recipe_title'] = Variable<String>(recipeTitle.value);
    }
    if (imageUrl.present) {
      map['image_url'] = Variable<String>(imageUrl.value);
    }
    if (savedAt.present) {
      map['saved_at'] = Variable<DateTime>(savedAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('SavedRecipesTableCompanion(')
          ..write('recipeId: $recipeId, ')
          ..write('recipeTitle: $recipeTitle, ')
          ..write('imageUrl: $imageUrl, ')
          ..write('savedAt: $savedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $InventoryItemsTableTable inventoryItemsTable =
      $InventoryItemsTableTable(this);
  late final $SavedRecipesTableTable savedRecipesTable =
      $SavedRecipesTableTable(this);
  late final InventoryDao inventoryDao = InventoryDao(this as AppDatabase);
  late final SavedRecipeDao savedRecipeDao =
      SavedRecipeDao(this as AppDatabase);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities =>
      [inventoryItemsTable, savedRecipesTable];
}

typedef $$InventoryItemsTableTableCreateCompanionBuilder
    = InventoryItemsTableCompanion Function({
  required String id,
  required String displayName,
  required double quantity,
  required String unit,
  required String storageLocation,
  Value<String?> canonicalName,
  Value<String?> canonicalIngredientId,
  required DateTime estimatedExpiryDate,
  required double confidence,
  Value<String> status,
  Value<String> source,
  Value<int> version,
  Value<int> rowid,
});
typedef $$InventoryItemsTableTableUpdateCompanionBuilder
    = InventoryItemsTableCompanion Function({
  Value<String> id,
  Value<String> displayName,
  Value<double> quantity,
  Value<String> unit,
  Value<String> storageLocation,
  Value<String?> canonicalName,
  Value<String?> canonicalIngredientId,
  Value<DateTime> estimatedExpiryDate,
  Value<double> confidence,
  Value<String> status,
  Value<String> source,
  Value<int> version,
  Value<int> rowid,
});

class $$InventoryItemsTableTableFilterComposer
    extends Composer<_$AppDatabase, $InventoryItemsTableTable> {
  $$InventoryItemsTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get displayName => $composableBuilder(
      column: $table.displayName, builder: (column) => ColumnFilters(column));

  ColumnFilters<double> get quantity => $composableBuilder(
      column: $table.quantity, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get unit => $composableBuilder(
      column: $table.unit, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get storageLocation => $composableBuilder(
      column: $table.storageLocation,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get canonicalName => $composableBuilder(
      column: $table.canonicalName, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get canonicalIngredientId => $composableBuilder(
      column: $table.canonicalIngredientId,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get estimatedExpiryDate => $composableBuilder(
      column: $table.estimatedExpiryDate,
      builder: (column) => ColumnFilters(column));

  ColumnFilters<double> get confidence => $composableBuilder(
      column: $table.confidence, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get status => $composableBuilder(
      column: $table.status, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get source => $composableBuilder(
      column: $table.source, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get version => $composableBuilder(
      column: $table.version, builder: (column) => ColumnFilters(column));
}

class $$InventoryItemsTableTableOrderingComposer
    extends Composer<_$AppDatabase, $InventoryItemsTableTable> {
  $$InventoryItemsTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get displayName => $composableBuilder(
      column: $table.displayName, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<double> get quantity => $composableBuilder(
      column: $table.quantity, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get unit => $composableBuilder(
      column: $table.unit, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get storageLocation => $composableBuilder(
      column: $table.storageLocation,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get canonicalName => $composableBuilder(
      column: $table.canonicalName,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get canonicalIngredientId => $composableBuilder(
      column: $table.canonicalIngredientId,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get estimatedExpiryDate => $composableBuilder(
      column: $table.estimatedExpiryDate,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<double> get confidence => $composableBuilder(
      column: $table.confidence, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get status => $composableBuilder(
      column: $table.status, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get source => $composableBuilder(
      column: $table.source, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get version => $composableBuilder(
      column: $table.version, builder: (column) => ColumnOrderings(column));
}

class $$InventoryItemsTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $InventoryItemsTableTable> {
  $$InventoryItemsTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get displayName => $composableBuilder(
      column: $table.displayName, builder: (column) => column);

  GeneratedColumn<double> get quantity =>
      $composableBuilder(column: $table.quantity, builder: (column) => column);

  GeneratedColumn<String> get unit =>
      $composableBuilder(column: $table.unit, builder: (column) => column);

  GeneratedColumn<String> get storageLocation => $composableBuilder(
      column: $table.storageLocation, builder: (column) => column);

  GeneratedColumn<String> get canonicalName => $composableBuilder(
      column: $table.canonicalName, builder: (column) => column);

  GeneratedColumn<String> get canonicalIngredientId => $composableBuilder(
      column: $table.canonicalIngredientId, builder: (column) => column);

  GeneratedColumn<DateTime> get estimatedExpiryDate => $composableBuilder(
      column: $table.estimatedExpiryDate, builder: (column) => column);

  GeneratedColumn<double> get confidence => $composableBuilder(
      column: $table.confidence, builder: (column) => column);

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<String> get source =>
      $composableBuilder(column: $table.source, builder: (column) => column);

  GeneratedColumn<int> get version =>
      $composableBuilder(column: $table.version, builder: (column) => column);
}

class $$InventoryItemsTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $InventoryItemsTableTable,
    InventoryItemsTableData,
    $$InventoryItemsTableTableFilterComposer,
    $$InventoryItemsTableTableOrderingComposer,
    $$InventoryItemsTableTableAnnotationComposer,
    $$InventoryItemsTableTableCreateCompanionBuilder,
    $$InventoryItemsTableTableUpdateCompanionBuilder,
    (
      InventoryItemsTableData,
      BaseReferences<_$AppDatabase, $InventoryItemsTableTable,
          InventoryItemsTableData>
    ),
    InventoryItemsTableData,
    PrefetchHooks Function()> {
  $$InventoryItemsTableTableTableManager(
      _$AppDatabase db, $InventoryItemsTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$InventoryItemsTableTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$InventoryItemsTableTableOrderingComposer(
                  $db: db, $table: table),
          createComputedFieldComposer: () =>
              $$InventoryItemsTableTableAnnotationComposer(
                  $db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> id = const Value.absent(),
            Value<String> displayName = const Value.absent(),
            Value<double> quantity = const Value.absent(),
            Value<String> unit = const Value.absent(),
            Value<String> storageLocation = const Value.absent(),
            Value<String?> canonicalName = const Value.absent(),
            Value<String?> canonicalIngredientId = const Value.absent(),
            Value<DateTime> estimatedExpiryDate = const Value.absent(),
            Value<double> confidence = const Value.absent(),
            Value<String> status = const Value.absent(),
            Value<String> source = const Value.absent(),
            Value<int> version = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              InventoryItemsTableCompanion(
            id: id,
            displayName: displayName,
            quantity: quantity,
            unit: unit,
            storageLocation: storageLocation,
            canonicalName: canonicalName,
            canonicalIngredientId: canonicalIngredientId,
            estimatedExpiryDate: estimatedExpiryDate,
            confidence: confidence,
            status: status,
            source: source,
            version: version,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String id,
            required String displayName,
            required double quantity,
            required String unit,
            required String storageLocation,
            Value<String?> canonicalName = const Value.absent(),
            Value<String?> canonicalIngredientId = const Value.absent(),
            required DateTime estimatedExpiryDate,
            required double confidence,
            Value<String> status = const Value.absent(),
            Value<String> source = const Value.absent(),
            Value<int> version = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              InventoryItemsTableCompanion.insert(
            id: id,
            displayName: displayName,
            quantity: quantity,
            unit: unit,
            storageLocation: storageLocation,
            canonicalName: canonicalName,
            canonicalIngredientId: canonicalIngredientId,
            estimatedExpiryDate: estimatedExpiryDate,
            confidence: confidence,
            status: status,
            source: source,
            version: version,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$InventoryItemsTableTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $InventoryItemsTableTable,
    InventoryItemsTableData,
    $$InventoryItemsTableTableFilterComposer,
    $$InventoryItemsTableTableOrderingComposer,
    $$InventoryItemsTableTableAnnotationComposer,
    $$InventoryItemsTableTableCreateCompanionBuilder,
    $$InventoryItemsTableTableUpdateCompanionBuilder,
    (
      InventoryItemsTableData,
      BaseReferences<_$AppDatabase, $InventoryItemsTableTable,
          InventoryItemsTableData>
    ),
    InventoryItemsTableData,
    PrefetchHooks Function()>;
typedef $$SavedRecipesTableTableCreateCompanionBuilder
    = SavedRecipesTableCompanion Function({
  required String recipeId,
  required String recipeTitle,
  Value<String?> imageUrl,
  Value<DateTime> savedAt,
  Value<int> rowid,
});
typedef $$SavedRecipesTableTableUpdateCompanionBuilder
    = SavedRecipesTableCompanion Function({
  Value<String> recipeId,
  Value<String> recipeTitle,
  Value<String?> imageUrl,
  Value<DateTime> savedAt,
  Value<int> rowid,
});

class $$SavedRecipesTableTableFilterComposer
    extends Composer<_$AppDatabase, $SavedRecipesTableTable> {
  $$SavedRecipesTableTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get recipeId => $composableBuilder(
      column: $table.recipeId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get recipeTitle => $composableBuilder(
      column: $table.recipeTitle, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get imageUrl => $composableBuilder(
      column: $table.imageUrl, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get savedAt => $composableBuilder(
      column: $table.savedAt, builder: (column) => ColumnFilters(column));
}

class $$SavedRecipesTableTableOrderingComposer
    extends Composer<_$AppDatabase, $SavedRecipesTableTable> {
  $$SavedRecipesTableTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get recipeId => $composableBuilder(
      column: $table.recipeId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get recipeTitle => $composableBuilder(
      column: $table.recipeTitle, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get imageUrl => $composableBuilder(
      column: $table.imageUrl, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get savedAt => $composableBuilder(
      column: $table.savedAt, builder: (column) => ColumnOrderings(column));
}

class $$SavedRecipesTableTableAnnotationComposer
    extends Composer<_$AppDatabase, $SavedRecipesTableTable> {
  $$SavedRecipesTableTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get recipeId =>
      $composableBuilder(column: $table.recipeId, builder: (column) => column);

  GeneratedColumn<String> get recipeTitle => $composableBuilder(
      column: $table.recipeTitle, builder: (column) => column);

  GeneratedColumn<String> get imageUrl =>
      $composableBuilder(column: $table.imageUrl, builder: (column) => column);

  GeneratedColumn<DateTime> get savedAt =>
      $composableBuilder(column: $table.savedAt, builder: (column) => column);
}

class $$SavedRecipesTableTableTableManager extends RootTableManager<
    _$AppDatabase,
    $SavedRecipesTableTable,
    SavedRecipeRecord,
    $$SavedRecipesTableTableFilterComposer,
    $$SavedRecipesTableTableOrderingComposer,
    $$SavedRecipesTableTableAnnotationComposer,
    $$SavedRecipesTableTableCreateCompanionBuilder,
    $$SavedRecipesTableTableUpdateCompanionBuilder,
    (
      SavedRecipeRecord,
      BaseReferences<_$AppDatabase, $SavedRecipesTableTable, SavedRecipeRecord>
    ),
    SavedRecipeRecord,
    PrefetchHooks Function()> {
  $$SavedRecipesTableTableTableManager(
      _$AppDatabase db, $SavedRecipesTableTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$SavedRecipesTableTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$SavedRecipesTableTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$SavedRecipesTableTableAnnotationComposer(
                  $db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> recipeId = const Value.absent(),
            Value<String> recipeTitle = const Value.absent(),
            Value<String?> imageUrl = const Value.absent(),
            Value<DateTime> savedAt = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              SavedRecipesTableCompanion(
            recipeId: recipeId,
            recipeTitle: recipeTitle,
            imageUrl: imageUrl,
            savedAt: savedAt,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String recipeId,
            required String recipeTitle,
            Value<String?> imageUrl = const Value.absent(),
            Value<DateTime> savedAt = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              SavedRecipesTableCompanion.insert(
            recipeId: recipeId,
            recipeTitle: recipeTitle,
            imageUrl: imageUrl,
            savedAt: savedAt,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$SavedRecipesTableTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $SavedRecipesTableTable,
    SavedRecipeRecord,
    $$SavedRecipesTableTableFilterComposer,
    $$SavedRecipesTableTableOrderingComposer,
    $$SavedRecipesTableTableAnnotationComposer,
    $$SavedRecipesTableTableCreateCompanionBuilder,
    $$SavedRecipesTableTableUpdateCompanionBuilder,
    (
      SavedRecipeRecord,
      BaseReferences<_$AppDatabase, $SavedRecipesTableTable, SavedRecipeRecord>
    ),
    SavedRecipeRecord,
    PrefetchHooks Function()>;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$InventoryItemsTableTableTableManager get inventoryItemsTable =>
      $$InventoryItemsTableTableTableManager(_db, _db.inventoryItemsTable);
  $$SavedRecipesTableTableTableManager get savedRecipesTable =>
      $$SavedRecipesTableTableTableManager(_db, _db.savedRecipesTable);
}
