/**
 * Plantilla Base SSR (Renderizado en Servidor) para optimizar el ancho de banda rural.
 */

export function renderizarDocumentoSSR(
  tituloPagina: string,
  rutaActiva: string,
  contenidoPrincipalHtml: string,
  incluirLeaflet = false,
): string {
  const cabecerasLeaflet = incluirLeaflet
    ? `
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" defer></script>
    `
    : "";

  const enlaces = [
    { ruta: "/dashboard", texto: "Tablero Fitosanitario" },
    { ruta: "/lotes", texto: "Fincas y Lotes" },
    { ruta: "/mapas", texto: "Mapas de Calor VANT" },
    { ruta: "/reportes", texto: "Reportes MIP & Auditoría" },
  ];

  const navegacionHtml = enlaces.map((item) => {
    const claseActivo = item.ruta === rutaActiva ? "enlace-nav activo" : "enlace-nav";
    return `<a href="${item.ruta}" class="${claseActivo}">${item.texto}</a>`;
  }).join("");

  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${tituloPagina} | PlagIA Tolima Empresarial</title>
  ${cabecerasLeaflet}
  <style>
    :root {
      --verde-corporativo: #1b5e20;
      --verde-claro: #e8f5e9;
      --gris-fondo: #f8fafc;
      --texto-oscuro: #0f172a;
      --borde-suave: #e2e8f0;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      background-color: var(--gris-fondo);
      color: var(--texto-oscuro);
      line-height: 1.5;
    }
    .barra-superior {
      background-color: var(--verde-corporativo);
      color: #ffffff;
      padding: 0.9rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }
    .marca-titulo {
      font-size: 1.25rem;
      font-weight: 700;
      margin: 0;
    }
    .marca-subtitulo {
      font-size: 0.8rem;
      opacity: 0.9;
      display: block;
    }
    .navegacion-principal {
      display: flex;
      gap: 0.75rem;
      flex-wrap: wrap;
    }
    .enlace-nav {
      color: #ffffff;
      text-decoration: none;
      padding: 0.45rem 0.9rem;
      border-radius: 6px;
      font-size: 0.9rem;
      font-weight: 500;
      background: rgba(255, 255, 255, 0.1);
    }
    .enlace-nav.activo, .enlace-nav:hover {
      background: #ffffff;
      color: var(--verde-corporativo);
    }
    .contenedor-principal {
      max-width: 1240px;
      margin: 1.5rem auto;
      padding: 0 1.25rem;
    }
    .tarjeta-isla {
      background: #ffffff;
      border: 1px solid var(--borde-suave);
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    .encabezado-isla {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 1.25rem;
    }
    .encabezado-isla h2 { margin: 0 0 0.25rem 0; font-size: 1.25rem; }
    .subtitulo { margin: 0; color: #475569; font-size: 0.9rem; }
    .controles-isla { display: flex; gap: 0.6rem; align-items: center; flex-wrap: wrap; }
    select, .boton-primario {
      padding: 0.5rem 0.85rem;
      border-radius: 6px;
      border: 1px solid #cbd5e1;
      font-size: 0.9rem;
    }
    .boton-primario {
      background-color: var(--verde-corporativo);
      color: #ffffff;
      border: none;
      cursor: pointer;
      font-weight: 600;
    }
    .rejilla-kpis {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }
    .tarjeta-kpi {
      background: var(--verde-claro);
      border-radius: 10px;
      padding: 1rem;
      display: flex;
      flex-direction: column;
    }
    .etiqueta-kpi { font-size: 0.8rem; color: #1e293b; font-weight: 600; }
    .valor-kpi { font-size: 1.65rem; color: var(--verde-corporativo); margin: 0.2rem 0; }
    .detalle-kpi { font-size: 0.78rem; color: #334155; }
    .contenedor-tabla { overflow-x: auto; }
    .tabla-empresarial {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
    }
    .tabla-empresarial th, .tabla-empresarial td {
      padding: 0.75rem;
      text-align: left;
      border-bottom: 1px solid var(--borde-suave);
    }
    .tabla-empresarial th { background-color: #f1f5f9; font-weight: 600; }
    .leyenda-calor { display: flex; gap: 0.75rem; margin-bottom: 1rem; flex-wrap: wrap; }
    .insignia-leyenda {
      display: inline-block;
      padding: 0.25rem 0.65rem;
      border-radius: 999px;
      font-size: 0.78rem;
      font-weight: 700;
      color: #ffffff;
    }
    .insignia-leyenda.verde { background-color: #16a34a; }
    .insignia-leyenda.amarillo { background-color: #d97706; }
    .insignia-leyenda.rojo { background-color: #dc2626; }
    .nota-pie { font-size: 0.82rem; color: #475569; margin-top: 0.75rem; }
    .aviso-ica {
      background: #fffbeb;
      border-left: 4px solid #d97706;
      padding: 0.9rem 1.2rem;
      border-radius: 6px;
      font-size: 0.85rem;
      margin-top: 1.5rem;
    }
  </style>
</head>
<body>
  <header class="barra-superior">
    <div>
      <h1 class="marca-titulo">PlagIA Tolima Empresarial</h1>
      <span class="marca-subtitulo">Vigilancia Fitosanitaria Multinivel (Drones VANT + Flutter Edge-AI + PostGIS)</span>
    </div>
    <nav class="navegacion-principal" aria-label="Navegación Principal">
      ${navegacionHtml}
    </nav>
  </header>
  <main class="contenedor-principal">
    ${contenidoPrincipalHtml}
    <div class="aviso-ica">
      <strong>AVISO AGRONOMICO (GOBERNANZA ICA / FEDEARROZ):</strong>
      PlagIA es un sistema de soporte a la decisión para Manejo Integrado de Plagas (MIP).
      Toda aplicación química debe ser prescrita por un Ingeniero Agrónomo con tarjeta profesional vigente.
    </div>
  </main>
</body>
</html>`;
}
