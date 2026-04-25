import 'dart:async';
import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fridgefriend_mobile/core/design/theme.dart';

// Golden tests for AppTheme light/dark.
//
// The production theme uses GoogleFonts.inter which makes async HTTP calls to
// load font files. In the test environment those calls return HTTP 400 and the
// font loader throws. We suppress those specific exceptions so the widget still
// renders (with system fallback font) and the golden captures color/shape
// faithfully without requiring network access or bundled font assets.
//
// Goldens are platform-sensitive: Flutter's golden comparison includes anti-
// aliased font glyphs, and Linux Freetype renders glyphs slightly differently
// from macOS CoreText. The committed baselines were captured on macOS, so we
// only run the comparison on macOS hosts. Linux/Windows CI runners skip — the
// hardcoded-color lint test (no_hardcoded_colors_test.dart) provides the
// platform-independent regression coverage.

// Skip on non-macOS hosts (e.g. Linux CI runners). Reason: golden baselines
// were rendered on macOS and Freetype glyph anti-aliasing on Linux produces
// sub-pixel diffs that fail the comparison.
final bool _skipOnThisHost = kIsWeb || !Platform.isMacOS;

bool _isFontError(String msg) =>
    msg.contains('google_fonts') ||
    msg.contains('GoogleFonts') ||
    msg.contains('Failed to load font') ||
    msg.contains('allowRuntimeFetching') ||
    msg.contains('fonts.gstatic.com');

void main() {
  FlutterExceptionHandler? originalOnError;

  setUp(() {
    originalOnError = FlutterError.onError;
    FlutterError.onError = (FlutterErrorDetails details) {
      if (_isFontError(details.exceptionAsString())) return;
      originalOnError?.call(details);
    };
  });

  tearDown(() {
    FlutterError.onError = originalOnError;
  });

  group('theme golden', () {
    testWidgets('light theme snapshot', (tester) async {
      await runZonedGuarded(
        () async {
          await tester.pumpWidget(_buildSampleApp(theme: AppTheme.light));
          await tester.pump();
        },
        (error, stack) {
          if (_isFontError(error.toString())) return;
          Error.throwWithStackTrace(error, stack);
        },
      );
      await tester.pump(const Duration(milliseconds: 300));
      await expectLater(
        find.byType(MaterialApp),
        matchesGoldenFile('goldens/theme_light.png'),
      );
    }, skip: _skipOnThisHost);

    testWidgets('dark theme snapshot', (tester) async {
      await runZonedGuarded(
        () async {
          await tester.pumpWidget(_buildSampleApp(theme: AppTheme.dark));
          await tester.pump();
        },
        (error, stack) {
          if (_isFontError(error.toString())) return;
          Error.throwWithStackTrace(error, stack);
        },
      );
      await tester.pump(const Duration(milliseconds: 300));
      await expectLater(
        find.byType(MaterialApp),
        matchesGoldenFile('goldens/theme_dark.png'),
      );
    }, skip: _skipOnThisHost);
  });
}

Widget _buildSampleApp({required ThemeData theme}) {
  return MaterialApp(
    debugShowCheckedModeBanner: false,
    theme: theme,
    home: Builder(builder: (ctx) {
      final cs = Theme.of(ctx).colorScheme;
      return Scaffold(
        appBar: AppBar(title: const Text('Theme Sample')),
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: const Text('Card on surfaceContainer'),
                ),
              ),
              const SizedBox(height: 12),
              FilledButton(onPressed: () {}, child: const Text('Filled')),
              const SizedBox(height: 8),
              OutlinedButton(onPressed: () {}, child: const Text('Outlined')),
              const SizedBox(height: 12),
              const TextField(
                decoration: InputDecoration(labelText: 'Label', hintText: 'Hint'),
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                children: [
                  FilterChip(
                      label: const Text('Off'),
                      selected: false,
                      onSelected: (_) {}),
                  FilterChip(
                      label: const Text('On'),
                      selected: true,
                      onSelected: (_) {}),
                ],
              ),
              const SizedBox(height: 12),
              Container(
                decoration: BoxDecoration(
                  color: cs.surfaceContainerHigh,
                  borderRadius: BorderRadius.circular(16),
                ),
                padding: const EdgeInsets.all(16),
                child: const Text('Bottom-sheet style'),
              ),
              const SizedBox(height: 12),
              Container(
                decoration: BoxDecoration(
                  color: cs.inverseSurface,
                  borderRadius: BorderRadius.circular(8),
                ),
                padding: const EdgeInsets.all(12),
                child: Text(
                  'SnackBar style',
                  style: TextStyle(color: cs.onInverseSurface),
                ),
              ),
            ],
          ),
        ),
        bottomNavigationBar: NavigationBar(
          destinations: const [
            NavigationDestination(icon: Icon(Icons.home), label: 'Home'),
            NavigationDestination(icon: Icon(Icons.search), label: 'Search'),
            NavigationDestination(
                icon: Icon(Icons.settings), label: 'Settings'),
          ],
        ),
      );
    }),
  );
}
