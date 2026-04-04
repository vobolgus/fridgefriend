import 'dart:convert';

import 'package:drift/drift.dart';

import 'package:fridgefriend_mobile/database/app_database.dart';
import 'package:fridgefriend_mobile/features/recommendations/domain/recipe.dart';

class CachedRecipeRecord {
  const CachedRecipeRecord({
    required this.id,
    required this.title,
    required this.coveragePct,
    required this.score,
    required this.prepMinutes,
    required this.missingItems,
    required this.syncedAt,
  });

  final String id;
  final String title;
  final double coveragePct;
  final double score;
  final int prepMinutes;
  final List<String> missingItems;
  final DateTime syncedAt;

  Recipe toDomain() {
    return Recipe(
      id: id,
      title: title,
      coveragePct: coveragePct,
      score: score,
      prepMinutes: prepMinutes,
      missingItems: missingItems,
      substitutions: const [],
    );
  }
}

class RecipeDao {
  RecipeDao(this._db);

  final AppDatabase _db;

  Future<List<CachedRecipeRecord>> getAllRecipes() async {
    final rows = await _db.customSelect(
      'SELECT id, title, coverage_pct, score, prep_minutes, missing_items_json, synced_at '
      'FROM recipes_cache ORDER BY synced_at DESC, title ASC',
    ).get();

    return rows.map(_mapRow).toList(growable: false);
  }

  Future<void> replaceAllRecipes(List<Recipe> recipes) async {
    await _db.transaction(() async {
      await _db.customStatement('DELETE FROM recipes_cache');

      for (final recipe in recipes) {
        await _db.customStatement(
          'INSERT OR REPLACE INTO recipes_cache '
          '(id, title, coverage_pct, score, prep_minutes, missing_items_json, synced_at) '
          'VALUES (?, ?, ?, ?, ?, ?, ?)',
          <Object?>[
            recipe.id,
            recipe.title,
            recipe.coveragePct,
            recipe.score,
            recipe.prepMinutes,
            jsonEncode(recipe.missingItems),
            DateTime.now().toIso8601String(),
          ],
        );
      }
    });
  }

  Future<void> clear() => _db.customStatement('DELETE FROM recipes_cache');

  CachedRecipeRecord _mapRow(QueryRow row) {
    final missingItemsJson = row.read<String>('missing_items_json');
    final syncedAtRaw = row.read<String>('synced_at');

    return CachedRecipeRecord(
      id: row.read<String>('id'),
      title: row.read<String>('title'),
      coveragePct: row.read<double>('coverage_pct'),
      score: row.read<double>('score'),
      prepMinutes: row.read<int>('prep_minutes'),
      missingItems: (jsonDecode(missingItemsJson) as List<dynamic>)
          .map((item) => item.toString())
          .toList(growable: false),
      syncedAt: DateTime.tryParse(syncedAtRaw) ?? DateTime.fromMillisecondsSinceEpoch(0),
    );
  }
}
