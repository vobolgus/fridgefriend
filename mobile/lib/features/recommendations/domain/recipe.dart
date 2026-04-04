class Recipe {
  const Recipe({
    required this.id,
    required this.title,
    required this.coveragePct,
    required this.score,
    required this.prepMinutes,
    required this.missingItems,
    required this.substitutions,
  });

  final String id;
  final String title;
  final double coveragePct;
  final double score;
  final int prepMinutes;
  final List<String> missingItems;
  final List<String> substitutions;

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
