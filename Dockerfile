FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt \
    && apt update \
    && apt install wkhtmltopdf

CMD ["python", "main.py"]