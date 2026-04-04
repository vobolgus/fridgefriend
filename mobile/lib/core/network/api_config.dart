class ApiConfig {
  const ApiConfig._();

  static const String defaultBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );
  static const String apiVersionPath = '/v1';
}
