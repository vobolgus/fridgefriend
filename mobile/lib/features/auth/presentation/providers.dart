import 'package:flutter_riverpod/flutter_riverpod.dart';

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

final authStateProvider = StreamProvider<String?>((ref) {
  final authService = ref.watch(authServiceProvider);
  return authService.authStateChanges;
});

final currentTokenProvider = FutureProvider<String?>((ref) async {
  final authService = ref.watch(authServiceProvider);
  return authService.getToken();
});
