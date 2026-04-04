import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart'
    as inventory_providers;
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart'
    show appDatabaseProvider, syncManagerProvider;

import '../domain/household.dart';
import 'providers.dart';

class HouseholdScreen extends ConsumerStatefulWidget {
  const HouseholdScreen({super.key});

  @override
  ConsumerState<HouseholdScreen> createState() => _HouseholdScreenState();
}

class _HouseholdScreenState extends ConsumerState<HouseholdScreen> {
  String? _switchingHouseholdId;

  @override
  Widget build(BuildContext context) {
    final householdsAsync = ref.watch(householdsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Household Management')),
      body: householdsAsync.when(
        data: (households) {
          if (households.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('You are not in any household.'),
                  const SizedBox(height: 16),
                   ElevatedButton(
                     onPressed: () => _showCreateDialog(context, ref),
                     child: const Text('Create Household'),
                   ),
                   TextButton(
                     onPressed: () => _showJoinDialog(context, ref),
                     child: const Text('Join Household'),
                   ),
                ],
              ),
            );
          }

          return ListView(
            padding: const EdgeInsets.all(16.0),
            children: [
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: Text(
                      'Your Households',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                  ),
                   TextButton.icon(
                     onPressed: () => _showJoinDialog(context, ref),
                     icon: const Icon(Icons.group_add),
                     label: const Text('Join'),
                   ),
                  const SizedBox(width: 8),
                   ElevatedButton.icon(
                     onPressed: () => _showCreateDialog(context, ref),
                     icon: const Icon(Icons.add_home),
                     label: const Text('Create'),
                   ),
                ],
              ),
              const SizedBox(height: 16),
              ...households.map(
                (household) => Card(
                  margin: const EdgeInsets.only(bottom: 16),
                  child: Padding(
                    padding: const EdgeInsets.all(8),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        ListTile(
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 8,
                          ),
                          leading: Icon(
                            household.isActive
                                ? Icons.check_circle
                                : Icons.home_outlined,
                            color: household.isActive
                                ? Theme.of(context).colorScheme.primary
                                : null,
                          ),
                          title: Text(household.name),
                          subtitle: Text(
                            '${household.members.length} members • Invite Code: ${household.inviteCode}',
                          ),
                          trailing: household.isActive
                              ? Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 12,
                                    vertical: 6,
                                  ),
                                  decoration: BoxDecoration(
                                    color: Theme.of(context)
                                        .colorScheme
                                        .primaryContainer,
                                    borderRadius: BorderRadius.circular(999),
                                  ),
                                  child: const Text('Active'),
                                )
                              : FilledButton.tonal(
                                  onPressed: _switchingHouseholdId == household.id
                                      ? null
                                      : () => _setActiveHousehold(household),
                                  child: _switchingHouseholdId == household.id
                                      ? const SizedBox(
                                          width: 16,
                                          height: 16,
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                          ),
                                        )
                                      : const Text('Set Active'),
                                ),
                        ),
                        const Divider(),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          child: Text(
                            'Members',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                        ),
                        ...household.members.map(
                          (member) => ListTile(
                            leading: const Icon(Icons.person),
                            title: Text(member.email),
                            subtitle: Text(member.role),
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.fromLTRB(8, 8, 8, 0),
                          child: Align(
                            alignment: Alignment.centerLeft,
                            child: TextButton.icon(
                              onPressed: () {
                                context.pushNamed(
                                  'activity-log',
                                  extra: household.id,
                                );
                              },
                              icon: const Icon(Icons.history),
                              label: const Text('View Activity'),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
    );
  }

  Future<void> _setActiveHousehold(Household household) async {
    setState(() {
      _switchingHouseholdId = household.id;
    });

    try {
      await ref
          .read(householdRepositoryProvider)
          .setActiveHousehold(household.id);

      await _clearHouseholdCaches();
      _invalidateHouseholdScopedProviders();

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${household.name} is now active')),
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to switch household: $error')),
      );
    } finally {
      if (mounted) {
        setState(() {
          _switchingHouseholdId = null;
        });
      }
    }
  }

  Future<void> _clearHouseholdCaches() async {
    final db = ref.read(appDatabaseProvider);
    await db.inventoryDao.clearAll();
    await db.recipeDao.clear();
    await db.mealPlanDao.clear();

    final syncManager = ref.read(syncManagerProvider);
    await syncManager.clearPendingMutations();
  }

  void _invalidateHouseholdScopedProviders() {
    ref.invalidate(householdsProvider);
    ref.invalidate(inventory_providers.inventoryProvider);
    ref.invalidate(inventory_providers.recommendationsProvider);
    ref.invalidate(inventory_providers.mealPlanProvider);
    ref.invalidate(inventory_providers.shoppingListProvider);
  }

  void _showCreateDialog(BuildContext context, WidgetRef ref) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Create'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(hintText: 'Household name'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              final name = controller.text.trim();
              if (name.isEmpty) return;
              Navigator.pop(dialogContext);
              try {
                await ref.read(householdRepositoryProvider).createHousehold(name);
                await _clearHouseholdCaches();
                _invalidateHouseholdScopedProviders();
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Failed to create: $e')),
                  );
                }
              }
            },
            child: const Text('Create'),
          ),
        ],
      ),
    );
  }

  void _showJoinDialog(BuildContext context, WidgetRef ref) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Join'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(hintText: 'Invite Code'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              final code = controller.text.trim();
              if (code.isEmpty) return;
              Navigator.pop(dialogContext);
              try {
                await ref.read(householdRepositoryProvider).joinHousehold(code);
                await _clearHouseholdCaches();
                _invalidateHouseholdScopedProviders();
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Failed to join: $e')),
                  );
                }
              }
            },
            child: const Text('Join'),
          ),
        ],
      ),
    );
  }
}
