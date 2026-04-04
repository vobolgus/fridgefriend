class Recipe {
  const Recipe({
    required this.id,
    required this.title,
    required this.coveragePct,
    required this.score,
    required this.prepMinutes,
    required this.missingItems,
    required this.substitutions,
    this.imageUrl,
    this.sourceUrl,
    this.summary,
    this.instructions = const [],
    this.cuisines = const [],
    this.servings,
    this.nutrition,
    this.dietaryTags = const [],
    this.ingredients = const [],
  });

  final String id;
  final String title;
  final double coveragePct;
  final double score;
  final int prepMinutes;
  final List<String> missingItems;
  final List<String> substitutions;
  final String? imageUrl;
  final String? sourceUrl;
  final String? summary;
  final List<Map<String, dynamic>> instructions;
  final List<String> cuisines;
  final int? servings;
  final Map<String, dynamic>? nutrition;
  final List<String> dietaryTags;
  final List<Map<String, dynamic>> ingredients;

  factory Recipe.fromJson(Map<String, dynamic> json) {
    return Recipe(
      id: (json['id'] ?? '').toString(),
      title: (json['title'] ?? '').toString(),
      coveragePct: _asDouble(json['coveragePct']),
      score: _asDouble(json['score'] ?? json['useSoonScore']),
      prepMinutes: _asInt(json['prepMinutes']),
      missingItems: (json['missingItems'] as List<dynamic>? ?? const [])
          .map((item) => item.toString())
          .toList(growable: false),
      substitutions: (json['substitutions'] as List<dynamic>? ?? const [])
          .map((s) => s.toString())
          .toList(growable: false),
      imageUrl: json['imageUrl']?.toString(),
      sourceUrl: json['sourceUrl']?.toString(),
      summary: json['summary']?.toString(),
      instructions: (json['instructions'] as List<dynamic>? ?? const [])
          .map((i) => Map<String, dynamic>.from(i as Map))
          .toList(growable: false),
      cuisines: (json['cuisines'] as List<dynamic>? ?? const [])
          .map((c) => c.toString())
          .toList(growable: false),
      servings: json['servings'] != null ? _asInt(json['servings']) : null,
      nutrition: json['nutrition'] != null
          ? Map<String, dynamic>.from(json['nutrition'] as Map)
          : null,
      dietaryTags: (json['dietaryTags'] as List<dynamic>? ?? const [])
          .map((t) => t.toString())
          .toList(growable: false),
      ingredients: (json['ingredients'] as List<dynamic>? ?? const [])
          .map((i) => Map<String, dynamic>.from(i as Map))
          .toList(growable: false),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'coveragePct': coveragePct,
      'score': score,
      'prepMinutes': prepMinutes,
      'missingItems': missingItems,
      'substitutions': substitutions,
      if (imageUrl != null) 'imageUrl': imageUrl,
      if (sourceUrl != null) 'sourceUrl': sourceUrl,
      if (summary != null) 'summary': summary,
      'instructions': instructions,
      'cuisines': cuisines,
      if (servings != null) 'servings': servings,
      if (nutrition != null) 'nutrition': nutrition,
      'dietaryTags': dietaryTags,
      'ingredients': ingredients,
    };
  }

  static double _asDouble(Object? value) {
    if (value is num) {
      return value.toDouble();
    }

    return double.tryParse(value?.toString() ?? '') ?? 0;
  }

  static int _asInt(Object? value) {
    if (value is num) {
      return value.toInt();
    }

    return int.tryParse(value?.toString() ?? '') ?? 0;
  }
}
