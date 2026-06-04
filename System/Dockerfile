FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    libgomp1 \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir \
    torch \
    torchvision \
    --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir paddlepaddle

RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "from paddleocr import PaddleOCR; PaddleOCR(lang='en'); print('PaddleOCR models cached')"

COPY . .

EXPOSE 7860
CMD ["python", "-u", "app.py"]