# Frontend Applairo : Next.js en build « standalone », servi par Node 20.
# Multi-étapes : deps -> build -> runner (image finale minimale).
# Étape « dev » séparée : serveur Next avec hot reload (voir docker-compose.dev.yml).

# ---- deps : installe les dépendances (couche mise en cache) ----
FROM node:20-slim AS deps
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# ---- dev : serveur de développement avec rechargement à chaud ----
# Le code est monté en volume par docker-compose.dev.yml ; node_modules vient de
# l'image (préservé par un volume anonyme côté compose).
FROM node:20-slim AS dev
RUN corepack enable
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["pnpm", "dev"]

# ---- builder : compile l'application ----
FROM node:20-slim AS builder
RUN corepack enable
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm build

# ---- runner : serveur Node autonome, sans code source ni node_modules complet ----
FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

# Le build standalone embarque server.js + les seules dépendances runtime.
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
