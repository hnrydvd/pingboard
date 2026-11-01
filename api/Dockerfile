# Starter single-stage image. Week 3-4 exercise:
#   1. `docker image ls` and note the size.
#   2. Convert to a multi-stage build (build wheels in stage 1, copy into a slim stage 2).
#   3. Compare sizes and layer counts (`docker history`), and write the numbers in the README.
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN useradd --uid 10001 --no-create-home app
USER 10001

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
