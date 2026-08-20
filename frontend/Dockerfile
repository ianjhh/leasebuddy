# frontend/Dockerfile

# --- STAGE 1: Install & Build ---
FROM node:18-alpine AS builder

WORKDIR /app

# Using bun instead of npm as requested in the project previously
COPY package.json bun.lockb* ./
RUN npm install -g bun && bun install --frozen-lockfile

COPY . .
RUN npm install -g bun && bun run build

# --- STAGE 2: Run ---
FROM node:18-alpine AS runner

WORKDIR /app
ENV NODE_ENV production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]
