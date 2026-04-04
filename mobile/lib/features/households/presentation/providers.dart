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

final householdEventsProvider = StreamProvider.family<HouseholdSseEvent, String>(
  (ref, householdId) {
    return ref.watch(householdSseClientProvider).connect(householdId);
  },
);
