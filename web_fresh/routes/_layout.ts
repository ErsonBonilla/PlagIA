/**
 * Plantilla Base SSR (Renderizado en Servidor) con Sistema de Diseño Cromático
 * y Accesibilidad Visual WCAG AA (> 4.5:1) para el Portal Web de PlagIA.
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
  <link rel="stylesheet" href="/static/styles.css" />
  ${cabecerasLeaflet}
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
