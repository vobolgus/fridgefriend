import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sentry_flutter/sentry_flutter.dart';

import 'package:fridgefriend_mobile/app.dart';

const String _sentryDsn = String.fromEnvironment('SENTRY_DSN', defaultValue: '');

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  if (_sentryDsn.isEmpty) {
    runApp(const ProviderScope(child: MyApp()));
    return;
  }

  await SentryFlutter.init(
    (options) {
      options.dsn = _sentryDsn;
    },
    appRunner: () {
      runApp(
        SentryWidget(
          child: const ProviderScope(child: MyApp()),
        ),
      );
    },
  );
}
