FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt \
    & sudo apt-get install wkhtmltopdf

CMD ["python", "main.py"]