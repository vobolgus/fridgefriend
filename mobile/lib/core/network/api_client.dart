import 'package:dio/dio.dart';

import 'package:fridgefriend_mobile/core/network/api_config.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
import 'package:fridgefriend_mobile/features/meal_planning/domain/meal_plan.dart';
import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';

class ApiClient {
  ApiClient({String? baseUrl})
      : _dio = Dio(
          BaseOptions(
            baseUrl: baseUrl ?? ApiClient._baseUrl,
            headers: const {'Authorization': 'Bearer test-token'},
          ),
        );

  final Dio _dio;

  static const String _baseUrl = ApiConfig.defaultBaseUrl;

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
        'displayName': displayName,
        'quantity': quantity,
        'unit': unit,
        'storageLocation': storageLocation,
      },
      options: Options(
        headers: {
          'Idempotency-Key': '${displayName}_$quantity_$unit_$storageLocation',
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
}
