class MealPlan {
  const MealPlan({
    required this.planId,
    required this.days,
    required this.shoppingList,
  });

  final String planId;
  final List<PlanDay> days;
  final List<ShoppingItem> shoppingList;

  factory MealPlan.fromJson(Map<String, dynamic> json) {
    final plan = (json['plan'] as Map<String, dynamic>?) ?? json;
    final rawDays = plan['days'] as List<dynamic>? ?? const [];
    final rawShoppingList = (json['shoppingList'] as List<dynamic>?) ??
        (plan['shoppingList'] as List<dynamic>?) ??
        const [];

    return MealPlan(
      planId: (plan['planId'] ?? plan['id'] ?? '').toString(),
      days: rawDays
          .whereType<Map<String, dynamic>>()
          .map(PlanDay.fromJson)
          .toList(growable: false),
      shoppingList: rawShoppingList
          .whereType<Map<String, dynamic>>()
          .map(ShoppingItem.fromJson)
          .toList(growable: false),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'planId': planId,
      'days': days.map((day) => day.toJson()).toList(growable: false),
      'shoppingList':
          shoppingList.map((item) => item.toJson()).toList(growable: false),
    };
  }
}

class PlanDay {
  const PlanDay({
    required this.date,
    required this.recipeId,
    required this.recipeTitle,
  });

  final DateTime date;
  final String recipeId;
  final String recipeTitle;

  factory PlanDay.fromJson(Map<String, dynamic> json) {
    return PlanDay(
      date:
          DateTime.tryParse((json['date'] ?? '').toString()) ?? DateTime.now(),
      recipeId: (json['recipeId'] ?? '').toString(),
      recipeTitle: (json['recipeTitle'] ?? json['title'] ?? '').toString(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'date': date.toIso8601String(),
      'recipeId': recipeId,
      'recipeTitle': recipeTitle,
    };
  }
}

class ShoppingItem {
  const ShoppingItem({
    required this.ingredientName,
    required this.quantity,
    required this.unit,
    this.reason,
  });

  final String ingredientName;
  final double quantity;
  final String unit;
  final String? reason;

  factory ShoppingItem.fromJson(Map<String, dynamic> json) {
    return ShoppingItem(
      ingredientName: (json['ingredientName'] ??
              json['ingredient_name'] ??
              json['name'] ??
              '')
          .toString(),
      quantity: _asDouble(json['quantity']),
      unit: (json['unit'] ?? '').toString(),
      reason: (json['reason'] ?? json['recipe_reason'] ?? json['recipeReason'])
          ?.toString(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'ingredientName': ingredientName,
      'quantity': quantity,
      'unit': unit,
      'reason': reason,
    };
  }

  static double _asDouble(Object? value) {
    if (value is num) {
      return value.toDouble();
    }

    return double.tryParse(value?.toString() ?? '') ?? 0;
  }
}
