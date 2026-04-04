import 'dart:async';
import '../domain/auth_service.dart';

class MockAuthService implements AuthService {
  final _authStateController = StreamController<String?>.broadcast();
  String? _currentToken;

  @override
  Stream<String?> get authStateChanges => _authStateController.stream;

  @override
  Future<String?> getToken() async => _currentToken;

  @override
  Future<void> signIn(String provider) async {
    await Future.delayed(const Duration(milliseconds: 500));
    _currentToken = 'test-token';
    _authStateController.add(_currentToken);
  }

  @override
  Future<void> signInWithEmail(String email, String password) async {
    await Future.delayed(const Duration(milliseconds: 500));
    _currentToken = 'test-token';
    _authStateController.add(_currentToken);
  }

  @override
  Future<void> signOut() async {
    await Future.delayed(const Duration(milliseconds: 500));
    _currentToken = null;
    _authStateController.add(null);
  }
}
