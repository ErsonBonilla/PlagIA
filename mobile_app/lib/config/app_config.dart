/// Configuración central de la aplicación móvil PlagIA Tolima.
///
/// Incluye soporte nativo para el puente del Emulador de Android Studio (`10.0.2.2:8000`)
/// hacia el Backend Empresarial FastAPI que se ejecuta en WSL 2 / Windows.
class AppConfig {
  static const String appTitle = 'PlagIA Tolima Enterprise';
  static const String modelVersion = '1.0.0-edge-int8';
  static const String deviceId = 'ANDROID-TOLIMA-FIELD-01';

  /// IP especial del Emulador de Android Studio que redirige al localhost del host
  static String apiBaseUrl = 'http://10.0.2.2:8000/api/v1';

  static const List<Map<String, dynamic>> tolimaLots = [
    {
      'id': 'LOTE-ESPINAL-01',
      'name': 'Lote Las Acacias - El Espinal (Usocoello)',
      'variety': 'Fedearroz 67',
      'lat': 4.1486,
      'lon': -74.8830,
    },
    {
      'id': 'LOTE-SALDANA-01',
      'name': 'Lote El Canal - Saldaña (Usosaldaña)',
      'variety': 'Fedearroz 2000',
      'lat': 3.9317,
      'lon': -75.0153,
    },
  ];
}
