FROM node:22-bookworm-slim AS console
WORKDIR /app/apps/console
COPY apps/console/package*.json ./
RUN npm ci
COPY apps/console/ ./
RUN npm run build
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY configs ./configs
COPY data/sample ./data/sample
COPY artifacts/metrics.json ./artifacts/metrics.json
COPY --from=console /app/apps/console/dist ./apps/console/dist
ENV ARGUS_ROOT=/app
EXPOSE 7860
CMD ["sh", "-c", "python -m argus.cli demo && uvicorn argus.api.app:app --host 0.0.0.0 --port 7860"]
