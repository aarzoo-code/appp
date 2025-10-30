FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
# This image is an example runner that would execute jobs in a sandboxed container.
# In production, build a smaller runtime with only required packages.
CMD ["python3", "-u", "backend/scripts/worker.py"]
