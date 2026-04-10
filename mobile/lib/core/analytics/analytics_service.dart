import 'dart:async';

import 'package:amplitude_flutter/amplitude.dart';
import 'package:amplitude_flutter/configuration.dart';
import 'package:amplitude_flutter/events/base_event.dart';
import 'package:amplitude_flutter/events/identify.dart';

abstract class AnalyticsService {
  Future<void> track(String eventType,
      {Map<String, Object?> payload = const {}});
}

class NoopAnalyticsService implements AnalyticsService {
  const NoopAnalyticsService();

  @override
  Future<void> track(
    String eventType, {
    Map<String, Object?> payload = const {},
  }) async {}
}

class AmplitudeAnalyticsService implements AnalyticsService {
  AmplitudeAnalyticsService(this.apiKey) {
    if (!isConfigured) {
      return;
    }

    try {
      _amplitude = Amplitude(
        Configuration(
          apiKey: apiKey,
        ),
      );
      _buildFuture = _amplitude?.isBuilt;
    } catch (_) {
      _amplitude = null;
      _buildFuture = null;
    }
  }

  final String apiKey;
  Amplitude? _amplitude;
  Future<void>? _buildFuture;

  bool get isConfigured => apiKey.isNotEmpty && _amplitude != null;

  @override
  Future<void> track(
    String eventType, {
    Map<String, Object?> payload = const {},
  }) async {
    final amplitude = _amplitude;
    if (!isConfigured || amplitude == null) {
      return;
    }

    try {
      unawaited(_buildFuture);
      amplitude.track(
        BaseEvent(
          eventType,
          eventProperties: _sanitizeMap(payload),
        ),
      );
    } catch (_) {}
  }

  Future<void> setUserId(String? userId) async {
    final amplitude = _amplitude;
    if (!isConfigured || amplitude == null) {
      return;
    }

    try {
      unawaited(_buildFuture);
      amplitude.setUserId(userId);
    } catch (_) {}
  }

  Future<void> setUserProperties(Map<String, Object?> properties) async {
    final amplitude = _amplitude;
    if (!isConfigured || amplitude == null || properties.isEmpty) {
      return;
    }

    try {
      unawaited(_buildFuture);
      final identify = Identify();
      for (final entry in properties.entries) {
        final value = entry.value;
        if (value == null) {
          continue;
        }
        identify.set(entry.key, value);
      }
      amplitude.identify(identify);
    } catch (_) {}
  }

  Map<String, Object> _sanitizeMap(Map<String, Object?> values) {
    final sanitized = <String, Object>{};

    for (final entry in values.entries) {
      final value = entry.value;
      if (value == null) {
        continue;
      }
      sanitized[entry.key] = value;
    }

    return sanitized;
  }
}
