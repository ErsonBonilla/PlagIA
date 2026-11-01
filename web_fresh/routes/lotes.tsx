import { renderizarDocumentoSSR } from "./_layout.ts";

export function renderizarRutaLotes(): string {
  const cuerpo = `
    <section class="tarjeta-isla">
      <div class="encabezado-isla">
        <div>
          <h2>Inventario Georreferenciado de Fincas y Lotes Arroceros (Tolima)</h2>
          <p class="subtitulo">Polígonos registrados en PostgreSQL 18.6 + PostGIS (EPSG:4326)</p>
        </div>
      </div>
      <div class="contenedor-tabla">
        <table class="tabla-empresarial">
          <thead>
            <tr>
              <th>Código Lote</th>
              <th>Finca Asociada</th>
              <th>Municipio / Distrito</th>
              <th>Variedad de Semilla</th>
              <th>Edad Fenológica</th>
              <th>Área (ha)</th>
              <th>Centroide GPS</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>LOTE-ESPINAL-01</strong></td>
              <td>FINCA-TOL-01 (Hacienda San Isidro)</td>
              <td>El Espinal (Usocoello)</td>
              <td>Fedearroz 67</td>
              <td>58 días (Macollamiento/Primordio)</td>
              <td>42.5 ha</td>
              <td>4.1486, -74.8830</td>
            </tr>
            <tr>
              <td><strong>LOTE-SALDANA-01</strong></td>
              <td>FINCA-TOL-02 (Agrícola Las Palmas)</td>
              <td>Saldaña (Usosaldaña)</td>
              <td>Fedearroz 2000</td>
              <td>45 días (Fase Vegetativa)</td>
              <td>38.0 ha</td>
              <td>3.9317, -75.0153</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  `;
  return renderizarDocumentoSSR("Gestión de Fincas y Lotes", "/lotes", cuerpo, false);
}
