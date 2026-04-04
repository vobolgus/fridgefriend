import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

import 'package:fridgefriend_mobile/core/design/colors.dart';
import 'package:fridgefriend_mobile/core/design/spacing.dart';
import 'package:fridgefriend_mobile/features/inventory/domain/inventory_item.dart';
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
        HapticFeedback.heavyImpact();
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
      final scannedItem =
          await ref.read(apiClientProvider).scanBarcode(barcode);
      final item = InventoryItem(
        id: scannedItem.id,
        displayName: scannedItem.displayName,
        quantity: scannedItem.quantity,
        unit: scannedItem.unit,
        storageLocation: scannedItem.storageLocation,
        estimatedExpiryDate: scannedItem.estimatedExpiryDate,
        confidence: scannedItem.confidence,
        status: scannedItem.status,
        source: 'barcode',
        canonicalName: scannedItem.canonicalName,
        canonicalIngredientId: scannedItem.canonicalIngredientId,
      );

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
      backgroundColor: Colors.black,
      appBar: AppBar(
        title: const Text('Scan Barcode',
            style: TextStyle(
                fontFamily: 'Inter',
                fontWeight: FontWeight.bold,
                color: Colors.white)),
        backgroundColor: Colors.transparent,
        iconTheme: const IconThemeData(color: Colors.white),
        elevation: 0,
      ),
      extendBodyBehindAppBar: true,
      body: Column(
        children: [
          Expanded(
            child: Stack(
              fit: StackFit.expand,
              children: [
                MobileScanner(
                  controller: controller,
                  onDetect: _onDetect,
                ),
                if (_isLoading)
                  Container(
                    color: Colors.black54,
                    child: const Center(
                      child: CircularProgressIndicator(
                          color: AppColors.primary, strokeWidth: 4),
                    ),
                  ),
              ],
            ),
          ),
          Container(
            padding: EdgeInsets.only(
              left: AppSpacing.screenPadding.left,
              right: AppSpacing.screenPadding.right,
              top: AppSpacing.xl,
              bottom: MediaQuery.of(context).padding.bottom + AppSpacing.xl,
            ),
            decoration: const BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.vertical(
                  top: Radius.circular(AppSpacing.bottomSheetRadius)),
              boxShadow: [
                BoxShadow(
                    color: Colors.black12,
                    blurRadius: 10,
                    offset: Offset(0, -4))
              ],
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Manual Entry',
                  style: TextStyle(
                      fontFamily: 'Inter',
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: AppColors.textPrimary),
                ),
                const SizedBox(height: AppSpacing.md),
                if (_error != null) ...[
                  Container(
                    padding: const EdgeInsets.all(AppSpacing.sm),
                    decoration: BoxDecoration(
                        color: AppColors.errorLight,
                        borderRadius:
                            BorderRadius.circular(AppSpacing.cardRadius)),
                    child: Text(
                      _error!,
                      style: const TextStyle(
                          fontFamily: 'Inter',
                          color: AppColors.error,
                          fontWeight: FontWeight.w600),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.md),
                ],
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _manualController,
                        style: const TextStyle(
                            fontFamily: 'Inter', fontWeight: FontWeight.bold),
                        decoration: InputDecoration(
                          hintText: 'Enter barcode number',
                          hintStyle: const TextStyle(
                              fontFamily: 'Inter',
                              fontWeight: FontWeight.normal),
                          prefixIcon: const Icon(Icons.qr_code,
                              color: AppColors.primary),
                          filled: true,
                          fillColor: AppColors.surfaceVariant,
                          border: OutlineInputBorder(
                            borderRadius:
                                BorderRadius.circular(AppSpacing.inputRadius),
                            borderSide: BorderSide.none,
                          ),
                        ),
                        keyboardType: TextInputType.number,
                      ),
                    ),
                    const SizedBox(width: AppSpacing.md),
                    FilledButton(
                      style: FilledButton.styleFrom(
                        padding: const EdgeInsets.all(16),
                        shape: RoundedRectangleBorder(
                            borderRadius:
                                BorderRadius.circular(AppSpacing.buttonRadius)),
                      ),
                      onPressed: _isLoading
                          ? null
                          : () {
                              final barcode = _manualController.text.trim();
                              if (barcode.isNotEmpty) {
                                _submitBarcode(barcode);
                              }
                            },
                      child: const Icon(Icons.arrow_forward_rounded, size: 28),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
