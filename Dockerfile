
FROM python:3.12.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin calculator

COPY --chown=calculator:calculator . .
USER calculator

# Demo image: runs the project's pytest suite; it is not a production web service.
CMD ["pytest", "-q"]

