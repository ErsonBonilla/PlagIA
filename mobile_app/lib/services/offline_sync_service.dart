import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';
import '../models/inspection_record.dart';

/// Gestor de Cola Offline-First y Sincronización por Lotes hacia FastAPI (`/api/v1/sync/batch`).
class OfflineSyncService {
  final List<InspectionRecord> _records = [];

  List<InspectionRecord> get allRecords => List.unmodifiable(_records);

  int get pendingCount => _records.where((r) => !r.isSynced).length;

  void enqueueRecord(InspectionRecord record) {
    _records.insert(0, record);
  }

  Future<Map<String, dynamic>> syncPendingRecords() async {
    final pending = _records.where((r) => !r.isSynced).toList();
    if (pending.isEmpty) {
      return {
        'synced_count': 0,
        'status': 'NO_PENDING_RECORDS',
        'message': 'No existen inspecciones pendientes por sincronizar.',
      };
    }

    final uri = Uri.parse('${AppConfig.apiBaseUrl}/sync/batch');
    final payload = {
      'device_id': AppConfig.deviceId,
      'records': pending.map((e) => e.toSyncJson()).toList(),
    };

    try {
      final response = await http
          .post(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(payload),
          )
          .timeout(const Duration(seconds: 6));

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final decoded = jsonDecode(response.body) as Map<String, dynamic>;
        for (final item in pending) {
          item.isSynced = true;
        }
        return {
          'synced_count': pending.length,
          'status': 'SYNCED_ONLINE',
          'lot_infection_rate': decoded['lot_updated_infection_rate'] ?? 0.0,
          'message':
              'Sincronizados ${pending.length} registros con el servidor PostGIS.',
        };
      }
      return {
        'synced_count': 0,
        'status': 'SERVER_ERROR_${response.statusCode}',
        'message':
            'Servidor respondió HTTP ${response.statusCode}. Los datos siguen seguros en la cola local.',
      };
    } catch (_) {
      return {
        'synced_count': 0,
        'status': 'OFFLINE_QUEUED',
        'message':
            'Sin conexión al servidor (${AppConfig.apiBaseUrl}). ${pending.length} inspecciones resguardadas localmente.',
      };
    }
  }
}
