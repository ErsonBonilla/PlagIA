/**
 * Isla Interactiva: Visor Geoespacial de Ortomosaicos y Mapas de Calor (Leaflet + GeoJSON).
 *
 * Aplica la Regla de Visibilidad Grad-CAM:
 * - Nunca utiliza verde sobre follaje para baja activación.
 * - Nivel 0 (Baja/Sin Activación): Cian Translúcido (#00B4D8, opacity: 0.3)
 * - Nivel 1 (Activación Media)   : Amarillo Sol (#FFD166, opacity: 0.7)
 * - Nivel 2 (Foco de Infección)  : Rojo Carmesí (#EF476F, opacity: 0.9)
 */

export interface CeldaCalorFitosanitaria {
  idParche: string;
  sector: string;
  etiquetaEnfermedad: string;
  nombreComun: string;
  estadoBadge: "Cultivo Sano" | "Alerta Temprana" | "Plaga Detectada" | "Objeto No Identificado";
  indiceSeveridad: number;
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
    estadoBadge: "Cultivo Sano",
    indiceSeveridad: 0.06,
    latitud: 4.1512,
    longitud: -74.8865,
    recomendacionMip: "Mantener lámina de agua estable y monitoreo preventivo.",
  },
  {
    idParche: "PAR-002",
    sector: "Sector Central - Lote Las Acacias",
    etiquetaEnfermedad: "piricularia",
    nombreComun: "Piricularia / Añublo del Arroz",
    estadoBadge: "Plaga Detectada",
    indiceSeveridad: 0.89,
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
    estadoBadge: "Plaga Detectada",
    indiceSeveridad: 0.74,
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
    estadoBadge: "Alerta Temprana",
    indiceSeveridad: 0.48,
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
        <h2>Visor Geoespacial de Ortomosaicos y Capas Grad-CAM (PostGIS / GeoJSON)</h2>
        <p class="subtitulo">Espectro de alto contraste (Cian / Amarillo Sol / Rojo Carmesí) sin superposición verde sobre follaje</p>
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
      <span class="insignia-gradcam nivel-0">Nivel 0 · Cultivo Sano (#00B4D8, opacidad 0.3)</span>
      <span class="insignia-gradcam nivel-1">Nivel 1 · Alerta Temprana (#FFD166, opacidad 0.7)</span>
      <span class="insignia-gradcam nivel-2">Nivel 2 · Plaga Detectada (#EF476F, opacidad 0.9)</span>
    </div>

    <div id="contenedor-leaflet-tolima" style="height: 430px; width: 100%; border-radius: 10px; border: 1px solid #cbd5e1;"></div>
    <p id="estado-conexion-mapa" class="nota-pie">
      Estado de capa espacial: Mostrando espectro Grad-CAM del Tolima. Conectado a <code>${urlApiBase}/maps/heatmap/{farm_id}</code>.
    </p>

    <script>
      (function inicializarIslaMapa() {
        const celdasBase = ${datosInicialesJson};
        const urlApi = "${urlApiBase}";

        function estiloGradCamPorSeveridad(sev) {
          if (sev >= 0.65) {
            return { color: "#EF476F", fillColor: "#EF476F", fillOpacity: 0.9, badge: "Plaga Detectada" };
          }
          if (sev >= 0.30) {
            return { color: "#FFD166", fillColor: "#FFD166", fillOpacity: 0.7, badge: "Alerta Temprana" };
          }
          return { color: "#00B4D8", fillColor: "#00B4D8", fillOpacity: 0.3, badge: "Cultivo Sano" };
        }

        function montarMapa() {
          if (typeof L === "undefined") return;
          const mapa = L.map("contenedor-leaflet-tolima").setView([4.1486, -74.8830], 14);
          L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: "&copy; OpenStreetMap | PlagIA Tolima Grad-CAM"
          }).addTo(mapa);

          const capaGrupo = L.layerGroup().addTo(mapa);

          function dibujarCeldasLocales(lista) {
            capaGrupo.clearLayers();
            lista.forEach(function(c) {
              const est = estiloGradCamPorSeveridad(c.indiceSeveridad);
              const circulo = L.circle([c.latitud, c.longitud], {
                color: est.color,
                fillColor: est.fillColor,
                fillOpacity: est.fillOpacity,
                weight: 2,
                radius: 180
              }).addTo(capaGrupo);

              circulo.bindPopup(
                "<strong>" + c.estadoBadge + " · " + c.nombreComun + "</strong><br/>" +
                "Sector: " + c.sector + "<br/>" +
                "Índice de Severidad: <b>" + c.indiceSeveridad.toFixed(2) + "</b><br/>" +
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
                    const est = estiloGradCamPorSeveridad(sev);
                    return {
                      color: est.color,
                      fillColor: est.fillColor,
                      weight: 2,
                      fillOpacity: est.fillOpacity
                    };
                  },
                  onEachFeature: function(feature, layer) {
                    const p = feature.properties || {};
                    const est = estiloGradCamPorSeveridad(p.severity_index || 0.1);
                    layer.bindPopup(
                      "<strong>" + est.badge + " · " + (p.nombre_comun || p.disease_label) + "</strong><br/>" +
                      "Severidad: " + p.severity_index + "<br/>" +
                      "<em>" + (p.recomendacion_mip || "") + "</em>"
                    );
                  }
                }).addTo(capaGrupo);
                if (capaGeo.getBounds().isValid()) {
                  mapa.fitBounds(capaGeo.getBounds());
                }
                estado.textContent = "Capa GeoJSON Grad-CAM sincronizada (" + data.total_cells + " celdas, infestación: " + (data.infection_rate * 100).toFixed(1) + "%).";
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
