import 'package:flutter/material.dart';
import 'config/app_config.dart';
import 'screens/farm_heatmap_screen.dart';
import 'screens/field_scanner_screen.dart';
import 'services/edge_inference_service.dart';
import 'services/gps_service.dart';
import 'services/offline_sync_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const PlagIAEnterpriseApp());
}

class PlagIAEnterpriseApp extends StatelessWidget {
  const PlagIAEnterpriseApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: AppConfig.appTitle,
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1B5E20),
          brightness: Brightness.light,
        ),
        useMaterial3: true,
      ),
      home: const PlagIAHomeShell(),
    );
  }
}

class PlagIAHomeShell extends StatefulWidget {
  const PlagIAHomeShell({super.key});

  @override
  State<PlagIAHomeShell> createState() => _PlagIAHomeShellState();
}

class _PlagIAHomeShellState extends State<PlagIAHomeShell> {
  final EdgeInferenceService _edgeService = EdgeInferenceService();
  final GpsService _gpsService = GpsService();
  final OfflineSyncService _syncService = OfflineSyncService();

  int _currentIndex = 0;
  String _syncBannerMessage =
      'Modo Rural Offline-First activo. Listo para diagnosticar en terreno.';

  Future<void> _triggerSync() async {
    final result = await _syncService.syncPendingRecords();
    if (!mounted) return;
    setState(() {
      _syncBannerMessage = result['message'] as String;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(_syncBannerMessage)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final pages = [
      FieldScannerScreen(
        edgeService: _edgeService,
        gpsService: _gpsService,
        syncService: _syncService,
        onRecordAdded: () => setState(() {}),
      ),
      FarmHeatmapScreen(records: _syncService.allRecords),
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('PlagIA Tolima Enterprise'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: ActionChip(
              avatar: const Icon(Icons.sync, size: 18),
              label: Text('Cola Sync (${_syncService.pendingCount})'),
              onPressed: _triggerSync,
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
              _syncBannerMessage,
              style: const TextStyle(fontSize: 12, color: Color(0xFF1B5E20)),
            ),
          ),
          Expanded(child: pages[_currentIndex]),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (idx) {
          setState(() {
            _currentIndex = idx;
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
