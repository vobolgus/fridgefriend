import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';

import 'package:fridgefriend_mobile/core/network/api_client.dart';
import 'package:fridgefriend_mobile/core/network/api_config.dart';

class HouseholdSseEvent {
  const HouseholdSseEvent({required this.data});

  final Map<String, dynamic> data;
}

class HouseholdSseClient {
  HouseholdSseClient(this._apiClient);

  final ApiClient _apiClient;

  Stream<HouseholdSseEvent> connect(String householdId) async* {
    final response = await _apiClient.rawClient.get<ResponseBody>(
      '${ApiConfig.apiVersionPath}/households/$householdId/events',
      options: Options(responseType: ResponseType.stream),
    );

    final body = response.data;
    if (body == null) {
      return;
    }

    final buffer = StringBuffer();
    await for (final chunk in body.stream.cast<List<int>>().transform(utf8.decoder)) {
      buffer.write(chunk);
      final payload = buffer.toString();
      final frames = payload.split('\n\n');

      if (frames.length < 2) {
        continue;
      }

      buffer
        ..clear()
        ..write(frames.removeLast());

      for (final frame in frames) {
        final event = parseFrame(frame);
        if (event != null) {
          yield event;
        }
      }
    }
  }

  HouseholdSseEvent? parseFrame(String frame) {
    final lines = frame
        .split('\n')
        .map((line) => line.trim())
        .where((line) => line.isNotEmpty && !line.startsWith(':'))
        .toList(growable: false);

    if (lines.isEmpty) {
      return null;
    }

    final dataLine = lines.firstWhere(
      (line) => line.startsWith('data:'),
      orElse: () => '',
    );
    if (dataLine.isEmpty) {
      return null;
    }

    final raw = dataLine.substring(5).trim();
    final decoded = jsonDecode(raw);
    if (decoded is! Map<String, dynamic>) {
      return null;
    }

    return HouseholdSseEvent(data: decoded);
  }
}
