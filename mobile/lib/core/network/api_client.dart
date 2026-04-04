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
  }) async {
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/items',
      data: {
        'display_name': displayName,
        'quantity': quantity,
        'unit': unit,
        'storage_location': storageLocation,
      },
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

  Future<void> updateItemStatus(String id, String status) async {
    await _dio.patch(
      '${ApiConfig.apiVersionPath}/items/$id',
      data: {'status': status},
      options: Options(
        headers: {'Idempotency-Key': '${id}_$status'},
      ),
    );
  }

  Future<List<Recipe>> getRecommendations({int servings = 2}) async {
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/recommendations',
      data: {'servings': servings},
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

  Future<Household> createHousehold(String name) async {
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/households',
      data: {'name': name},
    );
    return Household.fromJson(response.data as Map<String, dynamic>);
  }

  Future<Household> joinHousehold(String inviteCode) async {
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/households/join',
      data: {'invite_code': inviteCode},
    );
    return Household.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> leaveHousehold(String id) async {
    await _dio.post('${ApiConfig.apiVersionPath}/households/$id/leave');
  }

  Future<InventoryItem> scanBarcode(String barcode) async {
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/scan/barcode',
      data: {
        'barcode': barcode,
        'quantity': 1,
        'storage_location': 'fridge',
      },
    );

    final payload = response.data;
    if (payload is Map<String, dynamic>) {
      return InventoryItem.fromJson(_normalizeInventoryItemJson(payload));
    }

    throw const FormatException('Invalid barcode scan response');
  }

  Future<List<InventoryItem>> scanPhoto(String imageUrl) async {
    final response = await _dio.post(
      '${ApiConfig.apiVersionPath}/scan/photo',
      data: {'image_url': imageUrl},
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
      'storageLocation': json['storageLocation'] ?? json['storage_location'],
      'estimatedExpiryDate':
          json['estimatedExpiryDate'] ?? json['estimated_expiry_date'],
    };
  }
}
