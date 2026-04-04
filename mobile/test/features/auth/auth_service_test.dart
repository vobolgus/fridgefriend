import 'package:flutter_test/flutter_test.dart';
import 'package:fridgefriend_mobile/features/auth/data/mock_auth_service.dart';

void main() {
  group('MockAuthService', () {
    late MockAuthService authService;

    setUp(() {
      authService = MockAuthService();
    });

    test('initial state is null token', () async {
      final token = await authService.getToken();
      expect(token, isNull);
    });

    test('signIn sets token and emits to stream', () async {
      expect(authService.authStateChanges, emitsInOrder(['test-token']));
      await authService.signIn('email');
      final token = await authService.getToken();
      expect(token, 'test-token');
    });

    test('signOut clears token and emits to stream', () async {
      await authService.signIn('email');
      expect(authService.authStateChanges, emitsInOrder([null]));
      await authService.signOut();
      final token = await authService.getToken();
      expect(token, isNull);
    });
  });
}
