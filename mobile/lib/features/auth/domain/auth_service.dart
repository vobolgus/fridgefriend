abstract class AuthService {
  Future<void> signIn(String provider);
  Future<void> signOut();
  Future<String?> getToken();
  Stream<String?> get authStateChanges;
}
