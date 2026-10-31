import 'dart:math';
import '../config/app_config.dart';

/// Servicio de Geolocalización GPS Offline para los Lotes Arroceros del Tolima.
class GpsService {
  final Random _rng = Random(42);

  Map<String, double> captureCurrentLotCoordinates(String lotId) {
    final lot = AppConfig.tolimaLots.firstWhere(
      (element) => element['id'] == lotId,
      orElse: () => AppConfig.tolimaLots.first,
    );
    final double baseLat = (lot['lat'] as num).toDouble();
    final double baseLon = (lot['lon'] as num).toDouble();

    final double jitterLat = (_rng.nextDouble() - 0.5) * 0.008;
    final double jitterLon = (_rng.nextDouble() - 0.5) * 0.008;

    return {
      'latitude': double.parse((baseLat + jitterLat).toStringAsFixed(6)),
      'longitude': double.parse((baseLon + jitterLon).toStringAsFixed(6)),
      'accuracy_m': 3.2,
    };
  }
}
