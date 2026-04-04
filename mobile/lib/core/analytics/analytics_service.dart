abstract class AnalyticsService {
  Future<void> track(String eventType, {Map<String, Object?> payload = const {}});
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
  const AmplitudeAnalyticsService(this.apiKey);

  final String apiKey;

  bool get isConfigured => apiKey.isNotEmpty;

  @override
  Future<void> track(
    String eventType, {
    Map<String, Object?> payload = const {},
  }) async {
    if (!isConfigured) {
      return;
    }

    // Stub only: real SDK wiring happens once analytics is enabled.
    return;
  }
}
