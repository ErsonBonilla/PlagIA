import { manejarSolicitudPortal } from "../main.ts";

Deno.test("Portal Web PlagIA SSR responde en /dashboard, /lotes, /mapas, /reportes y /health", async () => {
  const rutas = ["/dashboard", "/lotes", "/mapas", "/reportes"];

  for (const ruta of rutas) {
    const req = new Request(`http://localhost:3000${ruta}`);
    const resp = manejarSolicitudPortal(req);
    if (resp.status !== 200) {
      throw new Error(`La ruta ${ruta} devolvió estado ${resp.status}`);
    }
    const html = await resp.text();
    if (!html.includes("PlagIA Tolima Empresarial")) {
      throw new Error(`El HTML de ${ruta} no contiene el encabezado corporativo en español.`);
    }
  }

  const reqHealth = new Request("http://localhost:3000/health");
  const respHealth = manejarSolicitudPortal(reqHealth);
  const datos = await respHealth.json();
  if (datos.status !== "ok") {
    throw new Error("El endpoint /health del portal Deno no devolvió ok.");
  }
});
