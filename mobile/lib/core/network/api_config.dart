class ApiConfig {
  const ApiConfig._();

  static const String defaultBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://api.fridgefriend.lat',
  );
  static const String apiVersionPath = '/v1';
}
