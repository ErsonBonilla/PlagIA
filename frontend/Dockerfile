# ============================================================================
# PLAGIA EMPRESARIAL - PORTAL WEB SSR & ISLANDS (DENO 2.9.5)
# ============================================================================
FROM denoland/deno:latest

WORKDIR /app

COPY deno.json ./
COPY static ./static
COPY islands ./islands
COPY routes ./routes
COPY tests ./tests
COPY main.ts ./

EXPOSE 3000

CMD ["run", "-A", "main.ts"]
