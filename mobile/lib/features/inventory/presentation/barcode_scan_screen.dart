import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

import 'package:fridgefriend_mobile/features/inventory/presentation/providers.dart';

class BarcodeScanScreen extends ConsumerStatefulWidget {
  const BarcodeScanScreen({super.key});

  @override
  ConsumerState<BarcodeScanScreen> createState() => _BarcodeScanScreenState();
}

class _BarcodeScanScreenState extends ConsumerState<BarcodeScanScreen> {
  final MobileScannerController controller = MobileScannerController();
  final TextEditingController _manualController = TextEditingController();
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    controller.dispose();
    _manualController.dispose();
    super.dispose();
  }

  void _onDetect(BarcodeCapture capture) {
    final List<Barcode> barcodes = capture.barcodes;
    if (barcodes.isNotEmpty) {
      final barcode = barcodes.first.rawValue;
      if (barcode != null && mounted && !_isLoading) {
        _submitBarcode(barcode);
      }
    }
  }

  Future<void> _submitBarcode(String barcode) async {
    if (_isLoading) {
      return;
    }

    controller.stop();
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final item = await ref.read(apiClientProvider).scanBarcode(barcode);

      if (!mounted) {
        return;
      }

      context.pushReplacement('/add-item', extra: item);
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _error = error.toString();
        _isLoading = false;
      });
      await controller.start();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Scan Barcode'),
      ),
      body: Column(
        children: [
          Expanded(
            flex: 3,
            child: Stack(
              children: [
                MobileScanner(
                  controller: controller,
                  onDetect: _onDetect,
                ),
                if (_isLoading)
                  const ColoredBox(
                    color: Color(0x88000000),
                    child: Center(child: CircularProgressIndicator()),
                  ),
              ],
            ),
          ),
          Expanded(
            flex: 1,
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (_error != null) ...[
                    Text(
                      _error!,
                      style: const TextStyle(color: Colors.red),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                  ],
                  const Text('Or enter manually:'),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _manualController,
                          decoration: const InputDecoration(
                            hintText: 'Barcode number',
                            border: OutlineInputBorder(),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      ElevatedButton(
                        onPressed: _isLoading
                            ? null
                            : () {
                                final barcode = _manualController.text.trim();
                                if (barcode.isNotEmpty) {
                                  _submitBarcode(barcode);
                                }
                              },
                        child: const Text('Submit'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
