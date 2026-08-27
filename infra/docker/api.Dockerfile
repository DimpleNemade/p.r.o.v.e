FROM python:3.12-slim
WORKDIR /app
COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/api .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
