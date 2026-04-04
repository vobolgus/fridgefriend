import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:dio/dio.dart';

import 'package:fridgefriend_mobile/core/network/api_client.dart';
import 'package:fridgefriend_mobile/core/network/api_config.dart';

class HouseholdSseEvent {
  const HouseholdSseEvent({required this.data, this.eventId});

  final Map<String, dynamic> data;
  final String? eventId;
}

class HouseholdSseClient {
  HouseholdSseClient(this._apiClient, {Random? random})
      : _random = random ?? Random();

  final ApiClient _apiClient;
  final Random _random;

  static const Duration _initialReconnectDelay = Duration(seconds: 1);
  static const Duration _maxReconnectDelay = Duration(seconds: 30);

  Stream<HouseholdSseEvent> connect(String householdId) async* {
    Duration reconnectDelay = _initialReconnectDelay;
    String? lastEventId;

    while (true) {
      try {
        final response = await _apiClient.rawClient.get<ResponseBody>(
          '${ApiConfig.apiVersionPath}/households/$householdId/events',
          options: Options(
            responseType: ResponseType.stream,
            headers: {
              if (lastEventId != null) 'Last-Event-ID': lastEventId,
            },
          ),
        );

        reconnectDelay = _initialReconnectDelay;

        final body = response.data;
        if (body == null) {
          return;
        }

        final buffer = StringBuffer();
        await for (final chunk
            in body.stream.cast<List<int>>().transform(utf8.decoder)) {
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
              lastEventId = event.eventId ?? lastEventId;
              yield event;
            }
          }
        }
      } on DioException {
        await Future<void>.delayed(_applyJitter(reconnectDelay));
        reconnectDelay = _nextReconnectDelay(reconnectDelay);
      }
    }
  }

  Duration _nextReconnectDelay(Duration currentDelay) {
    final nextMilliseconds = currentDelay.inMilliseconds * 2;
    if (nextMilliseconds >= _maxReconnectDelay.inMilliseconds) {
      return _maxReconnectDelay;
    }
    return Duration(milliseconds: nextMilliseconds);
  }

  Duration _applyJitter(Duration delay) {
    final factor = 0.75 + (_random.nextDouble() * 0.5);
    return Duration(milliseconds: (delay.inMilliseconds * factor).round());
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

    final idLine = lines.firstWhere(
      (line) => line.startsWith('id:'),
      orElse: () => '',
    );

    final raw = dataLine.substring(5).trim();
    final decoded = jsonDecode(raw);
    if (decoded is! Map<String, dynamic>) {
      return null;
    }

    final eventId = idLine.isEmpty ? '' : idLine.substring(3).trim();
    return HouseholdSseEvent(
      data: decoded,
      eventId: eventId.isEmpty ? null : eventId,
    );
  }
}
