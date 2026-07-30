# syntax=docker/dockerfile:1

FROM node:24.18.1-bookworm AS base
RUN corepack enable && corepack prepare pnpm@10.33.3 --activate
WORKDIR /app

FROM base AS deps
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml* ./
COPY packages/shared/package.json packages/shared/
COPY packages/server/package.json packages/server/
COPY packages/web/package.json packages/web/
RUN pnpm install --frozen-lockfile || pnpm install

FROM deps AS build
COPY . .
RUN pnpm --filter @opsswarm/shared build \
 && pnpm --filter @opsswarm/server build \
 && pnpm --filter @opsswarm/web build

FROM base AS api
COPY --from=build /app /app
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3001
ENV HOST=0.0.0.0
ENV DATABASE_URL=/data/opsswarm.db
EXPOSE 3001
CMD ["pnpm", "--filter", "@opsswarm/server", "start"]

FROM nginx:1.27-alpine AS web
COPY --from=build /app/packages/web/dist /usr/share/nginx/html
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
