import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fridgefriend_mobile/core/analytics/analytics_service.dart';
import '../data/firebase_auth_service.dart';
import '../domain/auth_service.dart';
import '../data/mock_auth_service.dart';

const bool useMockAuth = bool.fromEnvironment(
  'USE_MOCK_AUTH',
  defaultValue: false,
);

final authServiceProvider = Provider<AuthService>((ref) {
  if (useMockAuth) {
    return MockAuthService();
  }

  return FirebaseAuthService();
});

final analyticsProvider = Provider<AnalyticsService>((ref) {
  const apiKey = String.fromEnvironment('AMPLITUDE_API_KEY', defaultValue: '');
  if (apiKey.isEmpty) {
    return const NoopAnalyticsService();
  }

  return AmplitudeAnalyticsService(apiKey);
});

final authStateProvider = StreamProvider<String?>((ref) {
  final authService = ref.watch(authServiceProvider);
  return authService.authStateChanges;
});

final currentTokenProvider = FutureProvider<String?>((ref) async {
  final authService = ref.watch(authServiceProvider);
  return authService.getToken();
});
