FROM python:3.12-alpine

WORKDIR /app

RUN apk add --no-cache --virtual .build-deps gcc musl-dev && \
    pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps

COPY main.py .

CMD ["python", "-u", "main.py"]
