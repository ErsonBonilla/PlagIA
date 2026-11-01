/**
 * Isla Interactiva: Visor Geoespacial de Ortomosaicos y Mapas de Calor (Leaflet + GeoJSON).
 *
 * Aplica la Regla de Oro:
 * - Interfaz de usuario, leyendas, popups agronómicos y variables de dominio en español.
 * - Contratos GeoJSON (`FeatureCollection`, `features`, `geometry`, `properties`) y API Leaflet en inglés.
 */

export interface CeldaCalorFitosanitaria {
  idParche: string;
  sector: string;
  etiquetaEnfermedad: string;
  nombreComun: string;
  indiceSeveridad: number;
  nivelRiesgo: "BAJO" | "MEDIO" | "ALTO" | "CRITICO";
  latitud: number;
  longitud: number;
  recomendacionMip: string;
}

export const CELDAS_CALOR_TOLIMA: CeldaCalorFitosanitaria[] = [
  {
    idParche: "PAR-001",
    sector: "Sector Norte - Canal Usocoello",
    etiquetaEnfermedad: "sano",
    nombreComun: "Cultivo Saludable",
    indiceSeveridad: 0.06,
    nivelRiesgo: "BAJO",
    latitud: 4.1512,
    longitud: -74.8865,
    recomendacionMip: "Mantener lámina de agua estable y monitoreo preventivo.",
  },
  {
    idParche: "PAR-002",
    sector: "Sector Central - Lote Las Acacias",
    etiquetaEnfermedad: "piricularia",
    nombreComun: "Piricularia / Añublo del Arroz",
    indiceSeveridad: 0.89,
    nivelRiesgo: "CRITICO",
    latitud: 4.1486,
    longitud: -74.8830,
    recomendacionMip:
      "Fumigación localizada prioritaria con fungicida específico según umbral ICA / FEDEARROZ.",
  },
  {
    idParche: "PAR-003",
    sector: "Sector Oriental - El Espinal",
    etiquetaEnfermedad: "roya_parda",
    nombreComun: "Roya Parda Foliar",
    indiceSeveridad: 0.74,
    nivelRiesgo: "ALTO",
    latitud: 4.1460,
    longitud: -74.8795,
    recomendacionMip:
      "Inspeccionar foco georreferenciado y aplicar control fúngico en parche.",
  },
  {
    idParche: "PAR-004",
    sector: "Sector Sur - Saldaña",
    etiquetaEnfermedad: "barrenador_tallo",
    nombreComun: "Barrenador del Tallo (Diatraea / Rupela)",
    indiceSeveridad: 0.58,
    nivelRiesgo: "ALTO",
    latitud: 3.9317,
    longitud: -75.0153,
    recomendacionMip:
      "Liberación biológica de Trichogramma exiguum y control de socas.",
  },
];

