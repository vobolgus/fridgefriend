import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import 'package:fridgefriend_mobile/core/design/colors.dart';
import 'package:fridgefriend_mobile/core/design/spacing.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/error_view.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/loading_view.dart';
import 'package:fridgefriend_mobile/core/presentation/widgets/app_bar.dart';
import 'package:fridgefriend_mobile/features/auth/presentation/providers.dart';
import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

class PhotoUploadScreen extends ConsumerStatefulWidget {
  const PhotoUploadScreen({super.key});

  @override
  ConsumerState<PhotoUploadScreen> createState() => _PhotoUploadScreenState();
}

class _PhotoUploadScreenState extends ConsumerState<PhotoUploadScreen> {
  final ImagePicker _picker = ImagePicker();
  bool _isUploading = false;
  String? _error;

  Future<void> _pickImage(ImageSource source) async {
    try {
      final XFile? image = await _picker.pickImage(source: source);
      if (image == null) return;

      setState(() {
        _isUploading = true;
        _error = null;
      });

      final apiClient = ref.read(apiClientProvider);

      // Step 1: Upload image to get a signed URL
      final imageUrl = await apiClient.uploadPhoto(image.path);

      // Step 2: Send the URL to the scan endpoint for AI parsing
      final draftItems = await apiClient.scanPhoto(imageUrl);
      unawaited(
        ref.read(analyticsProvider).track(
          'photo_uploaded',
          payload: {
            'source': source.name,
            'draft_item_count': draftItems.length,
          },
        ),
      );

      if (mounted) {
        context.pushReplacement(
          '/scan/photo/review',
          extra: {'draft_items': draftItems},
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _isUploading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: const FridgeFriendAppBar(title: 'Scan Photo'),
      body: _isUploading
          ? const LoadingView(message: 'Analyzing fridge contents...')
          : _error != null
              ? ErrorView(
                  message: _error!,
                  onRetry: () => setState(() => _error = null))
              : Padding(
                  padding: AppSpacing.screenPadding,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const Text(
                        'Add via Photo',
                        style: TextStyle(
                            fontFamily: 'Inter',
                            fontSize: 32,
                            fontWeight: FontWeight.w900,
                            color: AppColors.textPrimary),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      const Text(
                        'Snap your fridge or receipt to add items instantly using AI.',
                        style: TextStyle(
                            fontFamily: 'Inter',
                            fontSize: 16,
                            color: AppColors.textSecondary,
                            fontWeight: FontWeight.w500),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: AppSpacing.xxxl),
                      Row(
                        children: [
                          Expanded(
                            child: GestureDetector(
                              onTap: () => _pickImage(ImageSource.camera),
                              child: Container(
                                height: 180,
                                decoration: BoxDecoration(
                                  color: AppColors.primary,
                                  borderRadius: BorderRadius.circular(
                                      AppSpacing.cardRadius),
                                  boxShadow: [
                                    BoxShadow(
                                        color:
                                            AppColors.primary.withOpacity(0.3),
                                        blurRadius: 16,
                                        offset: const Offset(0, 8))
                                  ],
                                ),
                                child: const Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Icon(Icons.camera_alt_rounded,
                                        color: Colors.white, size: 56),
                                    SizedBox(height: AppSpacing.md),
                                    Text('Camera',
                                        style: TextStyle(
                                            fontFamily: 'Inter',
                                            color: Colors.white,
                                            fontWeight: FontWeight.w800,
                                            fontSize: 20)),
                                  ],
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(width: AppSpacing.lg),
                          Expanded(
                            child: GestureDetector(
                              onTap: () => _pickImage(ImageSource.gallery),
                              child: Container(
                                height: 180,
                                decoration: BoxDecoration(
                                  color: AppColors.secondary,
                                  borderRadius: BorderRadius.circular(
                                      AppSpacing.cardRadius),
                                  boxShadow: [
                                    BoxShadow(
                                        color: AppColors.secondary
                                            .withOpacity(0.3),
                                        blurRadius: 16,
                                        offset: const Offset(0, 8))
                                  ],
                                ),
                                child: const Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Icon(Icons.photo_library_rounded,
                                        color: Colors.white, size: 56),
                                    SizedBox(height: AppSpacing.md),
                                    Text('Gallery',
                                        style: TextStyle(
                                            fontFamily: 'Inter',
                                            color: Colors.white,
                                            fontWeight: FontWeight.w800,
                                            fontSize: 20)),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
    );
  }
}
