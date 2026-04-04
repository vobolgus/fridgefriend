import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

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
