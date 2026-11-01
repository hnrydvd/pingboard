FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

RUN useradd --uid 10001 --no-create-home app
USER 10001

# -u: unbuffered output so logs show up in `docker compose logs` immediately
CMD ["python", "-u", "worker.py"]
