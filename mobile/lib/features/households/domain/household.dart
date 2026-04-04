class HouseholdMember {
  const HouseholdMember({
    required this.id,
    required this.userId,
    required this.email,
    required this.role,
  });

  final String id;
  final String userId;
  final String email;
  final String role;

  factory HouseholdMember.fromJson(Map<String, dynamic> json) {
    return HouseholdMember(
      id: (json['id'] ?? '').toString(),
      userId: (json['user_id'] ?? json['userId'] ?? '').toString(),
      email: (json['email'] ?? '').toString(),
      role: (json['role'] ?? 'member').toString(),
    );
  }
}

class Household {
  const Household({
    required this.id,
    required this.name,
    required this.inviteCode,
    required this.members,
  });

  final String id;
  final String name;
  final String inviteCode;
  final List<HouseholdMember> members;

  factory Household.fromJson(Map<String, dynamic> json) {
    final rawMembers = json['members'] as List<dynamic>? ?? const [];
    return Household(
      id: (json['id'] ?? '').toString(),
      name: (json['name'] ?? '').toString(),
      inviteCode: (json['invite_code'] ?? json['inviteCode'] ?? '').toString(),
      members: rawMembers
          .whereType<Map<String, dynamic>>()
          .map(HouseholdMember.fromJson)
          .toList(growable: false),
    );
  }
}
