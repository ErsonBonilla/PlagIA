import 'package:flutter/material.dart';

/// Sistema de Diseño Cromático y Accesibilidad Visual (WCAG AA > 4.5:1) para PlagIA.
///
/// Diseñado para operación en campo bajo luz solar intensa en el Tolima y análisis
/// de mapas de calor Grad-CAM sin superposición verde sobre el follaje del arroz.
class AppTheme {
  // A. Paleta Base de la Aplicación (Marca & Neutros UI)
  static const Color verdeArrozal = Color(0xFF1B5E20);
  static const Color verdeHoja = Color(0xFF2E7D32);
  static const Color blancoCampo = Color(0xFFF8F9FA);
  static const Color blancoPuro = Color(0xFFFFFFFF);
  static const Color grisCarbon = Color(0xFF1C1B1F);
  static const Color rojoTolima = Color(0xFFD32F2F);

  // B. Espectro Semántico de Estado Fitosanitario
  static const Color estadoSano = Color(0xFF4CAF50);
  static const Color estadoAlerta = Color(0xFFFFB300);
  static const Color estadoCritico = Color(0xFFD32F2F);
  static const Color estadoDesconocido = Color(0xFF6C757D);

  // C. Espectro Especial Grad-CAM y Capas de Severidad (Evita verde sobre follaje)
  static const Color gradcamBajo = Color(0xFF00B4D8); // Cian Translúcido
  static const Color gradcamMedio = Color(0xFFFFD166); // Amarillo Sol
  static const Color gradcamAlto = Color(0xFFEF476F); // Rojo Carmesí

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      colorScheme: const ColorScheme.light(
        primary: verdeArrozal,
        secondary: rojoTolima,
        surface: blancoPuro,
        onPrimary: blancoPuro,
        onSurface: grisCarbon,
        error: rojoTolima,
      ),
      scaffoldBackgroundColor: blancoCampo,
      appBarTheme: const AppBarTheme(
        backgroundColor: verdeArrozal,
        foregroundColor: blancoPuro,
        elevation: 0,
      ),
      cardTheme: CardThemeData(
        color: blancoPuro,
        elevation: 1,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: Color(0xFFE2E8F0)),
        ),
      ),
    );
  }

  /// Devuelve el color semántico de estado según la etiqueta y el nivel de riesgo.
  static Color colorEstadoFitosanitario(
    String etiquetaEnfermedad,
    String nivelRiesgo,
  ) {
    if (etiquetaEnfermedad == 'desconocido_no_arroz') {
      return estadoDesconocido;
    }
    if (etiquetaEnfermedad == 'sano') {
      return estadoSano;
    }
    if (nivelRiesgo == 'CRITICO' || nivelRiesgo == 'ALTO') {
      return estadoCritico;
    }
    return estadoAlerta;
  }

  /// Devuelve el texto oficial en español para la insignia (badge) de diagnóstico.
  static String textoInsigniaEstado(
    String etiquetaEnfermedad,
    String nivelRiesgo,
  ) {
    if (etiquetaEnfermedad == 'desconocido_no_arroz') {
      return 'Objeto No Identificado';
    }
    if (etiquetaEnfermedad == 'sano') {
      return 'Cultivo Sano';
    }
    if (nivelRiesgo == 'CRITICO' || nivelRiesgo == 'ALTO') {
      return 'Plaga Detectada';
    }
    return 'Alerta Temprana';
  }

  /// Devuelve el color del espectro Grad-CAM (Cian -> Amarillo Sol -> Rojo Carmesí)
  /// evitando usar verde sobre fotografías de hojas o dosel arrocero.
  static Color colorGradCamPorSeveridad(double severidad) {
    if (severidad >= 0.65) {
      return gradcamAlto.withValues(alpha: 0.90);
    }
    if (severidad >= 0.30) {
      return gradcamMedio.withValues(alpha: 0.85);
    }
    return gradcamBajo.withValues(alpha: 0.45);
  }
}