export function renderizarIslaMapaViewer(urlApiBase = "http://localhost:8000/api/v1"): string {
  const datosInicialesJson = JSON.stringify(CELDAS_CALOR_TOLIMA);

  return `
  <section class="tarjeta-isla" id="isla-visor-mapa">
    <div class="encabezado-isla">
      <div>
        <h2>Visor Geoespacial de Ortomosaicos y Mapa de Calor (PostGIS / GeoJSON)</h2>
        <p class="subtitulo">Integración interactiva Leaflet para los distritos de riego del Tolima (EPSG:4326)</p>
      </div>
      <div class="controles-isla">
        <select id="selector-finca-mapa" aria-label="Seleccionar Finca o Lote">
          <option value="LOTE-ESPINAL-01">FINCA-TOL-01 · Lote Las Acacias (El Espinal)</option>
          <option value="LOTE-SALDANA-01">FINCA-TOL-02 · Lote El Canal (Saldaña)</option>
        </select>
        <button type="button" id="btn-sincronizar-mapa" class="boton-primario">
          Cargar Capa GeoJSON en Vivo
        </button>
      </div>
    </div>

    <div class="leyenda-calor">
      <span class="insignia-leyenda verde">Saludable (&lt; 0.30)</span>
      <span class="insignia-leyenda amarillo">Moderado (0.30 - 0.64)</span>
      <span class="insignia-leyenda rojo">Crítico (&ge; 0.65 - Acción Inmediata)</span>
    </div>

    <div id="contenedor-leaflet-tolima" style="height: 430px; width: 100%; border-radius: 10px; border: 1px solid #cbd5e1;"></div>
    <p id="estado-conexion-mapa" class="nota-pie">
      Estado de capa espacial: Mostrando malla georreferenciada del Tolima. Conectado a <code>${urlApiBase}/maps/heatmap/{farm_id}</code>.
    </p>

    <script>
      (function inicializarIslaMapa() {
        const celdasBase = ${datosInicialesJson};
        const urlApi = "${urlApiBase}";

        function colorPorSeveridad(sev) {
          if (sev >= 0.65) return "#dc2626";
          if (sev >= 0.30) return "#f59e0b";
          return "#16a34a";
        }

        function montarMapa() {
          if (typeof L === "undefined") return;
          const mapa = L.map("contenedor-leaflet-tolima").setView([4.1486, -74.8830], 14);
          L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: "&copy; OpenStreetMap | PlagIA Tolima Geoespacial"
          }).addTo(mapa);

          const capaGrupo = L.layerGroup().addTo(mapa);

          function dibujarCeldasLocales(lista) {
            capaGrupo.clearLayers();
            lista.forEach(function(c) {
              const color = colorPorSeveridad(c.indiceSeveridad);
              const circulo = L.circle([c.latitud, c.longitud], {
                color: color,
                fillColor: color,
                fillOpacity: 0.55,
                radius: 180
              }).addTo(capaGrupo);

              circulo.bindPopup(
                "<strong>" + c.nombreComun + " (" + c.etiquetaEnfermedad + ")</strong><br/>" +
                "Sector: " + c.sector + "<br/>" +
                "Índice de Severidad: <b>" + c.indiceSeveridad.toFixed(2) + "</b> (" + c.nivelRiesgo + ")<br/>" +
                "<em>MIP: " + c.recomendacionMip + "</em>"
              );
            });
          }

          dibujarCeldasLocales(celdasBase);

          const boton = document.getElementById("btn-sincronizar-mapa");
          const selector = document.getElementById("selector-finca-mapa");
          const estado = document.getElementById("estado-conexion-mapa");

          if (boton && selector && estado) {
            boton.addEventListener("click", async function() {
              const idLote = selector.value;
              estado.textContent = "Consultando capa GeoJSON en " + urlApi + "/maps/heatmap/" + idLote + "...";
              try {
                const resp = await fetch(urlApi + "/maps/heatmap/" + idLote);
                if (!resp.ok) throw new Error("HTTP " + resp.status);
                const data = await resp.json();
                capaGrupo.clearLayers();
                const capaGeo = L.geoJSON(data.geojson, {
                  style: function(feature) {
                    const sev = (feature.properties && feature.properties.severity_index) || 0.1;
                    const col = colorPorSeveridad(sev);
                    return { color: col, fillColor: col, weight: 2, fillOpacity: 0.55 };
                  },
                  onEachFeature: function(feature, layer) {
                    const p = feature.properties || {};
                    layer.bindPopup(
                      "<strong>" + (p.nombre_comun || p.disease_label) + "</strong><br/>" +
                      "Severidad: " + p.severity_index + " | Riesgo: " + p.nivel_riesgo + "<br/>" +
                      "<em>" + (p.recomendacion_mip || "") + "</em>"
                    );
                  }
                }).addTo(capaGrupo);
                if (capaGeo.getBounds().isValid()) {
                  mapa.fitBounds(capaGeo.getBounds());
                }
                estado.textContent = "Capa GeoJSON sincronizada (" + data.total_cells + " celdas, infestación: " + (data.infection_rate * 100).toFixed(1) + "%).";
              } catch (err) {
                dibujarCeldasLocales(celdasBase);
                estado.textContent = "Modo Rural Resiliente: Mostrando caché geoespacial local (" + err.message + ").";
              }
            });
          }
        }

        if (document.readyState === "complete") {
          montarMapa();
        } else {
          window.addEventListener("load", montarMapa);
        }
      })();
    </script>
  </section>
  `;
}
