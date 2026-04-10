import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fridgefriend_mobile/features/households/data/sse_client.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart'; // api client provider
import '../data/household_repository.dart';
import '../domain/household.dart';

final householdRepositoryProvider = Provider<HouseholdRepository>((ref) {
  return HouseholdRepositoryImpl(ref.watch(apiClientProvider));
});

final householdSseClientProvider = Provider<HouseholdSseClient>((ref) {
  return HouseholdSseClient(ref.watch(apiClientProvider));
});

final householdsProvider = FutureProvider<List<Household>>((ref) {
  return ref.watch(householdRepositoryProvider).getHouseholds();
});

final activityLogProvider =
    FutureProvider.family<List<Map<String, dynamic>>, String>(
        (ref, householdId) {
  return ref.watch(apiClientProvider).getActivityLog(householdId);
});

final householdEventsProvider =
    StreamProvider.autoDispose.family<HouseholdSseEvent, String>(
  (ref, householdId) {
    final stream = ref.watch(householdSseClientProvider).connect(householdId);
    final controller = StreamController<HouseholdSseEvent>();
    final subscription = stream.listen(
      controller.add,
      onError: controller.addError,
      onDone: () {
        if (!controller.isClosed) {
          controller.close();
        }
      },
    );

    ref.onDispose(() {
      subscription.cancel();
      if (!controller.isClosed) {
        controller.close();
      }
    });

    return controller.stream;
  },
);
