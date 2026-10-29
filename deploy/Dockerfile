# 红源智导 · 可部署镜像（零第三方依赖）
FROM python:3.12-slim

WORKDIR /app

# 运行必需文件（约 120 KB）
COPY run.py server.py ./
COPY agent ./agent
COPY data ./data
COPY web ./web

ENV PORT=8080 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8080

# 非 root 运行
RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=2)"

CMD ["python", "run.py", "--port", "8080"]
