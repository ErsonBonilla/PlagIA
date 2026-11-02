import 'package:flutter/material.dart';
import 'config/app_config.dart';
import 'screens/farm_heatmap_screen.dart';
import 'screens/field_scanner_screen.dart';
import 'services/edge_inference_service.dart';
import 'services/gps_service.dart';
import 'services/offline_sync_service.dart';
import 'theme/app_theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const AplicacionEmpresarialPlagIA());
}

class AplicacionEmpresarialPlagIA extends StatelessWidget {
  const AplicacionEmpresarialPlagIA({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: ConfiguracionApp.tituloApp,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: const ContenedorInicioPlagIA(),
    );
  }
}

class ContenedorInicioPlagIA extends StatefulWidget {
  const ContenedorInicioPlagIA({super.key});

  @override
  State<ContenedorInicioPlagIA> createState() => _EstadoContenedorInicioPlagIA();
}

class _EstadoContenedorInicioPlagIA extends State<ContenedorInicioPlagIA> {
  final ServicioInferenciaBorde _servicioBorde = ServicioInferenciaBorde();
  final ServicioGps _servicioGps = ServicioGps();
  final ServicioSincronizacionOffline _servicioSincronizacion =
      ServicioSincronizacionOffline();

  int _indiceActual = 0;
  String _mensajeEstadoSincronizacion =
      'Modo Rural Offline-First activo. Listo para diagnosticar en terreno.';

  Future<void> _ejecutarSincronizacion() async {
    final resultado =
        await _servicioSincronizacion.sincronizarRegistrosPendientes();
    if (!mounted) return;
    setState(() {
      _mensajeEstadoSincronizacion = resultado['mensaje'] as String;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(_mensajeEstadoSincronizacion)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final paginas = [
      PantallaEscanerCampo(
        servicioBorde: _servicioBorde,
        servicioGps: _servicioGps,
        servicioSincronizacion: _servicioSincronizacion,
        alAgregarRegistro: () => setState(() {}),
      ),
      PantallaMapaCalorFinca(
        registros: _servicioSincronizacion.todosLosRegistros,
      ),
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('PlagIA Tolima Empresarial'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: ActionChip(
              avatar: const Icon(Icons.sync, size: 18),
              label: Text(
                'Cola Sync (${_servicioSincronizacion.conteoPendientes})',
              ),
              onPressed: _ejecutarSincronizacion,
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          Container(
            width: double.infinity,
            color: const Color(0xFFE8F5E9),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Text(
              _mensajeEstadoSincronizacion,
              style: const TextStyle(fontSize: 12, color: Color(0xFF1B5E20)),
            ),
          ),
          Expanded(child: paginas[_indiceActual]),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _indiceActual,
        onDestinationSelected: (idx) {
          setState(() {
            _indiceActual = idx;
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.biotech_outlined),
            selectedIcon: Icon(Icons.biotech),
            label: 'Escáner Edge-AI',
          ),
          NavigationDestination(
            icon: Icon(Icons.map_outlined),
            selectedIcon: Icon(Icons.map),
            label: 'Mapa de Calor',
          ),
        ],
      ),
    );
  }
}

typedef PlagIAEnterpriseApp = AplicacionEmpresarialPlagIA;
