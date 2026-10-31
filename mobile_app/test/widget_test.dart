import 'package:flutter_test/flutter_test.dart';
import 'package:plagia_mobile/main.dart';

void main() {
  testWidgets('PlagIA Enterprise Mobile renders Edge-AI scanner and Heatmap navigation', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const PlagIAEnterpriseApp());

    expect(find.text('PlagIA Tolima Enterprise'), findsOneWidget);
    expect(find.textContaining('Motor Edge-AI ONNX INT8'), findsOneWidget);
    expect(find.text('Escáner Edge-AI'), findsOneWidget);
    expect(find.text('Mapa de Calor'), findsOneWidget);

    await tester.tap(find.text('Mapa de Calor'));
    await tester.pumpAndSettle();

    expect(
      find.textContaining('Mapa de Calor Fitosanitario'),
      findsOneWidget,
    );
  });
}
