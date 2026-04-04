import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../domain/auth_service.dart';
import '../data/mock_auth_service.dart';

final authServiceProvider = Provider<AuthService>((ref) {
  return MockAuthService();
});

final authStateProvider = StreamProvider<String?>((ref) {
  final authService = ref.watch(authServiceProvider);
  return authService.authStateChanges;
});

final currentTokenProvider = FutureProvider<String?>((ref) async {
  final authService = ref.watch(authServiceProvider);
  return authService.getToken();
});
