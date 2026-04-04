import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fridgefriend_mobile/core/network/api_client.dart';

void main() {
  group('ApiClient', () {
    test('createInventoryItem sends scan metadata fields when provided', () async {
      late RequestOptions capturedOptions;
      final adapter = _RecordingAdapter((options) {
        capturedOptions = options;
        return {
          'item_id': 'item-123',
          'display_name': 'Yogurt',
          'quantity': 1,
          'unit': 'cup',
          'storage_location': 'fridge',
          'estimated_expiry_date': '2026-04-10T00:00:00Z',
          'confidence': 0.87,
          'source': 'barcode',
          'canonical_name': 'Greek Yogurt',
          'canonical_ingredient_id': 'ingredient-1',
        };
      });

      final client = ApiClient(baseUrl: 'https://example.test');
      client.rawClient.httpClientAdapter = adapter;

      final item = await client.createInventoryItem(
        displayName: 'Yogurt',
        quantity: 1,
        unit: 'cup',
        storageLocation: 'fridge',
        source: 'barcode',
        canonicalName: 'Greek Yogurt',
        canonicalIngredientId: 'ingredient-1',
        confidence: 0.87,
        estimatedExpiryDate: DateTime.parse('2026-04-10T00:00:00Z'),
      );

      expect(capturedOptions.path, '/v1/items');
      expect(capturedOptions.data, {
        'display_name': 'Yogurt',
        'quantity': 1.0,
        'unit': 'cup',
        'storage_location': 'fridge',
        'source': 'barcode',
        'canonical_name': 'Greek Yogurt',
        'canonical_ingredient_id': 'ingredient-1',
        'confidence': 0.87,
        'estimated_expiry_date': '2026-04-10T00:00:00.000Z',
      });
      expect(item.source, 'barcode');
      expect(item.canonicalName, 'Greek Yogurt');
      expect(item.canonicalIngredientId, 'ingredient-1');
    });

    test('uses token provider and posts barcode payload', () async {
      late RequestOptions capturedOptions;
      final adapter = _RecordingAdapter((options) {
        capturedOptions = options;
        return {
          'item_id': 'item-1',
          'display_name': 'Milk',
          'quantity': 1,
          'unit': 'bottle',
          'storage_location': 'fridge',
          'estimated_expiry_date': '2026-04-10T00:00:00Z',
          'confidence': 0.91,
        };
      });

      final client = ApiClient(
        baseUrl: 'https://example.test',
        tokenProvider: () async => 'firebase-token',
      );
      client.rawClient.httpClientAdapter = adapter;

      final item = await client.scanBarcode('0123456789');

      expect(capturedOptions.headers['Authorization'], 'Bearer firebase-token');
      expect(
        (capturedOptions.headers['Idempotency-Key'] as String)
            .startsWith('barcode_scan_'),
        isTrue,
      );
      expect(capturedOptions.path, '/v1/scan/barcode');
      expect(capturedOptions.data, {
        'barcode': '0123456789',
        'quantity': 1,
        'storage_location': 'fridge',
      });
      expect(item.displayName, 'Milk');
      expect(item.storageLocation, 'fridge');
    });

    test('falls back to test token and parses draft_items aliases', () async {
      late RequestOptions capturedOptions;
      final adapter = _RecordingAdapter((options) {
        capturedOptions = options;
        return {
          'draft_items': [
            {
              'item_id': 'draft-1',
              'display_name': 'Spinach',
              'quantity': 2,
              'unit': 'bags',
              'storage_location': 'fridge',
              'estimated_expiry_date': '2026-04-08T00:00:00Z',
              'confidence': 0.75,
            },
          ],
        };
      });

      final client = ApiClient(
        baseUrl: 'https://example.test',
        tokenProvider: () async => null,
        fallbackToken: 'test-token',
      );
      client.rawClient.httpClientAdapter = adapter;

      final items = await client.scanPhoto('mock://photo.jpg');

      expect(capturedOptions.headers['Authorization'], 'Bearer test-token');
      expect(
        (capturedOptions.headers['Idempotency-Key'] as String)
            .startsWith('photo_scan_'),
        isTrue,
      );
      expect(capturedOptions.path, '/v1/scan/photo');
      expect(capturedOptions.data, {'image_url': 'mock://photo.jpg'});
      expect(items, hasLength(1));
      expect(items.first.displayName, 'Spinach');
      expect(items.first.storageLocation, 'fridge');
    });

    test('uploadPhoto sends idempotency key header', () async {
      final tmpFile = File('${Directory.systemTemp.path}/upload_test_${DateTime.now().millisecondsSinceEpoch}.txt');
      tmpFile.writeAsStringSync('test');

      late RequestOptions capturedOptions;
      final adapter = _RecordingAdapter((options) {
        capturedOptions = options;
        return {'image_url': 'https://cdn.example.test/image.jpg'};
      });

      final client = ApiClient(baseUrl: 'https://example.test');
      client.rawClient.httpClientAdapter = adapter;

      try {
        final imageUrl = await client.uploadPhoto(tmpFile.path);

        expect(capturedOptions.path, '/v1/scan/photo/upload');
        expect(
          (capturedOptions.headers['Idempotency-Key'] as String).startsWith('upload_'),
          isTrue,
        );
        expect(imageUrl, 'https://cdn.example.test/image.jpg');
      } finally {
        tmpFile.deleteSync();
      }
    });
  });
}

class _RecordingAdapter implements HttpClientAdapter {
  _RecordingAdapter(this._responseFactory);

  final Map<String, dynamic> Function(RequestOptions options) _responseFactory;

  @override
  void close({bool force = false}) {}

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    final body = jsonEncode(_responseFactory(options));
    return ResponseBody.fromString(
      body,
      200,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }
}
