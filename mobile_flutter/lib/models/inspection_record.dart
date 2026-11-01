/// Entidad interna de inspección fitosanitaria georreferenciada.
///
/// Aplica la Regla de Oro:
/// - Propiedades internas de negocio en español.
/// - Claves del contrato JSON en `toSyncJson()` conservadas en inglés para `/api/v1/sync`.
class RegistroInspeccion {
  final String idRegistroCliente;
  final String idLote;
  final String etiquetaEnfermedad;
  final String nombreComun;
  final String agenteCausal;
  final double confianza;
  final double indiceSeveridad;
  final String nivelRiesgo;
  final String recomendacionMip;
  final double latitud;
  final double longitud;
  final DateTime capturadoEn;
  final String versionModelo;
  final int latenciaMs;
  bool sincronizado;

  RegistroInspeccion({
    required this.idRegistroCliente,
    required this.idLote,
    required this.etiquetaEnfermedad,
    required this.nombreComun,
    required this.agenteCausal,
    required this.confianza,
    required this.indiceSeveridad,
    required this.nivelRiesgo,
    required this.recomendacionMip,
    required this.latitud,
    required this.longitud,
    required this.capturadoEn,
    required this.versionModelo,
    this.latenciaMs = 38,
    this.sincronizado = false,
  });

  bool get esFueraDeDominio => etiquetaEnfermedad == 'desconocido_no_arroz';

  /// Serializa al contrato JSON externo esperado por `POST /api/v1/sync`.
  Map<String, dynamic> toSyncJson() {
    return {
      'client_record_id': idRegistroCliente,
      'lot_id': idLote,
      'disease_label': etiquetaEnfermedad,
      'confidence': confianza,
      'severity_index': indiceSeveridad,
      'latitude': latitud,
      'longitude': longitud,
      'captured_at': capturadoEn.toUtc().toIso8601String(),
      'model_version': versionModelo,
    };
  }
}

typedef InspectionRecord = RegistroInspeccion;
