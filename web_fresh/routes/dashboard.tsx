import { renderizarIslaAnalyticsDashboard } from "../islands/AnalyticsDashboard.tsx";
import { renderizarIslaMapaViewer } from "../islands/MapViewer.tsx";
import { renderizarDocumentoSSR } from "./_layout.ts";

export function renderizarRutaDashboard(): string {
  const cuerpo = `
    ${renderizarIslaAnalyticsDashboard()}
    ${renderizarIslaMapaViewer()}
  `;
  return renderizarDocumentoSSR("Tablero de Control Fitosanitario", "/dashboard", cuerpo, true);
}
