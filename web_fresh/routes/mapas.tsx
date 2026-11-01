import { renderizarIslaMapaViewer } from "../islands/MapViewer.tsx";
import { renderizarDocumentoSSR } from "./_layout.ts";

export function renderizarRutaMapas(): string {
  const cuerpo = `
    ${renderizarIslaMapaViewer()}
  `;
  return renderizarDocumentoSSR("Mapas de Calor Fitosanitarios", "/mapas", cuerpo, true);
}
