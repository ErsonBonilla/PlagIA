import 'package:flutter/material.dart';
import '../config/app_config.dart';
import '../models/inspection_record.dart';
import '../services/edge_inference_service.dart';
import '../services/gps_service.dart';
import '../services/offline_sync_service.dart';

class FieldScannerScreen extends StatefulWidget {
  final EdgeInferenceService edgeService;
  final GpsService gpsService;
  final OfflineSyncService syncService;
  final VoidCallback onRecordAdded;

  const FieldScannerScreen({
    super.key,
    required this.edgeService,
    required this.gpsService,
    required this.syncService,
    required this.onRecordAdded,
  });

  @override
  State<FieldScannerScreen> createState() => _FieldScannerScreenState();
}

class _FieldScannerScreenState extends State<FieldScannerScreen> {
  String _idLoteSeleccionado = AppConfig.tolimaLots.first['id'] as String;
  String _muestraSeleccionada = 'roya_parda';
  InspectionRecord? _ultimoDiagnostico;
  bool _procesando = false;

  static const List<Map<String, String>> _opcionesMuestra = [
    {'key': 'roya_parda', 'label': 'Muestra Foliar: Roya Parda (roya_parda)'},
    {
      'key': 'roya_amarilla',
      'label': 'Muestra Foliar: Roya Amarilla (roya_amarilla)',
    },
    {
      'key': 'piricularia',
      'label': 'Muestra Foliar: Piricularia (piricularia)',
    },
    {
      'key': 'anublo_bacteriano_hoja',
      'label': 'Muestra Foliar: Añublo Bacteriano (anublo_bacteriano_hoja)',
    },
    {
      'key': 'barrenador_tallo',
      'label': 'Plaga en Tallo: Barrenador (barrenador_tallo)',
    },
    {'key': 'sano', 'label': 'Muestra Control: Dosel Arrocero Sano (sano)'},
  ];

  Future<void> _capturarYDiagnosticarOffline() async {
    setState(() {
      _procesando = true;
    });

    final coords = widget.gpsService.captureCurrentLotCoordinates(
      _idLoteSeleccionado,
    );
    final resultado = await widget.edgeService.runLocalEdgeDiagnosis(
      sampleKey: _muestraSeleccionada,
      lotId: _idLoteSeleccionado,
      latitude: coords['latitude']!,
      longitude: coords['longitude']!,
    );

    widget.syncService.enqueueRecord(resultado);
    widget.onRecordAdded();

    if (!mounted) return;
    setState(() {
      _ultimoDiagnostico = resultado;
      _procesando = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          elevation: 1,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.memory, color: Color(0xFF1B5E20)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Motor Edge-AI ONNX INT8 (Modo Offline Activo)',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                const Text(
                  'Ejecuta el reconocimiento fitosanitario directamente en el dispositivo móvil sin requerir cobertura celular en el lote.',
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  initialValue: _idLoteSeleccionado,
                  isExpanded: true,
                  decoration: const InputDecoration(
                    labelText: 'Lote Arrocero (Tolima)',
                    border: OutlineInputBorder(),
                  ),
                  items: AppConfig.tolimaLots
                      .map(
                        (lot) => DropdownMenuItem<String>(
                          value: lot['id'] as String,
                          child: Text(
                            lot['name'] as String,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      )
                      .toList(),
                  onChanged: (val) {
                    if (val != null) {
                      setState(() {
                        _idLoteSeleccionado = val;
                      });
                    }
                  },
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: _muestraSeleccionada,
                  isExpanded: true,
                  decoration: const InputDecoration(
                    labelText: 'Captura de Cámara / Patrón Fitosanitario',
                    border: OutlineInputBorder(),
                  ),
                  items: _opcionesMuestra
                      .map(
                        (item) => DropdownMenuItem<String>(
                          value: item['key'],
                          child: Text(
                            item['label']!,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      )
                      .toList(),
                  onChanged: (val) {
                    if (val != null) {
                      setState(() {
                        _muestraSeleccionada = val;
                      });
                    }
                  },
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: _procesando ? null : _capturarYDiagnosticarOffline,
                    icon: const Icon(Icons.camera_alt),
                    label: Text(
                      _procesando
                          ? 'Procesando en Edge-AI...'
                          : 'Capturar Hoja + Diagnosticar Offline',
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        if (_ultimoDiagnostico != null) _construirTarjetaDiagnostico(_ultimoDiagnostico!),
      ],
    );
  }

  Widget _construirTarjetaDiagnostico(InspectionRecord registro) {
    final bool esSano = registro.diseaseLabel == 'sano';
    final Color colorInsignia = esSano
        ? const Color(0xFF2E7D32)
        : (registro.riskLevel == 'CRITICO'
              ? const Color(0xFFC62828)
              : const Color(0xFFEF6C00));

    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: colorInsignia,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    'RIESGO ${registro.riskLevel}',
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                const Spacer(),
                Text(
                  'Confianza: ${(registro.confidence * 100).toStringAsFixed(1)}%',
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              '${registro.commonName} (${registro.diseaseLabel})',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(
              'Agente causal: ${registro.causalAgent}',
              style: const TextStyle(fontStyle: FontStyle.italic),
            ),
            const Divider(height: 20),
            Text(
              'Coordenadas GPS (Offline): ${registro.latitude}, ${registro.longitude}',
            ),
            Text(
              'Índice de Severidad: ${registro.severityIndex.toStringAsFixed(2)} | Lote: ${registro.lotId}',
            ),
            const SizedBox(height: 10),
            const Text(
              'Recomendación MIP:',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            Text(registro.mipRecommendation),
            const SizedBox(height: 8),
            Text(
              'Estado de sincronización: ${registro.isSynced ? "Sincronizado con PostGIS" : "En cola local SQLite (Pendiente)"}',
              style: TextStyle(
                fontSize: 12,
                color: registro.isSynced ? Colors.green[800] : Colors.orange[900],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
