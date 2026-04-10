import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';

import 'package:fridgefriend_mobile/core/network/api_config.dart';
import 'package:fridgefriend_mobile/features/households/domain/household.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
import 'package:fridgefriend_mobile/features/meal_planning/domain/meal_plan.dart';
import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';

typedef TokenProvider = Future<String?> Function();

TokenProvider forceRefreshAuthToken = _defaultForceRefreshAuthToken;

Future<String?> _defaultForceRefreshAuthToken() async {
  final user = FirebaseAuth.instance.currentUser;
  if (user == null) {
    return null;
  }

  return user.getIdToken(true);
}

class _AuthInterceptor extends QueuedInterceptor {
  _AuthInterceptor({
    required Dio dio,
    required String? token,
    required String? fallbackToken,
    required TokenProvider? tokenProvider,
  })  : _dio = dio,
        _token = token,
        _fallbackToken = fallbackToken,
        _tokenProvider = tokenProvider;

  static const String _retriedRequestKey = 'auth_token_refreshed';

  final Dio _dio;
  final String? _token;
  final String? _fallbackToken;
  final TokenProvider? _tokenProvider;

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final isRetriedRequest = options.extra[_retriedRequestKey] == true;
    if (isRetriedRequest && options.headers['Authorization'] != null) {
      handler.next(options);
      return;
    }

    final authorizationToken = await _resolveAuthorizationToken();

    if (authorizationToken != null && authorizationToken.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $authorizationToken';
    } else {
      options.headers.remove('Authorization');
    }

    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final statusCode = err.response?.statusCode;
    final requestOptions = err.requestOptions;
    final alreadyRetried = requestOptions.extra[_retriedRequestKey] == true;

    if (statusCode != 401 || alreadyRetried) {
      handler.next(err);
      return;
    }

    try {
      final refreshedToken = await forceRefreshAuthToken();
      if (refreshedToken == null || refreshedToken.isEmpty) {
        handler.next(err);
        return;
      }

      final response = await _dio.fetch<dynamic>(
        requestOptions.copyWith(
          headers: {
            ...requestOptions.headers,
            'Authorization': 'Bearer $refreshedToken',
          },
          extra: {
            ...requestOptions.extra,
            _retriedRequestKey: true,
          },
        ),
      );

      handler.resolve(response);
    } catch (_) {
      handler.next(err);
    }
  }

  Future<String?> _resolveAuthorizationToken() async {
    final resolvedToken =
        await (_tokenProvider?.call() ?? Future.value(_token));
    return resolvedToken ?? _fallbackToken;
  }
}

class ApiClient {
  ApiClient({
    String? baseUrl,
    String? token,
    String? fallbackToken,
    Future<String?> Function()? tokenProvider,
  })  : _token = token,
        _fallbackToken = fallbackToken,
        _tokenProvider = tokenProvider,
        _dio = Dio(
          BaseOptions(
            baseUrl: baseUrl ?? ApiClient._baseUrl,
          ),
        ) {
    _dio.interceptors.add(
      _AuthInterceptor(
        dio: _dio,
        token: _token,
        fallbackToken: _fallbackToken,
        tokenProvider: _tokenProvider,
      ),
    );
  }

  final Dio _dio;
  final String? _token;
  final String? _fallbackToken;
  final Future<String?> Function()? _tokenProvider;

  static const String _baseUrl = ApiConfig.defaultBaseUrl;

  Dio get rawClient => _dio;

  String _uniqueIdempotencyKey(String prefix) {
    return '${prefix}_${DateTime.now().microsecondsSinceEpoch}';
  }

  void _logUnexpectedResponse(String methodName, Object? payload) {
    debugPrint(
      'WARNING: Unexpected response format for $methodName: ${payload.runtimeType}',
    );
  }

