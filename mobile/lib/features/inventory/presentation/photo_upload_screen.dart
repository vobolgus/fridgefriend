import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

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
      final imageUrl = image.path;
      final draftItems = await apiClient.scanPhoto(imageUrl);
      
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
      appBar: AppBar(title: const Text('Scan Photo')),
      body: Center(
        child: _isUploading
            ? const Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text('Analyzing fridge contents...'),
                ],
              )
            : Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (_error != null) ...[
                    Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Text(
                        'Error: $_error',
                        style: const TextStyle(color: Colors.red),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    ElevatedButton(
                      onPressed: () => setState(() => _error = null),
                      child: const Text('Try Again'),
                    ),
                    const SizedBox(height: 32),
                  ],
                  ElevatedButton.icon(
                    onPressed: () => _pickImage(ImageSource.camera),
                    icon: const Icon(Icons.camera_alt),
                    label: const Text('Take Photo'),
                    style: ElevatedButton.styleFrom(
                      minimumSize: const Size(200, 48),
                    ),
                  ),
                  const SizedBox(height: 16),
                  OutlinedButton.icon(
                    onPressed: () => _pickImage(ImageSource.gallery),
                    icon: const Icon(Icons.photo_library),
                    label: const Text('Upload from Gallery'),
                    style: OutlinedButton.styleFrom(
                      minimumSize: const Size(200, 48),
                    ),
                  ),
                ],
              ),
      ),
    );
  }
}
