import 'dart:math';
import '../config/app_config.dart';

/// Servicio de Geolocalización GPS Offline para los Lotes Arroceros del Tolima.
class ServicioGps {
  final Random _generador = Random(42);

  Map<String, double> capturarCoordenadasLoteActual(String idLote) {
    final lote = ConfiguracionApp.lotesTolima.firstWhere(
      (elemento) => elemento['id'] == idLote,
      orElse: () => ConfiguracionApp.lotesTolima.first,
    );
    final double latBase = (lote['latitud'] as num).toDouble();
    final double lonBase = (lote['longitud'] as num).toDouble();

    final double variacionLat = (_generador.nextDouble() - 0.5) * 0.008;
    final double variacionLon = (_generador.nextDouble() - 0.5) * 0.008;

    return {
      'latitud': double.parse((latBase + variacionLat).toStringAsFixed(6)),
      'longitud': double.parse((lonBase + variacionLon).toStringAsFixed(6)),
      'precision_m': 3.2,
    };
  }
}

typedef GpsService = ServicioGps;
