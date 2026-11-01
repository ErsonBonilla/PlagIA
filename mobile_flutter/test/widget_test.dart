import 'package:flutter_test/flutter_test.dart';
import 'package:plagia_mobile/main.dart';

void main() {
  testWidgets(
    'PlagIA Móvil Empresarial renderiza escáner Edge-AI y navegación a Mapa de Calor',
    (WidgetTester tester) async {
      await tester.pumpWidget(const AplicacionEmpresarialPlagIA());

      expect(find.text('PlagIA Tolima Empresarial'), findsOneWidget);
      expect(find.textContaining('Motor Edge-AI ONNX INT8'), findsOneWidget);
      expect(find.text('Escáner Edge-AI'), findsOneWidget);
      expect(find.text('Mapa de Calor'), findsOneWidget);

      await tester.tap(find.text('Mapa de Calor'));
      await tester.pumpAndSettle();

      expect(
        find.textContaining('Mapa de Calor Fitosanitario'),
        findsOneWidget,
      );
    },
  );
}
