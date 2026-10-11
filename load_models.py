import transformers
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForSequenceClassification
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os

load_dotenv()
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

# Пути сохранения моделей локально
DETOX_MODEL_PATH = os.getenv("DETOX_MODEL_PATH")
DETOX_TOKENIZER_PATH = os.getenv("DETOX_TOKENIZER_PATH")
CLASSIFIER_MODEL_PATH = os.getenv("CLASSIFIER_MODEL_PATH")
CLASSIFIER_TOKENIZER_PATH = os.getenv("CLASSIFIER_TOKENIZER_PATH")
SIMILARITY_MODEL_PATH = os.getenv("SIMILARITY_MODEL_PATH")

# Ссылки на репозитории hugging face для загрузки моделей
DETOX_MODEL_URL = 'vl1d/detoxic_model'
DETOX_TOKENIZER_URL = 'facebook/nllb-200-distilled-600M'
CLASSIFIER_MODEL_URL = 's-nlp/russian_toxicity_classifier'
CLASSIFIER_TOKENIZER_URL = 's-nlp/russian_toxicity_classifier'
SIMILARITY_MODEL_URL = 'Alibaba-NLP/gte-multilingual-base'

# Функция предварительного скачивания моделей в локальное хранилище
def load_and_save_models():
    if not os.path.exists(DETOX_MODEL_PATH):
        print("Скачивание модели детоксикации")
        detox_model = AutoModelForSeq2SeqLM.from_pretrained(DETOX_MODEL_URL)
        detox_model.save_pretrained(DETOX_MODEL_PATH)
        print("Скачивание модели детоксикации завершено успешно!")
    else:
        print(f"Директория модели детоксикации {DETOX_MODEL_PATH} уже существует")

    if not os.path.exists(DETOX_TOKENIZER_PATH):
        print("Скачивание токенизатора детоксикации")
        detox_tokenizer = AutoTokenizer.from_pretrained(DETOX_TOKENIZER_URL)
        detox_tokenizer.save_pretrained(DETOX_TOKENIZER_PATH)
        print("Скачивание токенизатора детоксикации завершено успешно!")
    else:
        print(f"Директория токенизатора детоксикации {DETOX_TOKENIZER_PATH} уже существует")

    if not os.path.exists(CLASSIFIER_MODEL_PATH):
            print("Скачивание модели классификатора токсичности")
            classifier_model = AutoModelForSequenceClassification.from_pretrained(CLASSIFIER_MODEL_URL)
            classifier_model.save_pretrained(CLASSIFIER_MODEL_PATH)
            print("Скачивание модели классификатора токсичности завершено успешно!")
    else:
        print(f"Директория модели классификатора токсичности {CLASSIFIER_MODEL_PATH} уже существует")

    if not os.path.exists(CLASSIFIER_TOKENIZER_PATH):
            print("Скачивание токенизатора классификатора токсичности")
            classifier_tokenizer = AutoTokenizer.from_pretrained(CLASSIFIER_TOKENIZER_URL)
            classifier_tokenizer.save_pretrained(CLASSIFIER_TOKENIZER_PATH)
            print("Скачивание токенизатора классификатора токсичности завершено успешно!")
    else:
        print(f"Директория токенизатора классификатора токсичности {CLASSIFIER_TOKENIZER_PATH} уже существует")

    if not os.path.exists(SIMILARITY_MODEL_PATH):
            print("Скачивание модели оценки смысловой схожести")
            similarity_model = SentenceTransformer(SIMILARITY_MODEL_URL, trust_remote_code=True)
            similarity_model.save(SIMILARITY_MODEL_PATH)
            print("Скачивание модели оценки смысловой схожести завершено успешно!")
    else:
        print(f"Директория модели оценки смысловой схожести {SIMILARITY_MODEL_PATH} уже существует")
    

if __name__ == "__main__":
    load_and_save_models()