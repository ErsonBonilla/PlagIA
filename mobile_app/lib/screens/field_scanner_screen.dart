import 'package:flutter/material.dart';
import '../config/app_config.dart';
import '../models/inspection_record.dart';
import '../services/edge_inference_service.dart';
import '../services/gps_service.dart';
import '../services/offline_sync_service.dart';

class PantallaEscanerCampo extends StatefulWidget {
  final ServicioInferenciaBorde servicioBorde;
  final ServicioGps servicioGps;
  final ServicioSincronizacionOffline servicioSincronizacion;
  final VoidCallback alAgregarRegistro;

  const PantallaEscanerCampo({
    super.key,
    required this.servicioBorde,
    required this.servicioGps,
    required this.servicioSincronizacion,
    required this.alAgregarRegistro,
  });

  @override
  State<PantallaEscanerCampo> createState() => _EstadoPantallaEscanerCampo();
}

class _EstadoPantallaEscanerCampo extends State<PantallaEscanerCampo> {
  String _idLoteSeleccionado = ConfiguracionApp.lotesTolima.first['id'] as String;
  String _muestraSeleccionada = 'roya_parda';
  RegistroInspeccion? _ultimoDiagnostico;
  bool _procesando = false;

  static const List<Map<String, String>> _opcionesMuestra = [
    {'clave': 'roya_parda', 'etiqueta': 'Muestra Foliar: Roya Parda (roya_parda)'},
    {
      'clave': 'roya_amarilla',
      'etiqueta': 'Muestra Foliar: Roya Amarilla (roya_amarilla)',
    },
    {
      'clave': 'piricularia',
      'etiqueta': 'Muestra Foliar: Piricularia (piricularia)',
    },
    {
      'clave': 'anublo_bacteriano_hoja',
      'etiqueta': 'Muestra Foliar: Añublo Bacteriano (anublo_bacteriano_hoja)',
    },
    {
      'clave': 'barrenador_tallo',
      'etiqueta': 'Plaga en Tallo: Barrenador (barrenador_tallo)',
    },
    {'clave': 'sano', 'etiqueta': 'Muestra Control: Dosel Arrocero Sano (sano)'},
  ];

  Future<void> _capturarYDiagnosticarOffline() async {
    setState(() {
      _procesando = true;
    });

    final coords = widget.servicioGps.capturarCoordenadasLoteActual(
      _idLoteSeleccionado,
    );
    final resultado = await widget.servicioBorde.ejecutarDiagnosticoLocalBorde(
      claveMuestra: _muestraSeleccionada,
      idLote: _idLoteSeleccionado,
      latitud: coords['latitud']!,
      longitud: coords['longitud']!,
    );

    widget.servicioSincronizacion.encolarRegistro(resultado);
    widget.alAgregarRegistro();

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
                  items: ConfiguracionApp.lotesTolima
                      .map(
                        (lote) => DropdownMenuItem<String>(
                          value: lote['id'] as String,
                          child: Text(
                            lote['nombre'] as String,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      )
                      .toList(),
                  onChanged: (valor) {
                    if (valor != null) {
                      setState(() {
                        _idLoteSeleccionado = valor;
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
                          value: item['clave'],
                          child: Text(
                            item['etiqueta']!,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      )
                      .toList(),
                  onChanged: (valor) {
                    if (valor != null) {
                      setState(() {
                        _muestraSeleccionada = valor;
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
        if (_ultimoDiagnostico != null)
          _construirTarjetaDiagnostico(_ultimoDiagnostico!),
      ],
    );
  }

  Widget _construirTarjetaDiagnostico(RegistroInspeccion registro) {
    final bool esSano = registro.etiquetaEnfermedad == 'sano';
    final Color colorInsignia = esSano
        ? const Color(0xFF2E7D32)
        : (registro.nivelRiesgo == 'CRITICO'
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
                    'RIESGO ${registro.nivelRiesgo}',
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                const Spacer(),
                Text(
                  'Confianza: ${(registro.confianza * 100).toStringAsFixed(1)}%',
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              '${registro.nombreComun} (${registro.etiquetaEnfermedad})',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(
              'Agente causal: ${registro.agenteCausal}',
              style: const TextStyle(fontStyle: FontStyle.italic),
            ),
            const Divider(height: 20),
            Text(
              'Coordenadas GPS (Offline): ${registro.latitud}, ${registro.longitud}',
            ),
            Text(
              'Índice de Severidad: ${registro.indiceSeveridad.toStringAsFixed(2)} | Lote: ${registro.idLote}',
            ),
            const SizedBox(height: 10),
            const Text(
              'Recomendación MIP:',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            Text(registro.recomendacionMip),
            const SizedBox(height: 8),
            Text(
              'Estado de sincronización: ${registro.sincronizado ? "Sincronizado con PostgreSQL/PostGIS" : "En cola local SQLite (Pendiente)"}',
              style: TextStyle(
                fontSize: 12,
                color:
                    registro.sincronizado ? Colors.green[800] : Colors.orange[900],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

typedef FieldScannerScreen = PantallaEscanerCampo;
