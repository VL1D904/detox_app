FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 
ENV DETOX_MODEL_PATH=/detox_app/models/detox_model
ENV DETOX_TOKENIZER_PATH=/detox_app/models/detox_tokenizer
ENV CLASSIFIER_MODEL_PATH=/detox_app/models/classifier_model
ENV CLASSIFIER_TOKENIZER_PATH=/detox_app/models/classifier_tokenizer
ENV SIMILARITY_MODEL_PATH=/detox_app/models/similarity_model

WORKDIR /detox_app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN python load_models.py

EXPOSE 8000
CMD ["gunicorn", "--bind", "127.0.0.1:8000", "--workers", "1", "wsgi:app"]