  Future<List<InventoryItem>> getInventoryItems() async {
    final response = await _dio.get('${ApiConfig.apiVersionPath}/items');
    final payload = response.data;

    if (payload is List) {
      return payload
          .whereType<Map<String, dynamic>>()
          .map(InventoryItem.fromJson)
          .toList(growable: false);
    } else if (payload is Map && payload.containsKey('items')) {
      final normalizedPayload = Map<String, dynamic>.from(payload);
      final items = normalizedPayload['items'] as List<dynamic>? ?? const [];
      return items
          .whereType<Map<String, dynamic>>()
          .map(InventoryItem.fromJson)
          .toList(growable: false);
    }

    _logUnexpectedResponse('getInventoryItems', payload);
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
    String? idempotencyKey,
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
          'Idempotency-Key':
              idempotencyKey ?? _uniqueIdempotencyKey('create_item'),
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
    String? displayName,
    double? quantity,
    String? unit,
    String? storageLocation,
    DateTime? estimatedExpiryDate,
    int? version,
  }) async {
    final data = <String, dynamic>{
      if (displayName != null) 'display_name': displayName,
      if (quantity != null) 'quantity': quantity,
      if (unit != null) 'unit': unit,
      if (storageLocation != null) 'storage_location': storageLocation,
      if (estimatedExpiryDate != null)
        'estimated_expiry_date': estimatedExpiryDate.toIso8601String(),
      if (version != null) 'version': version,
    };

    final response = await _dio.patch(
      '${ApiConfig.apiVersionPath}/items/$id',
      data: data,
      options: Options(
        headers: {
          'Idempotency-Key': _uniqueIdempotencyKey('update_item_$id'),
        },
      ),
    );

    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      return InventoryItem.fromJson(payload);
    }
    throw const FormatException('Invalid inventory item response');
  }

  Future<InventoryItem> updateItemStatus(String id, String status,
      {int? version}) async {
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/items/$id/status',
      data: {'status': status, if (version != null) 'version': version},
      options: Options(
        headers: {
          'Idempotency-Key': _uniqueIdempotencyKey('${id}_status_$status')
        },
      ),
    );

    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      return InventoryItem.fromJson(payload);
    }
    throw const FormatException('Invalid status update response');
  }

  Future<void> undoItem(String id) async {
    await _dio.post(
      '${ApiConfig.apiVersionPath}/items/$id/undo',
      options: Options(
        headers: {'Idempotency-Key': _uniqueIdempotencyKey('undo_item_$id')},
      ),
    );
  }

  Future<List<Map<String, dynamic>>> getActivityLog(String householdId) async {
    final response = await _dio
        .get('${ApiConfig.apiVersionPath}/households/$householdId/activity');
    final payload = response.data;
    if (payload is List) {
      return payload.whereType<Map<String, dynamic>>().toList(growable: false);
    }
    if (payload is Map &&
        (payload.containsKey('events') || payload.containsKey('activity'))) {
      final normalizedPayload = Map<String, dynamic>.from(payload);
      final items = normalizedPayload['events'] as List<dynamic>? ??
          normalizedPayload['activity'] as List<dynamic>? ??
          const [];
      return items.whereType<Map<String, dynamic>>().toList(growable: false);
    }
    _logUnexpectedResponse('getActivityLog', payload);
    return const [];
  }

  Future<List<Recipe>> getRecommendations({int servings = 2}) async {
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/recommendations',
      data: {'servings': servings},
      options: Options(
        headers: {'Idempotency-Key': _uniqueIdempotencyKey('recommendations')},
      ),
    );

    final payload = response.data;
    if (payload is Map && payload.containsKey('recipes')) {
      final normalizedPayload = Map<String, dynamic>.from(payload);
      final recipes =
          normalizedPayload['recipes'] as List<dynamic>? ?? const [];
      return recipes
          .whereType<Map<String, dynamic>>()
          .map(Recipe.fromJson)
          .toList(growable: false);
    } else if (payload is List) {
      return payload
          .whereType<Map<String, dynamic>>()
          .map(Recipe.fromJson)
          .toList(growable: false);
    }

    _logUnexpectedResponse('getRecommendations', payload);
    return const [];
  }

  Future<Recipe> getRecipe(String id) async {
    final response = await _dio.get('${ApiConfig.apiVersionPath}/recipes/$id');
    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      return Recipe.fromJson(payload);
    }
    throw const FormatException('Invalid recipe response');
  }

  Future<MealPlan> generatePlan({int days = 7}) async {
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/plans',
      data: {'days': days},
      options: Options(
        headers: {'Idempotency-Key': _uniqueIdempotencyKey('plan')},
      ),
    );

    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      return MealPlan.fromJson(payload);
    }

    throw const FormatException('Invalid meal plan response');
  }

  Future<MealPlan?> getLatestPlan() async {
    try {
      final response = await _dio.get(
        '${ApiConfig.apiVersionPath}/plans/latest',
      );
      final payload = response.data;
      if (payload is Map<String, dynamic>) {
        return MealPlan.fromJson(payload);
      }
      _logUnexpectedResponse('getLatestPlan', payload);
      return null;
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        return null;
      }
      rethrow;
    }
  }

  Future<List<ShoppingItem>> getShoppingList() async {
    final response =
        await _dio.get('${ApiConfig.apiVersionPath}/shopping-list');
    final payload = response.data;

    if (payload is Map &&
        (payload.containsKey('shoppingList') || payload.containsKey('items'))) {
      final normalizedPayload = Map<String, dynamic>.from(payload);
      final items = normalizedPayload['shoppingList'] as List<dynamic>? ??
          normalizedPayload['items'] as List<dynamic>? ??
          const [];
      return items
          .whereType<Map<String, dynamic>>()
          .map(ShoppingItem.fromJson)
          .toList(growable: false);
    } else if (payload is List) {
      return payload
          .whereType<Map<String, dynamic>>()
          .map(ShoppingItem.fromJson)
          .toList(growable: false);
    }

    _logUnexpectedResponse('getShoppingList', payload);
    return const [];
  }

  Future<List<Household>> getHouseholds() async {
    final response = await _dio.get('${ApiConfig.apiVersionPath}/households');
    final payload = response.data;
    if (payload is List) {
      return payload
          .whereType<Map<String, dynamic>>()
          .map(Household.fromJson)
          .toList(growable: false);
    }
    if (payload is Map && payload.containsKey('households')) {
      final normalizedPayload = Map<String, dynamic>.from(payload);
      final items =
          normalizedPayload['households'] as List<dynamic>? ?? const [];
      return items
          .whereType<Map<String, dynamic>>()
          .map(Household.fromJson)
          .toList(growable: false);
    }
    _logUnexpectedResponse('getHouseholds', payload);
    return const [];
  }

  Future<Map<String, dynamic>> getNotificationPreferences() async {
    final response =
        await _dio.get('${ApiConfig.apiVersionPath}/notifications');
    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      return payload;
    }
    _logUnexpectedResponse('getNotificationPreferences', payload);
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
      if (quietHoursStart != null) 'quiet_hours_start': quietHoursStart,
      if (quietHoursEnd != null) 'quiet_hours_end': quietHoursEnd,
    };
    final response = await _dio.patch(
      '${ApiConfig.apiVersionPath}/notifications',
      data: data,
      options: Options(
        headers: {
          'Idempotency-Key': _uniqueIdempotencyKey('notif_pref'),
        },
      ),
    );
    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      return payload;
    }
    _logUnexpectedResponse('updateNotificationPreferences', payload);
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
        headers: {'Idempotency-Key': _uniqueIdempotencyKey('device_token')},
      ),
    );
    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      return payload;
    }
    _logUnexpectedResponse('registerDeviceToken', payload);
    return {};
  }

  Future<void> unregisterDeviceToken(String tokenId) async {
    await _dio.delete(
      '${ApiConfig.apiVersionPath}/notifications/devices/$tokenId',
      options: Options(
        headers: {
          'Idempotency-Key': _uniqueIdempotencyKey('unregister_device')
        },
      ),
    );
  }

  Future<Household> createHousehold(String name) async {
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/households',
      data: {'name': name},
      options: Options(
        headers: {'Idempotency-Key': _uniqueIdempotencyKey('create_household')},
      ),
    );
    return Household.fromJson(response.data as Map<String, dynamic>);
  }

  Future<Household> joinHousehold(String inviteCode) async {
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/households/join',
      data: {'invite_code': inviteCode},
      options: Options(
        headers: {'Idempotency-Key': _uniqueIdempotencyKey('join_household')},
      ),
    );
    return Household.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> leaveHousehold(String id) async {
    await _dio.post(
      '${ApiConfig.apiVersionPath}/households/$id/leave',
      options: Options(
        headers: {'Idempotency-Key': _uniqueIdempotencyKey('leave_household')},
      ),
    );
  }

  Future<void> setActiveHousehold(String householdId) async {
    await _dio.patch(
      '${ApiConfig.apiVersionPath}/households/$householdId',
      data: {'is_active': true},
      options: Options(
        headers: {
          'Idempotency-Key': _uniqueIdempotencyKey('set_active_household'),
        },
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
        headers: {'Idempotency-Key': _uniqueIdempotencyKey('barcode_scan')},
      ),
    );

    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      return InventoryItem.fromJson(_normalizeInventoryItemJson(payload));
    }

    throw const FormatException('Invalid barcode scan response');
  }

  Future<String> uploadPhoto(
    String localFilePath, {
    void Function(int sent, int total)? onSendProgress,
  }) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(localFilePath),
    });
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/scan/photo/upload',
      data: formData,
      onSendProgress: onSendProgress,
      options: Options(
        headers: {
          'Idempotency-Key': _uniqueIdempotencyKey('upload_photo'),
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
        headers: {'Idempotency-Key': _uniqueIdempotencyKey('photo_scan')},
      ),
    );

    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      final items = (payload['draft_items'] ??
              payload['draftItems'] ??
              payload['items']) as List<dynamic>? ??
          const [];
      return items
          .whereType<Map<String, dynamic>>()
          .map(_normalizeInventoryItemJson)
          .map(InventoryItem.fromJson)
          .toList(growable: false);
    }
    _logUnexpectedResponse('scanPhoto', payload);
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
