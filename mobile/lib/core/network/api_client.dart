import 'package:dio/dio.dart';

import 'package:fridgefriend_mobile/core/network/api_config.dart';
import 'package:fridgefriend_mobile/features/households/domain/household.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
import 'package:fridgefriend_mobile/features/meal_planning/domain/meal_plan.dart';
import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';

class ApiClient {
  ApiClient({
    String? baseUrl,
    String? token,
    String? fallbackToken,
    Future<String?> Function()? tokenProvider,
  }) : _token = token,
        _fallbackToken = fallbackToken,
        _tokenProvider = tokenProvider,
        _dio = Dio(
          BaseOptions(
            baseUrl: baseUrl ?? ApiClient._baseUrl,
          ),
        ) {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final resolvedToken = await (_tokenProvider?.call() ?? Future.value(_token));
          final authorizationToken = resolvedToken ?? _fallbackToken;

          if (authorizationToken != null && authorizationToken.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $authorizationToken';
          } else {
            options.headers.remove('Authorization');
          }

          handler.next(options);
        },
      ),
    );
  }

  final Dio _dio;
  final String? _token;
  final String? _fallbackToken;
  final Future<String?> Function()? _tokenProvider;

  static const String _baseUrl = ApiConfig.defaultBaseUrl;

  Dio get rawClient => _dio;

  Future<List<InventoryItem>> getInventoryItems() async {
    final response = await _dio.get('${ApiConfig.apiVersionPath}/items');
    final payload = response.data;

    if (payload is List) {
      return payload
          .whereType<Map<String, dynamic>>()
          .map(InventoryItem.fromJson)
          .toList(growable: false);
    }

    if (payload is Map<String, dynamic>) {
      final items = payload['items'] as List<dynamic>? ?? const [];
      return items
          .whereType<Map<String, dynamic>>()
          .map(InventoryItem.fromJson)
          .toList(growable: false);
    }

    return const [];
  }

  Future<InventoryItem> createInventoryItem({
    required String displayName,
    required double quantity,
    required String unit,
    required String storageLocation,
    String? source,
    String? canonicalName,
    String? canonicalIngredientId,
    double? confidence,
    DateTime? estimatedExpiryDate,
  }) async {
    final data = <String, dynamic>{
      'display_name': displayName,
      'quantity': quantity,
      'unit': unit,
      'storage_location': storageLocation,
      if (source != null) 'source': source,
      if (canonicalName != null) 'canonical_name': canonicalName,
      if (canonicalIngredientId != null)
        'canonical_ingredient_id': canonicalIngredientId,
      if (confidence != null) 'confidence': confidence,
      if (estimatedExpiryDate != null)
        'estimated_expiry_date': estimatedExpiryDate.toIso8601String(),
    };

    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/items',
      data: data,
      options: Options(
        headers: {
          'Idempotency-Key': '${displayName}_${quantity}_${unit}_$storageLocation',
        },
      ),
    );

    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      return InventoryItem.fromJson(payload);
    }

    throw const FormatException('Invalid inventory item response');
  }

  Future<InventoryItem> updateItem({
    required String id,
    double? quantity,
    String? unit,
    String? storageLocation,
    DateTime? estimatedExpiryDate,
  }) async {
    final data = <String, dynamic>{
      if (quantity != null) 'quantity': quantity,
      if (unit != null) 'unit': unit,
      if (storageLocation != null) 'storage_location': storageLocation,
      if (estimatedExpiryDate != null)
        'estimated_expiry_date': estimatedExpiryDate.toIso8601String(),
    };

    final response = await _dio.patch(
      '${ApiConfig.apiVersionPath}/items/$id',
      data: data,
      options: Options(
        headers: {
          'Idempotency-Key':
              '${id}_update_${DateTime.now().millisecondsSinceEpoch}',
        },
      ),
    );

    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      return InventoryItem.fromJson(payload);
    }
    throw const FormatException('Invalid inventory item response');
  }

  Future<void> updateItemStatus(String id, String status) async {
    await _dio.post(
      '${ApiConfig.apiVersionPath}/items/$id/status',
      data: {'status': status},
      options: Options(
        headers: {'Idempotency-Key': '${id}_status_$status'},
      ),
    );
  }

  Future<void> undoItem(String id) async {
    await _dio.post(
      '${ApiConfig.apiVersionPath}/items/$id/undo',
      options: Options(
        headers: {'Idempotency-Key': '${id}_undo_${DateTime.now().millisecondsSinceEpoch}'},
      ),
    );
  }

  Future<List<Map<String, dynamic>>> getActivityLog(String householdId) async {
    final response = await _dio.get('${ApiConfig.apiVersionPath}/households/$householdId/activity');
    final payload = response.data;
    if (payload is List) {
      return payload.whereType<Map<String, dynamic>>().toList(growable: false);
    }
    if (payload is Map<String, dynamic>) {
      final items = payload['events'] as List<dynamic>? ?? payload['activity'] as List<dynamic>? ?? const [];
      return items.whereType<Map<String, dynamic>>().toList(growable: false);
    }
    return const [];
  }

  Future<List<Recipe>> getRecommendations({int servings = 2}) async {
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/recommendations',
      data: {'servings': servings},
      options: Options(
        headers: {'Idempotency-Key': 'recommendations_$servings'},
      ),
    );

    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      final recipes = payload['recipes'] as List<dynamic>? ?? const [];
      return recipes
          .whereType<Map<String, dynamic>>()
          .map(Recipe.fromJson)
          .toList(growable: false);
    }

    if (payload is List) {
      return payload
          .whereType<Map<String, dynamic>>()
          .map(Recipe.fromJson)
          .toList(growable: false);
    }

    return const [];
  }

  Future<MealPlan> generatePlan({int days = 7}) async {
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/plans',
      data: {'days': days},
      options: Options(headers: {'Idempotency-Key': 'plan_$days'}),
    );

    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      return MealPlan.fromJson(payload);
    }

    throw const FormatException('Invalid meal plan response');
  }

  Future<List<ShoppingItem>> getShoppingList() async {
    final response = await _dio.get('${ApiConfig.apiVersionPath}/shopping-list');
    final payload = response.data;

    if (payload is Map<String, dynamic>) {
      final items = payload['shoppingList'] as List<dynamic>? ??
          payload['items'] as List<dynamic>? ??
          const [];
      return items
          .whereType<Map<String, dynamic>>()
          .map(ShoppingItem.fromJson)
          .toList(growable: false);
    }

    if (payload is List) {
      return payload
          .whereType<Map<String, dynamic>>()
          .map(ShoppingItem.fromJson)
          .toList(growable: false);
    }

    return const [];
  }

  Future<List<Household>> getHouseholds() async {
    final response = await _dio.get('${ApiConfig.apiVersionPath}/households');
    final payload = response.data;
    if (payload is List) {
      return payload.whereType<Map<String, dynamic>>().map(Household.fromJson).toList(growable: false);
    }
    if (payload is Map<String, dynamic>) {
      final items = payload['households'] as List<dynamic>? ?? const [];
      return items.whereType<Map<String, dynamic>>().map(Household.fromJson).toList(growable: false);
    }
    return const [];
  }

  Future<Map<String, dynamic>> getNotificationPreferences() async {
    final response = await _dio.get('${ApiConfig.apiVersionPath}/notifications');
    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      return payload;
    }
    return {};
  }

  Future<Map<String, dynamic>> updateNotificationPreferences({
    bool? expiryReminderEnabled,
    int? reminderDaysBefore,
    String? quietHoursStart,
    String? quietHoursEnd,
  }) async {
    final data = <String, dynamic>{
      if (expiryReminderEnabled != null)
        'expiry_reminder_enabled': expiryReminderEnabled,
      if (reminderDaysBefore != null)
        'reminder_days_before': reminderDaysBefore,
      if (quietHoursStart != null)
        'quiet_hours_start': quietHoursStart,
      if (quietHoursEnd != null)
        'quiet_hours_end': quietHoursEnd,
    };
    final response = await _dio.patch(
      '${ApiConfig.apiVersionPath}/notifications',
      data: data,
      options: Options(
        headers: {
          'Idempotency-Key':
              'notif_pref_${data.entries.map((e) => '${e.key}_${e.value}').join('_')}',
        },
      ),
    );
    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      return payload;
    }
    return {};
  }

  Future<Map<String, dynamic>> registerDeviceToken({
    required String token,
    required String platform,
  }) async {
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/notifications/devices',
      data: {'token': token, 'platform': platform},
      options: Options(
        headers: {'Idempotency-Key': 'device_token_${token.hashCode}'},
      ),
    );
    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      return payload;
    }
    return {};
  }

  Future<void> unregisterDeviceToken(String tokenId) async {
    await _dio.delete(
      '${ApiConfig.apiVersionPath}/notifications/devices/$tokenId',
      options: Options(
        headers: {'Idempotency-Key': 'unregister_device_$tokenId'},
      ),
    );
  }

  Future<Household> createHousehold(String name) async {
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/households',
      data: {'name': name},
      options: Options(
        headers: {'Idempotency-Key': 'create_household_$name'},
      ),
    );
    return Household.fromJson(response.data as Map<String, dynamic>);
  }

  Future<Household> joinHousehold(String inviteCode) async {
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/households/join',
      data: {'invite_code': inviteCode},
      options: Options(
        headers: {'Idempotency-Key': 'join_household_$inviteCode'},
      ),
    );
    return Household.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> leaveHousehold(String id) async {
    await _dio.post(
      '${ApiConfig.apiVersionPath}/households/$id/leave',
      options: Options(
        headers: {'Idempotency-Key': 'leave_household_$id'},
      ),
    );
  }

  Future<InventoryItem> scanBarcode(String barcode) async {
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/scan/barcode',
      data: {
        'barcode': barcode,
        'quantity': 1,
        'storage_location': 'fridge',
      },
      options: Options(
        headers: {'Idempotency-Key': 'barcode_$barcode'},
      ),
    );

    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      return InventoryItem.fromJson(_normalizeInventoryItemJson(payload));
    }

    throw const FormatException('Invalid barcode scan response');
  }

  Future<String> uploadPhoto(String localFilePath) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(localFilePath),
    });
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/scan/photo/upload',
      data: formData,
      options: Options(
        headers: {
          'Idempotency-Key':
              'upload_${DateTime.now().millisecondsSinceEpoch}',
        },
      ),
    );

    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      final url = payload['image_url'] as String?;
      if (url != null) return url;
    }

    throw const FormatException('Invalid upload response');
  }

  Future<List<InventoryItem>> scanPhoto(String imageUrl) async {
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/scan/photo',
      data: {'image_url': imageUrl},
      options: Options(
        headers: {'Idempotency-Key': 'photo_scan_${imageUrl.hashCode}'},
      ),
    );

    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      final items = (payload['draft_items'] ?? payload['draftItems'] ?? payload['items'])
              as List<dynamic>? ??
          const [];
      return items
          .whereType<Map<String, dynamic>>()
          .map(_normalizeInventoryItemJson)
          .map(InventoryItem.fromJson)
          .toList(growable: false);
    }
    return const [];
  }

  static Map<String, dynamic> _normalizeInventoryItemJson(
    Map<String, dynamic> json,
  ) {
    return {
      ...json,
      'itemId': json['itemId'] ?? json['item_id'] ?? json['id'],
      'displayName': json['displayName'] ?? json['display_name'],
      'unit': json['unit'] ?? json['unit_name'],
      'storageLocation': json['storageLocation'] ?? json['storage_location'],
      'estimatedExpiryDate':
          json['estimatedExpiryDate'] ?? json['estimated_expiry_date'],
      'canonicalName': json['canonicalName'] ?? json['canonical_name'],
      'canonicalIngredientId':
          json['canonicalIngredientId'] ?? json['canonical_ingredient_id'],
    };
  }
}
