FROM node:20-alpine AS base

FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build-time env vars (NEXT_PUBLIC_* are baked into the JS bundle)
ARG NEXT_PUBLIC_API_URL=https://loan-agent-backend-632353252476.us-central1.run.app
ARG NEXT_PUBLIC_BEARER_TOKEN=citi-poc-demo-token
ARG NEXT_PUBLIC_ADMIN_PASSWORD=Trustwise@citibank
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_BEARER_TOKEN=$NEXT_PUBLIC_BEARER_TOKEN
ENV NEXT_PUBLIC_ADMIN_PASSWORD=$NEXT_PUBLIC_ADMIN_PASSWORD

RUN npm run build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
