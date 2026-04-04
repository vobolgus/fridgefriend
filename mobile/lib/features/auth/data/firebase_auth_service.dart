import 'dart:async';
import 'package:firebase_auth/firebase_auth.dart' as fb;
import '../domain/auth_service.dart';

class FirebaseAuthService implements AuthService {
  FirebaseAuthService({fb.FirebaseAuth? firebaseAuth})
      : _auth = firebaseAuth ?? fb.FirebaseAuth.instance;

  final fb.FirebaseAuth _auth;

  @override
  Stream<String?> get authStateChanges {
    return _auth.authStateChanges().asyncMap((user) async {
      if (user == null) return null;
      return await user.getIdToken();
    });
  }

  @override
  Future<String?> getToken() async {
    final user = _auth.currentUser;
    if (user == null) return null;
    return await user.getIdToken();
  }

  @override
  Future<void> signIn(String provider) async {
    switch (provider) {
      case 'google':
        await _auth.signInWithProvider(fb.GoogleAuthProvider());
      case 'apple':
        await _auth.signInWithProvider(fb.AppleAuthProvider());
      default:
        throw ArgumentError('Unknown auth provider: $provider. Use signInWithEmail for email auth.');
    }
  }

  @override
  Future<void> signInWithEmail(String email, String password) async {
    try {
      await _auth.signInWithEmailAndPassword(email: email, password: password);
    } on fb.FirebaseAuthException catch (e) {
      if (e.code == 'user-not-found') {
        await _auth.createUserWithEmailAndPassword(email: email, password: password);
      } else {
        rethrow;
      }
    }
  }

  @override
  Future<void> signOut() async {
    await _auth.signOut();
  }
}
