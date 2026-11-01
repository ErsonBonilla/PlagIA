/**
 * Isla Interactiva: Tablero de Control Fitosanitario Institucional (FEDEARROZ / AGROSAVIA).
 *
 * Aplica la Regla de Oro:
 * - Indicadores, filtros por distrito de riego, tablas y alertas en español.
 */

export interface IndicadorDistritoTolima {
  codigo: string;
  distrito: string;
  municipio: string;
  hectareasMonitoreadas: number;
  tasaInfestacionPct: number;
  patogenoPredominante: string;
  nivelAlerta: "VERDE" | "AMARILLA" | "ROJA";
  variedadPrincipal: string;
}

export const INDICADORES_DISTRITOS_TOLIMA: IndicadorDistritoTolima[] = [
  {
    codigo: "USOCOELLO_ESPINAL",
    distrito: "Distrito Usocoello",
    municipio: "El Espinal",
    hectareasMonitoreadas: 1420,
    tasaInfestacionPct: 18.4,
    patogenoPredominante: "Piricularia (piricularia) / Roya Parda",
    nivelAlerta: "ROJA",
    variedadPrincipal: "Fedearroz 67",
  },
  {
    codigo: "USOSALDANA",
    distrito: "Distrito Usosaldaña",
    municipio: "Saldaña",
    hectareasMonitoreadas: 1180,
    tasaInfestacionPct: 11.2,
    patogenoPredominante: "Roya Amarilla (roya_amarilla)",
    nivelAlerta: "AMARILLA",
    variedadPrincipal: "Fedearroz 2000",
  },
  {
    codigo: "MESETA_IBAGUE",
    distrito: "Meseta de Ibagué",
    municipio: "Ibagué",
    hectareasMonitoreadas: 890,
    tasaInfestacionPct: 5.6,
    patogenoPredominante: "Cultivo Saludable (sano)",
    nivelAlerta: "VERDE",
    variedadPrincipal: "Fedearroz 67",
  },
  {
    codigo: "PRADO_PURIFICACION",
    distrito: "Distrito Prado - Purificación",
    municipio: "Purificación",
    hectareasMonitoreadas: 760,
    tasaInfestacionPct: 14.8,
    patogenoPredominante: "Barrenador del Tallo (barrenador_tallo)",
    nivelAlerta: "AMARILLA",
    variedadPrincipal: "Fedearroz 2000",
  },
];

export function renderizarIslaAnalyticsDashboard(): string {
  const filasHtml = INDICADORES_DISTRITOS_TOLIMA.map((item) => {
    const claseInsignia = item.nivelAlerta === "ROJA"
      ? "rojo"
      : (item.nivelAlerta === "AMARILLA" ? "amarillo" : "verde");
    return `
      <tr data-distrito="${item.codigo}">
        <td><strong>${item.distrito}</strong></td>
        <td>${item.municipio}</td>
        <td>${item.variedadPrincipal}</td>
        <td>${item.hectareasMonitoreadas.toLocaleString("es-CO")} ha</td>
        <td><strong>${item.tasaInfestacionPct.toFixed(1)}%</strong></td>
        <td>${item.patogenoPredominante}</td>
        <td><span class="insignia-leyenda ${claseInsignia}">ALERTA ${item.nivelAlerta}</span></td>
      </tr>
    `;
  }).join("");

  return `
  <section class="tarjeta-isla" id="isla-tablero-analitico">
    <div class="encabezado-isla">
      <div>
        <h2>Tablero de Vigilancia Fitosanitaria — convenio técnico FEDEARROZ / AGROSAVIA</h2>
        <p class="subtitulo">Consolidado en tiempo real de vuelos VANT (GeoTIFF) y capturas móviles Offline-First en el Tolima</p>
      </div>
      <div class="controles-isla">
        <label for="filtro-distrito-tablero">Filtrar por Distrito:</label>
        <select id="filtro-distrito-tablero">
          <option value="TODOS">Todos los Distritos del Tolima (4,250 ha)</option>
          <option value="USOCOELLO_ESPINAL">Usocoello - El Espinal</option>
          <option value="USOSALDANA">Usosaldaña - Saldaña</option>
          <option value="MESETA_IBAGUE">Meseta de Ibagué</option>
          <option value="PRADO_PURIFICACION">Prado - Purificación</option>
        </select>
      </div>
    </div>

    <div class="rejilla-kpis">
      <div class="tarjeta-kpi">
        <span class="etiqueta-kpi">Hectáreas Monitoreadas</span>
        <strong class="valor-kpi">4,250 ha</strong>
        <span class="detalle-kpi">6 municipios arroceros activos</span>
      </div>
      <div class="tarjeta-kpi">
        <span class="etiqueta-kpi">Exactitud Modelo Dron (CUDA)</span>
        <strong class="valor-kpi">93.8%</strong>
        <span class="detalle-kpi">ROC-AUC: 0.9735 | 0 neuronas muertas</span>
      </div>
      <div class="tarjeta-kpi">
        <span class="etiqueta-kpi">Latencia Móvil Edge-AI (INT8)</span>
        <strong class="valor-kpi">42 ms</strong>
        <span class="detalle-kpi">Inferencia offline &lt; 200 ms garantizada</span>
      </div>
      <div class="tarjeta-kpi">
        <span class="etiqueta-kpi">Ahorro Estimado en Fungicidas</span>
        <strong class="valor-kpi">38.5%</strong>
        <span class="detalle-kpi">Aplicación focalizada por mapa de calor</span>
      </div>
    </div>

    <div class="contenedor-tabla">
      <table class="tabla-empresarial" id="tabla-distritos-tolima">
        <thead>
          <tr>
            <th>Distrito de Riego</th>
            <th>Municipio</th>
            <th>Variedad Dominante</th>
            <th>Área Evaluada</th>
            <th>Índice de Infestación</th>
            <th>Diagnóstico Predominante</th>
            <th>Semáforo ICA</th>
          </tr>
        </thead>
        <tbody>
          ${filasHtml}
        </tbody>
      </table>
    </div>

    <script>
      (function inicializarFiltroTablero() {
        const selector = document.getElementById("filtro-distrito-tablero");
        const tabla = document.getElementById("tabla-distritos-tolima");
        if (!selector || !tabla) return;

        selector.addEventListener("change", function() {
          const valor = selector.value;
          const filas = tabla.querySelectorAll("tbody tr");
          filas.forEach(function(fila) {
            const cod = fila.getAttribute("data-distrito");
            fila.style.display = (valor === "TODOS" || cod === valor) ? "" : "none";
          });
        });
      })();
    </script>
  </section>
  `;
}
