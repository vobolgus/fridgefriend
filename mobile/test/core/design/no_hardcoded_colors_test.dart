import 'dart:io';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('no_hardcoded_colors', () {
    test(
      'lib/features and lib/core/presentation must not contain hardcoded Colors.* or Color(0xFF...)',
      () {
        const allowlist = <String>{
          'lib/core/presentation/widgets/app_bar.dart',
          'lib/core/presentation/widgets/urgency_badge.dart',
          'lib/core/presentation/widgets/empty_state.dart',
          'lib/core/presentation/widgets/error_view.dart',
          'lib/core/presentation/widgets/loading_view.dart',
        };

        final patterns = <RegExp>[
          RegExp(r'\bColors\.white(?:12|24|30|38|54|60|70)?\b'),
          RegExp(r'\bColors\.black(?:12|26|38|45|54|87)?\b'),
          RegExp(r'\bColors\.grey(?:\[\d+\])?\b'),
          RegExp(r'\bColor\(0x[fF]{2}[fF]{6}\)'),
          RegExp(r'\bColor\(0x[fF]{2}0{6}\)'),
          RegExp(
              r'\bColors\.(red|green|blue|orange|yellow|purple|pink|cyan|amber|teal|indigo)(?:Accent)?\b(?!\.shade)'),
        ];

        // Tests run from mobile/ as cwd
        expect(Directory('lib').existsSync(), isTrue,
            reason: 'must run from mobile/ directory');

        final scanRoots = <Directory>[
          Directory('lib/features'),
          Directory('lib/core/presentation'),
        ];

        final violations = <String>[];

        for (final root in scanRoots) {
          if (!root.existsSync()) continue;
          for (final entity in root.listSync(recursive: true)) {
            if (entity is! File) continue;
            if (!entity.path.endsWith('.dart')) continue;

            // Normalize path separators to forward slashes
            final relPath = entity.path.replaceAll(r'\', '/');
            // Strip leading './' if present
            final normalizedPath = relPath.startsWith('./')
                ? relPath.substring(2)
                : relPath;

            if (allowlist.contains(normalizedPath)) continue;

            final lines = entity.readAsLinesSync();
            for (var i = 0; i < lines.length; i++) {
              final codeOnly = lines[i].split('//').first;
              for (final p in patterns) {
                final m = p.firstMatch(codeOnly);
                if (m != null) {
                  violations.add(
                      '$normalizedPath:${i + 1}: ${m.group(0)}    (line: ${lines[i].trim()})');
                }
              }
            }
          }
        }

        if (violations.isNotEmpty) {
          fail(
            'Found ${violations.length} hardcoded color usages. '
            'Use Theme.of(context).colorScheme.* or AppColors.* instead.\n\n'
            '${violations.join('\n')}',
          );
        }
      },
    );
  });
}
