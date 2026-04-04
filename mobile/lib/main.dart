import 'package:flutter/material.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:sentry_flutter/sentry_flutter.dart';

import 'package:fridgefriend_mobile/app.dart';

const String _sentryDsn =
    String.fromEnvironment('SENTRY_DSN', defaultValue: '');
const bool _useMockAuth =
    bool.fromEnvironment('USE_MOCK_AUTH', defaultValue: false);

@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  debugPrint('Background message: ${message.messageId}');
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Firebase when using real auth.
  // Requires platform config files (GoogleService-Info.plist / google-services.json).
  if (!_useMockAuth) {
    try {
      await Firebase.initializeApp();
      FirebaseMessaging.onBackgroundMessage(
          _firebaseMessagingBackgroundHandler);
    } catch (e) {
      debugPrint('Firebase initialization failed: $e');
      debugPrint(
          'Ensure Firebase config files are present, or use USE_MOCK_AUTH=true.');
    }
  }

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
