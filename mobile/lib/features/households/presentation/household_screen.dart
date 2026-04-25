import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:fridgefriend_mobile/core/design/colors.dart';
import 'package:fridgefriend_mobile/core/design/spacing.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/empty_state.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/error_view.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/loading_view.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/app_bar.dart';
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
    final cs = Theme.of(context).colorScheme;
    final householdsAsync = ref.watch(householdsProvider);

    return Scaffold(
      appBar: const FridgeFriendAppBar(title: 'Households'),
      body: householdsAsync.when(
        data: (households) {
          if (households.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const EmptyState(
                    icon: Icons.people_outlined,
                    title: 'No households yet',
                    subtitle:
                        'Create or join a household to share inventory and plan meals together.',
                  ),
                  const SizedBox(height: AppSpacing.xl),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      FilledButton.tonal(
                        onPressed: () {
                          HapticFeedback.mediumImpact();
                          _showCreateDialog(context, ref);
                        },
                        style: FilledButton.styleFrom(
                          minimumSize: const Size(0, 52),
                          textStyle: const TextStyle(
                            fontFamily: 'Inter',
                            fontWeight: FontWeight.w800,
                          ),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 24, vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius:
                                BorderRadius.circular(AppSpacing.buttonRadius),
                          ),
                        ),
                        child: const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.add_home_rounded),
                            SizedBox(width: 8),
                            Text('Create'),
                          ],
                        ),
                      ),
                      const SizedBox(width: AppSpacing.md),
                      ElevatedButton.icon(
                        onPressed: () {
                          HapticFeedback.mediumImpact();
                          _showJoinDialog(context, ref);
                        },
                        icon: const Icon(Icons.group_add_rounded),
                        label: const Text('Join'),
                        style: ElevatedButton.styleFrom(
                          minimumSize: const Size(0, 52),
                          backgroundColor: AppColors.primary,
                          foregroundColor: AppColors.textOnPrimary,
                          textStyle: const TextStyle(
                            fontFamily: 'Inter',
                            fontWeight: FontWeight.w800,
                          ),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 24, vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius:
                                BorderRadius.circular(AppSpacing.buttonRadius),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            );
          }

          return ListView(
            padding: AppSpacing.screenPadding,
            children: [
              Row(
                children: [
                  Expanded(
                    child: FilledButton(
                      onPressed: () {
                        HapticFeedback.mediumImpact();
                        _showCreateDialog(context, ref);
                      },
                      style: FilledButton.styleFrom(
                        elevation: 0,
                        textStyle: const TextStyle(
                          fontFamily: 'Inter',
                          fontWeight: FontWeight.w800,
                        ),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius:
                              BorderRadius.circular(AppSpacing.buttonRadius),
                        ),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.add_home_rounded, size: 20),
                          SizedBox(width: 8),
                          Text('Create'),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.sm),
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: () {
                        HapticFeedback.mediumImpact();
                        _showJoinDialog(context, ref);
                      },
                      icon: const Icon(Icons.group_add_rounded, size: 20),
                      label: const Text('Join'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: cs.primaryContainer,
                        foregroundColor: cs.onPrimaryContainer,
                        elevation: 0,
                        textStyle: const TextStyle(
                          fontFamily: 'Inter',
                          fontWeight: FontWeight.w800,
                        ),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius:
                              BorderRadius.circular(AppSpacing.buttonRadius),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.xl),
              Text(
                'YOUR HOUSEHOLDS',
                style: TextStyle(
                  fontFamily: 'Inter',
                  fontWeight: FontWeight.w900,
                  fontSize: 13,
                  letterSpacing: 1.2,
                  color: cs.onSurfaceVariant,
                ),
              ),
              const SizedBox(height: AppSpacing.md),
              ...households
                  .map((household) => _buildHouseholdCard(context, household)),
            ],
          );
        },
        loading: () => const LoadingView(message: 'Loading households...'),
        error: (err, stack) => ErrorView(message: 'Error: $err'),
      ),
    );
  }

  Widget _buildHouseholdCard(BuildContext context, Household household) {
    final cs = Theme.of(context).colorScheme;
    final isActive = household.isActive;

    return Container(
      margin: const EdgeInsets.only(bottom: AppSpacing.lg),
      decoration: BoxDecoration(
        color: isActive ? cs.primaryContainer : cs.surface,
        borderRadius: BorderRadius.circular(AppSpacing.cardRadius),
        border: Border.all(
          color: isActive ? cs.primary : cs.outlineVariant,
          width: isActive ? 2 : 1,
        ),
        boxShadow: [
          BoxShadow(
            color: cs.shadow.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            household.name,
                            style: TextStyle(
                              fontFamily: 'Inter',
                              fontWeight: FontWeight.w900,
                              fontSize: 20,
                              color: cs.onSurface,
                            ),
                          ),
                          if (isActive) ...[
                            const SizedBox(width: AppSpacing.sm),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: cs.primary,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                'ACTIVE',
                                style: TextStyle(
                                  fontFamily: 'Inter',
                                  fontWeight: FontWeight.w900,
                                  fontSize: 10,
                                  color: cs.onPrimary,
                                  letterSpacing: 0.5,
                                ),
                              ),
                            ),
                          ]
                        ],
                      ),
                      const SizedBox(height: AppSpacing.xs),
                      Text(
                        '${household.members.length} members',
                        style: TextStyle(
                          fontFamily: 'Inter',
                          fontWeight: FontWeight.w600,
                          fontSize: 14,
                          color: cs.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
                if (!isActive)
                  FilledButton(
                    onPressed: _switchingHouseholdId == household.id
                        ? null
                        : () {
                            HapticFeedback.mediumImpact();
                            _setActiveHousehold(household);
                          },
                    style: FilledButton.styleFrom(
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius:
                            BorderRadius.circular(AppSpacing.buttonRadius),
                      ),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 12),
                    ),
                    child: _switchingHouseholdId == household.id
                        ? SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: cs.onPrimary,
                            ),
                          )
                        : const Text(
                            'Switch',
                            style: TextStyle(
                              fontFamily: 'Inter',
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                  ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.lg, vertical: AppSpacing.md),
            decoration: BoxDecoration(
              color: isActive
                  ? cs.surface.withValues(alpha: 0.5)
                  : cs.surfaceContainerHigh,
              border: Border(
                top: BorderSide(
                    color: isActive
                        ? cs.primary.withValues(alpha: 0.2)
                        : cs.outlineVariant),
                bottom: BorderSide(
                    color: isActive
                        ? cs.primary.withValues(alpha: 0.2)
                        : cs.outlineVariant),
              ),
            ),
            child: Row(
              children: [
                Text(
                  'Invite Code:',
                  style: TextStyle(
                    fontFamily: 'Inter',
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                    color: cs.onSurfaceVariant,
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: GestureDetector(
                    onTap: () {
                      Clipboard.setData(
                          ClipboardData(text: household.inviteCode));
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                            content: Text('Invite code copied to clipboard')),
                      );
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: cs.surface,
                        borderRadius:
                            BorderRadius.circular(AppSpacing.chipRadius),
                        border: Border.all(color: cs.outlineVariant),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            household.inviteCode,
                            style: TextStyle(
                              fontFamily: 'Inter',
                              fontWeight: FontWeight.w800,
                              fontSize: 14,
                              color: cs.onSurface,
                            ),
                          ),
                          const SizedBox(width: AppSpacing.xs),
                          Icon(Icons.copy_rounded,
                              size: 14, color: cs.onSurfaceVariant),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: household.members.map((member) {
                        final initial = member.email.isNotEmpty
                            ? member.email[0].toUpperCase()
                            : '?';
                        return Container(
                          margin: const EdgeInsets.only(right: AppSpacing.xs),
                          width: 36,
                          height: 36,
                          decoration: BoxDecoration(
                            color: AppColors.primaryDark,
                            shape: BoxShape.circle,
                            border: Border.all(color: cs.surface, width: 2),
                          ),
                          alignment: Alignment.center,
                          child: Text(
                            initial,
                            style: const TextStyle(
                              fontFamily: 'Inter',
                              fontWeight: FontWeight.w800,
                              fontSize: 14,
                              color: AppColors.textOnPrimary,
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ),
                TextButton.icon(
                  onPressed: () {
                    context.pushNamed(
                      'activity-log',
                      extra: household.id,
                    );
                  },
                  icon: const Icon(Icons.history_rounded, size: 18),
                  label: const Text('Activity'),
                  style: TextButton.styleFrom(
                    foregroundColor: cs.onSurface,
                    textStyle: const TextStyle(
                      fontFamily: 'Inter',
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _setActiveHousehold(Household household) async {
    setState(() {
      _switchingHouseholdId = household.id;
    });

    try {
      if (!await _flushOrWarnPendingMutations()) return;
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

  Future<bool> _flushOrWarnPendingMutations() async {
    final syncManager = ref.read(syncManagerProvider);
    final pending = await syncManager.pendingMutations();
    if (pending.isEmpty) return true;
    try {
      await syncManager.flushPendingMutations();
    } catch (_) {
      // flush threw — fall through to remaining check
    }
    final remaining = await syncManager.pendingMutations();
    if (remaining.isNotEmpty) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content:
                  Text('Sync pending changes before switching households')),
        );
      }
      return false;
    }
    return true;
  }

  Future<void> _clearHouseholdCaches() async {
    final db = ref.read(appDatabaseProvider);
    await db.inventoryDao.clearAll();
    await db.recipeDao.clear();
    await db.mealPlanDao.clear();
  }

  void _invalidateHouseholdScopedProviders() {
    ref.invalidate(householdsProvider);
    ref.invalidate(inventory_providers.inventoryProvider);
    ref.invalidate(inventory_providers.recommendationsProvider);
    ref.invalidate(inventory_providers.mealPlanProvider);
    ref.invalidate(inventory_providers.shoppingListProvider);
  }

  void _showCreateDialog(BuildContext context, WidgetRef ref) {
    final cs = Theme.of(context).colorScheme;
    final controller = TextEditingController();
    final formKey = GlobalKey<FormState>();
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppSpacing.cardRadius)),
        title: Text(
          'Create Household',
          style: TextStyle(
              fontFamily: 'Inter',
              fontWeight: FontWeight.w900,
              color: cs.onSurface),
        ),
        content: Form(
          key: formKey,
          autovalidateMode: AutovalidateMode.onUserInteraction,
          child: TextFormField(
            controller: controller,
            decoration: InputDecoration(
              hintText: 'Household name',
              hintStyle: TextStyle(
                  fontFamily: 'Inter',
                  color: cs.onSurfaceVariant.withValues(alpha: 0.5)),
              filled: true,
              fillColor: cs.surfaceContainerHigh,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(AppSpacing.inputRadius),
                borderSide: BorderSide.none,
              ),
            ),
            style: const TextStyle(
                fontFamily: 'Inter', fontWeight: FontWeight.w600),
            validator: (value) => (value == null || value.trim().isEmpty)
                ? 'Household name is required'
                : null,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancel',
                style: TextStyle(
                    fontFamily: 'Inter', fontWeight: FontWeight.w700)),
          ),
          ElevatedButton(
            onPressed: () async {
              HapticFeedback.mediumImpact();
              if (!formKey.currentState!.validate()) return;
              final name = controller.text.trim();
              if (name.isEmpty) return;
              Navigator.pop(dialogContext);
              try {
                if (!await _flushOrWarnPendingMutations()) return;
                await ref
                    .read(householdRepositoryProvider)
                    .createHousehold(name);
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
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: AppColors.textOnPrimary,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(AppSpacing.buttonRadius)),
            ),
            child: const Text('Create',
                style: TextStyle(
                    fontFamily: 'Inter', fontWeight: FontWeight.w800)),
          ),
        ],
      ),
    );
  }

  void _showJoinDialog(BuildContext context, WidgetRef ref) {
    final cs = Theme.of(context).colorScheme;
    final controller = TextEditingController();
    final formKey = GlobalKey<FormState>();
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppSpacing.cardRadius)),
        title: Text(
          'Join Household',
          style: TextStyle(
              fontFamily: 'Inter',
              fontWeight: FontWeight.w900,
              color: cs.onSurface),
        ),
        content: Form(
          key: formKey,
          autovalidateMode: AutovalidateMode.onUserInteraction,
          child: TextFormField(
            controller: controller,
            decoration: InputDecoration(
              hintText: 'Invite Code',
              hintStyle: TextStyle(
                  fontFamily: 'Inter',
                  color: cs.onSurfaceVariant.withValues(alpha: 0.5)),
              filled: true,
              fillColor: cs.surfaceContainerHigh,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(AppSpacing.inputRadius),
                borderSide: BorderSide.none,
              ),
            ),
            style: const TextStyle(
                fontFamily: 'Inter', fontWeight: FontWeight.w600),
            validator: (value) => (value == null || value.trim().isEmpty)
                ? 'Invite code is required'
                : null,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancel',
                style: TextStyle(
                    fontFamily: 'Inter', fontWeight: FontWeight.w700)),
          ),
          ElevatedButton(
            onPressed: () async {
              HapticFeedback.mediumImpact();
              if (!formKey.currentState!.validate()) return;
              final code = controller.text.trim();
              if (code.isEmpty) return;
              Navigator.pop(dialogContext);
              try {
                if (!await _flushOrWarnPendingMutations()) return;
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
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: AppColors.textOnPrimary,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(AppSpacing.buttonRadius)),
            ),
            child: const Text('Join',
                style: TextStyle(
                    fontFamily: 'Inter', fontWeight: FontWeight.w800)),
          ),
        ],
      ),
    );
  }
}
