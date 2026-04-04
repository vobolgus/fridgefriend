import 'dart:async';
import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

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
      _registeredTokenId =
          result['token_id'] as String? ?? result['id'] as String?;
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
  ApiClient? _apiClient;
  StreamSubscription<String>? _tokenRefreshSubscription;

  @override
  Future<void> registerToken(ApiClient apiClient) async {
    _apiClient = apiClient;

    FirebaseMessaging messaging;
    try {
      messaging = FirebaseMessaging.instance;
    } catch (e) {
      debugPrint('Failed to access Firebase Messaging instance: $e');
      return;
    }

    try {
      await messaging.requestPermission();
    } catch (e) {
      debugPrint('FCM permission request failed: $e');
    }

    String? token;
    try {
      token = await messaging.getToken();
    } catch (e) {
      debugPrint('FCM token retrieval failed: $e');
      return;
    }

    if (token == null) {
      debugPrint(
          'FCM token retrieval returned null. Skipping device registration.');
      return;
    }

    try {
      final result = await apiClient.registerDeviceToken(
        token: token,
        platform: _currentPlatform,
      );
      _registeredTokenId =
          result['token_id'] as String? ?? result['id'] as String?;
      debugPrint('Device token registered: $token ($_currentPlatform)');
    } catch (e) {
      debugPrint('FCM token registration failed: $e');
    }

    await _tokenRefreshSubscription?.cancel();
    try {
      _tokenRefreshSubscription =
          messaging.onTokenRefresh.listen((newToken) async {
        final refreshApiClient = _apiClient;
        if (refreshApiClient == null) {
          debugPrint(
              'Skipping FCM token refresh registration: missing API client.');
          return;
        }

        try {
          final previousTokenId = _registeredTokenId;
          if (previousTokenId != null) {
            await refreshApiClient.unregisterDeviceToken(previousTokenId);
          }

          final result = await refreshApiClient.registerDeviceToken(
            token: newToken,
            platform: _currentPlatform,
          );
          _registeredTokenId =
              result['token_id'] as String? ?? result['id'] as String?;
          debugPrint('Device token refreshed: $newToken ($_currentPlatform)');
        } catch (e) {
          debugPrint('FCM token refresh registration failed: $e');
        }
      });
    } catch (e) {
      debugPrint('FCM token refresh listener setup failed: $e');
    }
  }

  @override
  Future<void> unregisterToken(ApiClient apiClient) async {
    final tokenId = _registeredTokenId;
    await _tokenRefreshSubscription?.cancel();
    _tokenRefreshSubscription = null;

    if (tokenId != null) {
      try {
        await apiClient.unregisterDeviceToken(tokenId);
        _registeredTokenId = null;
      } catch (e) {
        debugPrint('FCM token unregistration failed: $e');
      }
    }

    try {
      await FirebaseMessaging.instance.deleteToken();
    } catch (e) {
      debugPrint('FCM token deletion failed: $e');
    }

    _apiClient = null;
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
