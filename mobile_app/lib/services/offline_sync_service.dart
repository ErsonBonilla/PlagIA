import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';
import '../models/inspection_record.dart';

/// Gestor de Cola Offline-First y Sincronización por Lotes hacia FastAPI (`/api/v1/sync/batch`).
///
/// Aplica la Regla de Oro:
/// - Métodos, estados internos y mensajes al usuario en español.
/// - Cabeceras HTTP (`Content-Type`) y contrato JSON (`device_id`, `records`) en inglés.
class ServicioSincronizacionOffline {
  final List<RegistroInspeccion> _registros = [];

  List<RegistroInspeccion> get todosLosRegistros =>
      List.unmodifiable(_registros);

  int get conteoPendientes => _registros.where((r) => !r.sincronizado).length;

  void encolarRegistro(RegistroInspeccion registro) {
    _registros.insert(0, registro);
  }

  Future<Map<String, dynamic>> sincronizarRegistrosPendientes() async {
    final pendientes = _registros.where((r) => !r.sincronizado).toList();
    if (pendientes.isEmpty) {
      return {
        'sincronizados': 0,
        'estado': 'SIN_PENDIENTES',
        'mensaje': 'No existen inspecciones pendientes por sincronizar.',
      };
    }

    final uri = Uri.parse('${ConfiguracionApp.urlBaseApi}/sync/batch');
    final cargaContrato = {
      'device_id': ConfiguracionApp.idDispositivo,
      'records': pendientes.map((e) => e.toSyncJson()).toList(),
    };

    try {
      final respuesta = await http
          .post(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(cargaContrato),
          )
          .timeout(const Duration(seconds: 6));

      if (respuesta.statusCode >= 200 && respuesta.statusCode < 300) {
        final decodificado =
            jsonDecode(respuesta.body) as Map<String, dynamic>;
        for (final item in pendientes) {
          item.sincronizado = true;
        }
        return {
          'sincronizados': pendientes.length,
          'estado': 'SINCRONIZADO_EN_LINEA',
          'tasa_infestacion_lote':
              decodificado['lot_updated_infection_rate'] ?? 0.0,
          'mensaje':
              'Sincronizados ${pendientes.length} registros con el servidor PostgreSQL/PostGIS.',
        };
      }
      return {
        'sincronizados': 0,
        'estado': 'ERROR_SERVIDOR_${respuesta.statusCode}',
        'mensaje':
            'Servidor respondió HTTP ${respuesta.statusCode}. Los datos siguen seguros en la cola local.',
      };
    } catch (_) {
      return {
        'sincronizados': 0,
        'estado': 'ENCOLADO_OFFLINE',
        'mensaje':
            'Sin conexión al servidor (${ConfiguracionApp.urlBaseApi}). ${pendientes.length} inspecciones resguardadas localmente.',
      };
    }
  }
}

typedef OfflineSyncService = ServicioSincronizacionOffline;
