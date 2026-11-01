/// Configuración central de la aplicación móvil PlagIA Tolima.
///
/// Aplica la Regla de Oro:
/// - Identificadores, constantes y lotes internos en español (`ConfiguracionApp`, `lotesTolima`).
/// - URL del contrato HTTP hacia el backend FastAPI en inglés (`/api/v1`).
class ConfiguracionApp {
  static const String tituloApp = 'PlagIA Tolima Empresarial';
  static const String versionModelo = '1.0.0-edge-int8';
  static const String idDispositivo = 'ANDROID-TOLIMA-CAMPO-01';

  /// IP especial del Emulador de Android Studio que redirige al localhost del host
  static String urlBaseApi = 'http://10.0.2.2:8000/api/v1';

  static const List<Map<String, dynamic>> lotesTolima = [
    {
      'id': 'LOTE-ESPINAL-01',
      'nombre': 'Lote Las Acacias - El Espinal (Usocoello)',
      'variedad': 'Fedearroz 67',
      'latitud': 4.1486,
      'longitud': -74.8830,
    },
    {
      'id': 'LOTE-SALDANA-01',
      'nombre': 'Lote El Canal - Saldaña (Usosaldaña)',
      'variedad': 'Fedearroz 2000',
      'latitud': 3.9317,
      'longitud': -75.0153,
    },
  ];
}

typedef AppConfig = ConfiguracionApp;
