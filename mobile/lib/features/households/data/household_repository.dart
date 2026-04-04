import 'package:fridgefriend_mobile/core/network/api_client.dart';
import '../domain/household.dart';

abstract class HouseholdRepository {
  Future<List<Household>> getHouseholds();
  Future<Household> createHousehold(String name);
  Future<Household> joinHousehold(String inviteCode);
  Future<void> leaveHousehold(String id);
}

class HouseholdRepositoryImpl implements HouseholdRepository {
  HouseholdRepositoryImpl(this._apiClient);
  final ApiClient _apiClient;

  @override
  Future<List<Household>> getHouseholds() => _apiClient.getHouseholds();

  @override
  Future<Household> createHousehold(String name) => _apiClient.createHousehold(name);

  @override
  Future<Household> joinHousehold(String inviteCode) => _apiClient.joinHousehold(inviteCode);

  @override
  Future<void> leaveHousehold(String id) => _apiClient.leaveHousehold(id);
}
