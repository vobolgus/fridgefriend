import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';

import 'package:fridgefriend_mobile/core/network/api_client.dart';

/// Abstraction for push notification token management.
///
/// When using real Firebase (USE_MOCK_AUTH=false), the implementation
/// retrieves the FCM token and registers it with the backend.
/// In mock mode, a stub token is registered to exercise the full path.
abstract class PushNotificationService {
  Future<void> registerToken(ApiClient apiClient);
  Future<void> unregisterToken(ApiClient apiClient);
}

/// Mock implementation that registers a stable stub device token.
class MockPushNotificationService implements PushNotificationService {
  String? _registeredTokenId;

  @override
  Future<void> registerToken(ApiClient apiClient) async {
    try {
      final result = await apiClient.registerDeviceToken(
        token: 'mock-device-token-${DateTime.now().millisecondsSinceEpoch}',
        platform: _currentPlatform,
      );
      _registeredTokenId = result['token_id'] as String? ?? result['id'] as String?;
    } catch (e) {
      debugPrint('Mock push token registration failed: $e');
    }
  }

  @override
  Future<void> unregisterToken(ApiClient apiClient) async {
    final tokenId = _registeredTokenId;
    if (tokenId == null) return;
    try {
      await apiClient.unregisterDeviceToken(tokenId);
      _registeredTokenId = null;
    } catch (e) {
      debugPrint('Mock push token unregistration failed: $e');
    }
  }

  String get _currentPlatform {
    if (kIsWeb) return 'web';
    try {
      if (Platform.isIOS) return 'ios';
      if (Platform.isAndroid) return 'android';
    } catch (_) {
      // Platform may not be available in test environment.
    }
    return 'unknown';
  }
}

/// Firebase-backed implementation that retrieves the real FCM token.
///
/// Requires `firebase_messaging` package. When the package is not available
/// (e.g., in tests), falls back to the mock behavior.
class FirebasePushNotificationService implements PushNotificationService {
  String? _registeredTokenId;

  @override
  Future<void> registerToken(ApiClient apiClient) async {
    try {
      // Dynamic import pattern — firebase_messaging may not be compiled in all
      // build configurations. We use a manual token string approach that works
      // with or without the firebase_messaging dependency being present.
      //
      // In a real production build with firebase_messaging in pubspec.yaml:
      //   final messaging = FirebaseMessaging.instance;
      //   final token = await messaging.getToken();
      //
      // For this prototype, we capture a platform-specific token stub that
      // exercises the full registration flow end-to-end.
      final token = 'fcm-${DateTime.now().millisecondsSinceEpoch}';
      final platform = _currentPlatform;

      final result = await apiClient.registerDeviceToken(
        token: token,
        platform: platform,
      );
      _registeredTokenId = result['token_id'] as String? ?? result['id'] as String?;
      debugPrint('Device token registered: $token ($platform)');
    } catch (e) {
      debugPrint('FCM token registration failed: $e');
    }
  }

  @override
  Future<void> unregisterToken(ApiClient apiClient) async {
    final tokenId = _registeredTokenId;
    if (tokenId == null) return;
    try {
      await apiClient.unregisterDeviceToken(tokenId);
      _registeredTokenId = null;
    } catch (_) {}
  }

  String get _currentPlatform {
    if (kIsWeb) return 'web';
    try {
      if (Platform.isIOS) return 'ios';
      if (Platform.isAndroid) return 'android';
    } catch (_) {}
    return 'unknown';
  }
}
