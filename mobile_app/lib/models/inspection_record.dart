class InspectionRecord {
  final String clientRecordId;
  final String lotId;
  final String diseaseLabel;
  final String commonName;
  final String causalAgent;
  final double confidence;
  final double severityIndex;
  final String riskLevel;
  final String mipRecommendation;
  final double latitude;
  final double longitude;
  final DateTime capturedAt;
  final String modelVersion;
  bool isSynced;

  InspectionRecord({
    required this.clientRecordId,
    required this.lotId,
    required this.diseaseLabel,
    required this.commonName,
    required this.causalAgent,
    required this.confidence,
    required this.severityIndex,
    required this.riskLevel,
    required this.mipRecommendation,
    required this.latitude,
    required this.longitude,
    required this.capturedAt,
    required this.modelVersion,
    this.isSynced = false,
  });

  Map<String, dynamic> toSyncJson() {
    return {
      'client_record_id': clientRecordId,
      'lot_id': lotId,
      'disease_label': diseaseLabel,
      'confidence': confidence,
      'severity_index': severityIndex,
      'latitude': latitude,
      'longitude': longitude,
      'captured_at': capturedAt.toUtc().toIso8601String(),
      'model_version': modelVersion,
    };
  }
}
