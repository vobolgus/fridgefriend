abstract class AuthService {
  Future<void> signIn(String provider);
  Future<void> signInWithEmail(String email, String password);
  Future<void> signOut();
  Future<String?> getToken();
  Stream<String?> get authStateChanges;
}
