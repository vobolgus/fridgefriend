import '../domain/auth_service.dart';
import 'mock_auth_service.dart';

class FirebaseAuthService implements AuthService {
  final _mock = MockAuthService();

  @override
  Stream<String?> get authStateChanges => _mock.authStateChanges;

  @override
  Future<String?> getToken() => _mock.getToken();

  @override
  Future<void> signIn(String provider) => _mock.signIn(provider);

  @override
  Future<void> signOut() => _mock.signOut();
}
