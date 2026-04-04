import 'dart:async';
import 'package:firebase_auth/firebase_auth.dart' as fb;
import '../domain/auth_service.dart';

/// Real Firebase Authentication service.
///
/// Requires Firebase project configuration (GoogleService-Info.plist / google-services.json)
/// and `Firebase.initializeApp()` called before use.
///
/// When `USE_MOCK_AUTH=false` is set at compile time, the app uses this service
/// to authenticate via Firebase email, Google, or Apple sign-in and obtain JWTs.
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
      case 'email':
        // For email sign-in, a separate flow with email/password would be needed.
        // This is a placeholder — the UI should collect credentials and call
        // signInWithEmailAndPassword directly.
        throw UnimplementedError(
          'Email sign-in requires email/password; use signInWithEmailAndPassword flow.',
        );
      case 'google':
        // Google Sign-In requires google_sign_in package integration.
        // The GoogleSignIn flow obtains an idToken + accessToken,
        // then creates a GoogleAuthProvider.credential to sign in.
        await _auth.signInWithProvider(fb.GoogleAuthProvider());
        break;
      case 'apple':
        await _auth.signInWithProvider(fb.AppleAuthProvider());
        break;
      default:
        throw ArgumentError('Unknown auth provider: $provider');
    }
  }

  @override
  Future<void> signOut() async {
    await _auth.signOut();
  }
}
