FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends bubblewrap \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system prove && adduser --system --ingroup prove prove \
    && mkdir -p /var/lib/prove/evidence /var/lib/prove/output \
    && chown -R prove:prove /app /var/lib/prove
COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=prove:prove apps/api .
USER prove
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
