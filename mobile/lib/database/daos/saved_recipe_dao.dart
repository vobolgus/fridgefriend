import 'package:drift/drift.dart';

import 'package:fridgefriend_mobile/database/app_database.dart';

class SavedRecipeEntry {
  const SavedRecipeEntry({
    required this.recipeId,
    required this.recipeTitle,
    this.imageUrl,
    required this.savedAt,
  });

  final String recipeId;
  final String recipeTitle;
  final String? imageUrl;
  final DateTime savedAt;
}

class SavedRecipeDao {
  SavedRecipeDao(this._db);

  final AppDatabase _db;

  Future<bool> isSaved(String recipeId) async {
    final rows = await _db.customSelect(
      'SELECT 1 FROM saved_recipes WHERE recipe_id = ? LIMIT 1',
      variables: [Variable<String>(recipeId)],
    ).get();
    return rows.isNotEmpty;
  }

  Future<void> toggleSave(
      String recipeId, String title, String? imageUrl) async {
    final saved = await isSaved(recipeId);
    if (saved) {
      await _db.customStatement(
        'DELETE FROM saved_recipes WHERE recipe_id = ?',
        [recipeId],
      );
    } else {
      await _db.customStatement(
        'INSERT OR REPLACE INTO saved_recipes (recipe_id, recipe_title, image_url, saved_at) '
        'VALUES (?, ?, ?, ?)',
        [recipeId, title, imageUrl, DateTime.now().toIso8601String()],
      );
    }
  }

  Future<List<SavedRecipeEntry>> getAllSaved() async {
    final rows = await _db
        .customSelect(
          'SELECT recipe_id, recipe_title, image_url, saved_at '
          'FROM saved_recipes ORDER BY saved_at DESC',
        )
        .get();

    return rows.map((row) {
      final savedAtRaw = row.read<String>('saved_at');
      return SavedRecipeEntry(
        recipeId: row.read<String>('recipe_id'),
        recipeTitle: row.read<String>('recipe_title'),
        imageUrl: row.readNullable<String>('image_url'),
        savedAt: DateTime.tryParse(savedAtRaw) ??
            DateTime.fromMillisecondsSinceEpoch(0),
      );
    }).toList(growable: false);
  }
}
