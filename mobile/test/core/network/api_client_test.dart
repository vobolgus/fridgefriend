import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fridgefriend_mobile/core/network/api_client.dart';

void main() {
  group('ApiClient', () {
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
      expect(capturedOptions.path, '/v1/scan/photo');
      expect(capturedOptions.data, {'image_url': 'mock://photo.jpg'});
      expect(items, hasLength(1));
      expect(items.first.displayName, 'Spinach');
      expect(items.first.storageLocation, 'fridge');
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
