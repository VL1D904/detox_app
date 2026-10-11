import transformers
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForSequenceClassification
from sentence_transformers import SentenceTransformer
import torch
from .model_exception import ModelException



# Класс для инференса нейросетевых моделей
class ModelsInference:
    # Инициализация моделей из локального хранилища
    def __init__(self, detox_model, detox_tokenizer, classifier_model, classifier_tokenizer, sim_model):
        try:
            self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'

            self.detox_model = AutoModelForSeq2SeqLM.from_pretrained(detox_model, local_files_only=True).to(self.device)
            self.detox_tokenizer = AutoTokenizer.from_pretrained(detox_tokenizer, local_files_only=True)

            self.classifier_model = AutoModelForSequenceClassification.from_pretrained(classifier_model, local_files_only=True).to(self.device)
            self.classifier_tokenizer = AutoTokenizer.from_pretrained(classifier_tokenizer, local_files_only=True)

            self.similarity_model = SentenceTransformer(sim_model, device=self.device, trust_remote_code=True, local_files_only=True)
        except OSError as error:
            raise ModelException("Ошибка подключения моделей") from error

    # Функция инференса модели детоксикации текста
    def detoxification_text(self, toxic_text):
        try:
            toxic_token = self.detox_tokenizer(toxic_text, max_length=32, padding=True, truncation=True, return_tensors='pt').to(self.device)
            prediction = self.detox_model.generate(**toxic_token)
            detox_text = self.detox_tokenizer.decode(prediction[0], skip_special_tokens=True)
            return detox_text
        except TypeError as error:
            raise ModelException("Ошибка модели детоксикации") from error

    # Функция инференса модели классификации токсичности текста
    def classifier_text(self, text):
        try:
            text_token = self.classifier_tokenizer(text, max_length=32, padding=True, truncation=True, return_tensors='pt').to(self.device)
            toxic_logits = self.classifier_model(**text_token).logits[:, 1]
            return torch.sigmoid(toxic_logits).item()
        except TypeError as error:
            raise ModelException("Ошибка модели классификации") from error

    # Функция инференса модели оценки смысловой схожести текстов
    def similarity_texts(self, toxic_text, neutral_text):
        try:
            toxic_embeddings = self.similarity_model.encode(toxic_text, normalize_embeddings=True)
            neutral_embeddings = self.similarity_model.encode(neutral_text, normalize_embeddings=True)
            similarity = self.similarity_model.similarity(toxic_embeddings, neutral_embeddings)
            return similarity.item()
        except TypeError as error:
            raise ModelException("Ошибка ембеддинговой модели") from error

