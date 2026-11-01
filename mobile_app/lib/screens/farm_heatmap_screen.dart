import 'package:flutter/material.dart';
import '../models/inspection_record.dart';

/// Visor Interactivo de Mapa de Calor Fitosanitario del Lote Arrocero.
class PantallaMapaCalorFinca extends StatelessWidget {
  final List<RegistroInspeccion> registros;

  const PantallaMapaCalorFinca({super.key, required this.registros});

  static const List<Map<String, dynamic>> _celdasCuadriculaBase = [
    {'sector': 'A1 (Noroeste)', 'etiqueta': 'sano', 'severidad': 0.06},
    {'sector': 'A2 (Norte)', 'etiqueta': 'roya_parda', 'severidad': 0.74},
    {'sector': 'A3 (Noreste)', 'etiqueta': 'sano', 'severidad': 0.08},
    {'sector': 'B1 (Oeste)', 'etiqueta': 'roya_amarilla', 'severidad': 0.48},
    {'sector': 'B2 (Centro Lote)', 'etiqueta': 'piricularia', 'severidad': 0.89},
    {'sector': 'B3 (Este)', 'etiqueta': 'roya_parda', 'severidad': 0.68},
    {'sector': 'C1 (Suroeste)', 'etiqueta': 'sano', 'severidad': 0.05},
    {'sector': 'C2 (Sur)', 'etiqueta': 'sano', 'severidad': 0.11},
    {
      'sector': 'C3 (Sureste)',
      'etiqueta': 'barrenador_tallo',
      'severidad': 0.55,
    },
  ];

  Color _colorPorSeveridad(double sev) {
    if (sev >= 0.65) return const Color(0xFFD32F2F);
    if (sev >= 0.30) return const Color(0xFFF57C00);
    return const Color(0xFF388E3C);
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Mapa de Calor Fitosanitario - Lote Las Acacias (El Espinal)',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Fusión geoespacial de ortomosaico VANT + inspecciones móviles georreferenciadas (EPSG:4326).',
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 12,
                  runSpacing: 6,
                  children: [
                    _puntoLeyenda(
                      const Color(0xFF388E3C),
                      'Saludable (<0.30)',
                    ),
                    _puntoLeyenda(
                      const Color(0xFFF57C00),
                      'Moderado (0.30-0.64)',
                    ),
                    _puntoLeyenda(
                      const Color(0xFFD32F2F),
                      'Crítico (>=0.65)',
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: _celdasCuadriculaBase.length,
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 3,
            mainAxisSpacing: 8,
            crossAxisSpacing: 8,
            childAspectRatio: 1.05,
          ),
          itemBuilder: (context, index) {
            final celda = _celdasCuadriculaBase[index];
            final double sev = (celda['severidad'] as num).toDouble();
            final Color colorFondo = _colorPorSeveridad(sev);
            return Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: colorFondo.withValues(alpha: 0.88),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.black26),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    celda['sector'] as String,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    celda['etiqueta'] as String,
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.white, fontSize: 11),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Sev: ${sev.toStringAsFixed(2)}',
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w600,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            );
          },
        ),
        const SizedBox(height: 16),
        Text(
          'Puntos Georreferenciados Capturados en Campo (${registros.length})',
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        if (registros.isEmpty)
          const Card(
            child: Padding(
              padding: EdgeInsets.all(12),
              child: Text(
                'Aún no se han capturado muestras móviles en esta sesión. Usa la pestaña Escáner Edge-AI.',
              ),
            ),
          )
        else
          ...registros.map(
            (r) => Card(
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor: _colorPorSeveridad(r.indiceSeveridad),
                  child: const Icon(Icons.location_on, color: Colors.white),
                ),
                title: Text(
                  '${r.nombreComun} (${r.etiquetaEnfermedad} - ${r.idLote})',
                ),
                subtitle: Text(
                  'GPS: ${r.latitud}, ${r.longitud} | Severidad: ${r.indiceSeveridad}',
                ),
                trailing: Icon(
                  r.sincronizado ? Icons.cloud_done : Icons.cloud_upload_outlined,
                  color: r.sincronizado ? Colors.green : Colors.orange,
                ),
              ),
            ),
          ),
      ],
    );
  }

  Widget _puntoLeyenda(Color color, String texto) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
        Text(texto, style: const TextStyle(fontSize: 12)),
      ],
    );
  }
}

typedef FarmHeatmapScreen = PantallaMapaCalorFinca;
