import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fridgefriend_mobile/features/auth/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/settings/data/push_notification_service.dart';

class NotificationsNotifier extends AsyncNotifier<bool> {
  @override
  Future<bool> build() async {
    final apiClient = ref.watch(apiClientProvider);
    final prefs = await apiClient.getNotificationPreferences();
    return prefs['expiry_reminder_enabled'] as bool? ?? false;
  }

  Future<void> toggle(bool enabled) async {
    state = const AsyncValue.loading();
    try {
      final apiClient = ref.read(apiClientProvider);
      await apiClient.updateNotificationPreferences(expiryReminderEnabled: enabled);
      state = AsyncValue.data(enabled);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}

final notificationsEnabledProvider =
    AsyncNotifierProvider<NotificationsNotifier, bool>(NotificationsNotifier.new);

final pushNotificationServiceProvider = Provider<PushNotificationService>((ref) {
  if (useMockAuth) {
    return MockPushNotificationService();
  }
  return FirebasePushNotificationService();
});

/// Registers the device token with the backend on first access.
/// Watch this provider after sign-in to trigger automatic registration.
final deviceTokenRegistrationProvider = FutureProvider<void>((ref) async {
  final pushService = ref.watch(pushNotificationServiceProvider);
  final apiClient = ref.watch(apiClientProvider);
  await pushService.registerToken(apiClient);
});
