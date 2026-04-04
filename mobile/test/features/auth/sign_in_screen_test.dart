import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fridgefriend_mobile/features/auth/presentation/sign_in_screen.dart';
import 'package:go_router/go_router.dart';

void main() {
  testWidgets('SignInScreen shows email and google sign in buttons', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(
          home: SignInScreen(),
        ),
      ),
    );

    expect(find.text('FridgeFriend'), findsOneWidget);
    expect(find.text('Sign in with Email'), findsOneWidget);
    expect(find.text('Sign in with Google'), findsOneWidget);
  });
}
