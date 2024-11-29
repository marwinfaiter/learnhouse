# Base image
FROM python:3.12.3-slim-bookworm as base

# Install Nginx, curl, and build-essential
RUN apt update && apt install -y nginx curl build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm /etc/nginx/sites-enabled/default

# Install Node tools
RUN curl -fsSL https://deb.nodesource.com/setup_21.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g corepack pm2

# Frontend Build
FROM base AS deps

ENV NEXT_PUBLIC_LEARNHOUSE_MULTI_ORG=false
ENV NEXT_PUBLIC_LEARNHOUSE_DEFAULT_ORG=default
ENV NEXT_PUBLIC_LEARNHOUSE_TOP_DOMAIN=buddaphest.se
ENV NEXT_PUBLIC_LEARNHOUSE_DOMAIN=peertube.buddaphest.se
ENV NEXT_PUBLIC_LEARNHOUSE_API_URL=https://peertube.buddaphest.se/api/v1/
ENV NEXT_PUBLIC_LEARNHOUSE_BACKEND_URL=https://peertube.buddaphest.se/
ENV NEXTAUTH_SECRET=6b9202f9d50559000bf1cded4be010e926979e7baeef5aeb2db27e132aae8606
ENV NEXTAUTH_URL=https://peertube.buddaphest.se/

WORKDIR /app/web
COPY ./apps/web/package.json ./apps/web/pnpm-lock.yaml* ./
COPY ./apps/web /app/web
RUN rm -f .env*
RUN if [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm i --frozen-lockfile && pnpm run build; \
    else echo "Lockfile not found." && exit 1; \
    fi

# Final image
FROM base as runner
RUN addgroup --system --gid 1001 system \
    && adduser --system --uid 1001 app \
    && mkdir .next \
    && chown app:system .next
COPY --from=deps /app/web/public ./app/web/public
COPY --from=deps --chown=app:system /app/web/.next/standalone ./app/web/
COPY --from=deps --chown=app:system /app/web/.next/static ./app/web/.next/static

# Backend Build
WORKDIR /app/api
COPY ./apps/api/poetry.lock* ./
COPY ./apps/api/pyproject.toml ./
RUN pip install --upgrade pip \
    && pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi
COPY ./apps/api ./

# Run the backend
WORKDIR /app
COPY ./extra/nginx.conf /etc/nginx/conf.d/default.conf
ENV PORT=8000 LEARNHOUSE_PORT=9000 HOSTNAME=0.0.0.0
COPY ./extra/start.sh /app/start.sh
CMD ["sh", "start.sh"]
