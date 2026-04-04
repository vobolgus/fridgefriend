import 'package:flutter_test/flutter_test.dart';

import 'package:fridgefriend_mobile/core/network/api_client.dart';
import 'package:fridgefriend_mobile/features/households/data/sse_client.dart';

void main() {
  test('parses sse data frame into household event', () {
    final client = HouseholdSseClient(ApiClient(baseUrl: 'https://example.test'));

    final event = client.parseFrame(
      'data: {"action":"added","item_id":"item-1","created_at":"2026-04-04T09:00:00Z"}\n\n',
    );

    expect(event, isNotNull);
    expect(event!.data['action'], 'added');
    expect(event.data['item_id'], 'item-1');
  });

  test('ignores keep-alive comments', () {
    final client = HouseholdSseClient(ApiClient(baseUrl: 'https://example.test'));

    final event = client.parseFrame(': keep-alive\n\n');

    expect(event, isNull);
  });
}
