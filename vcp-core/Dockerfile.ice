FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN useradd --uid 10001 --create-home ice
COPY independent_certifier.py ice_security.py /app/
RUN python -m pip install --no-cache-dir 'fastapi>=0.115,<1' 'uvicorn>=0.30,<1' 'cryptography>=43,<47'
RUN mkdir -p /var/lib/ice && chown ice:ice /var/lib/ice
USER ice
EXPOSE 8796
CMD ["uvicorn","independent_certifier:app","--host","0.0.0.0","--port","8796","--proxy-headers","--forwarded-allow-ips","127.0.0.1"]
