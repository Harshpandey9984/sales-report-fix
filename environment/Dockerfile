FROM python:3.12-slim

# Pin the test runner in the image so verification never depends on the network.
RUN pip install --no-cache-dir pytest==8.3.4

WORKDIR /app
COPY report.py sample.csv /app/
