FROM golang:1.23-alpine AS builder

ENV GOTOOLCHAIN=auto

RUN apk add --no-cache git ca-certificates

RUN go install -v github.com/itszeeshan/subdomainx@v1.5.0 && \
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest && \
    go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /go/bin/subdomainx /usr/local/bin/
COPY --from=builder /go/bin/subfinder /usr/local/bin/
COPY --from=builder /go/bin/httpx /usr/local/bin/
COPY --from=builder /go/bin/nuclei /usr/local/bin/

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
WORKDIR /app

EXPOSE 8000

CMD ["sh", "-c", "subdomainx serve --port 8081 --api-key ${SUBDOMAINX_API_KEY:-dev-key} --output /tmp/scans & sleep 2 && uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
