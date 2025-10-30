FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# install minimal build deps for some packages
RUN apt-get update && apt-get install -y --no-install-recommends build-essential ca-certificates && rm -rf /var/lib/apt/lists/*

# copy and install backend python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# copy app
COPY . /app

# make entrypoint executable
RUN chmod +x /app/entrypoint.sh || true

EXPOSE 5000

ENTRYPOINT ["/app/entrypoint.sh"]
