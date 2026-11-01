import { renderizarDocumentoSSR } from "./_layout.ts";

export function renderizarRutaReportes(): string {
  const cuerpo = `
    <section class="tarjeta-isla">
      <div class="encabezado-isla">
        <div>
          <h2>Reportes Técnicos MIP y Auditoría Neuronal de Modelos</h2>
          <p class="subtitulo">Trazabilidad MLOps (MLflow Registry) y Control de Entradas Fuera de Dominio</p>
        </div>
      </div>
      <div class="contenedor-tabla">
        <table class="tabla-empresarial">
          <thead>
            <tr>
              <th>Modelo Desplegado</th>
              <th>Dominio</th>
              <th>Clases Fitosanitarias</th>
              <th>Exactitud / ROC-AUC</th>
              <th>Neuronas Activas</th>
              <th>Formato / Peso</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>EfficientNet-B0 Aéreo</strong></td>
              <td>01_dron_dosel_cls (VANT)</td>
              <td>4 clases (sano, roya_parda, roya_amarilla, suelo_desnudo)</td>
              <td>93.8% Prueba | AUC 0.9735</td>
              <td>256 / 256 (100%)</td>
              <td>ONNX INT8 (4.51 MB)</td>
            </tr>
            <tr>
              <td><strong>EfficientNet-B0 / MobileNetV2 Foliar</strong></td>
              <td>02_campo_hoja_cls (Móvil)</td>
              <td>10 patologías + rechazo <code>desconocido_no_arroz</code></td>
              <td>AUC 0.9346</td>
              <td>256 / 256 (100%)</td>
              <td>ONNX INT8 (4.51 MB)</td>
            </tr>
            <tr>
              <td><strong>Ultralytics YOLOv8/v11</strong></td>
              <td>03_deteccion_plagas_yolo</td>
              <td>29 especies entomológicas (62,227 cajas delimitadoras)</td>
              <td>Localización en tiempo real</td>
              <td>Híbrido YOLO + HSV</td>
              <td>ONNX / TorchScript</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  `;
  return renderizarDocumentoSSR("Reportes Técnicos y Auditoría", "/reportes", cuerpo, false);
}
