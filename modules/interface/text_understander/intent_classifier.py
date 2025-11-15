import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import json
import yaml
from typing import Dict, List

class NeuralIntentClassifier(nn.Module):
    def __init__(self, input_size: int, num_intents: int):
        super(NeuralIntentClassifier, self).__init__()
        self.fc1 = nn.Linear(input_size, 512)
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, num_intents)
        self.dropout = nn.Dropout(0.3)
        self.relu = nn.ReLU()
    
    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return x

class IntentClassifier:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Загрузка датасета намерений
        self.intents = self._load_intents_dataset()
        
        # Инициализация модели
        self.model = None
        self.tokenizer = None
        self._initialize_model()
    
    def _load_intents_dataset(self) -> Dict:
        """Загрузка датасета намерений"""
        try:
            with open('modules/text_understander/training_data/intents_dataset.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"intents": []}
    
    def _initialize_model(self):
        """Инициализация модели классификации"""
        model_type = self.config.get('intent_model_type', 'bert')
        
        if model_type == 'bert':
            model_name = self.config.get('bert_model', 'bert-base-multilingual-uncased')
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name, 
                num_labels=len(self.intents.get('intents', []))
            )
        else:
            # Кастомная нейросеть
            input_size = self.config.get('input_size', 768)
            num_intents = len(self.intents.get('intents', []))
            self.model = NeuralIntentClassifier(input_size, num_intents)
    
    def classify(self, text: str, context: Dict = None) -> Dict:
        """Классификация намерения"""
        if self.model is None:
            return {"intent": "unknown", "confidence": 0.0}
        
        # Подготовка входных данных
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        
        # Предсказание
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.softmax(outputs.logits, dim=-1)
            confidence, predicted = torch.max(probabilities, 1)
        
        intent_idx = predicted.item()
        intents_list = self.intents.get('intents', [])
        
        if intent_idx < len(intents_list):
            intent_name = intents_list[intent_idx].get('tag', 'unknown')
        else:
            intent_name = 'unknown'
        
        return {
            "intent": intent_name,
            "confidence": confidence.item(),
            "all_probabilities": probabilities.tolist()[0]
        }
    
    def add_intent(self, tag: str, patterns: List[str], responses: List[str]):
        """Добавление нового намерения"""
        new_intent = {
            "tag": tag,
            "patterns": patterns,
            "responses": responses
        }
        self.intents['intents'].append(new_intent)
        
        # Сохранение обновленного датасета
        with open('modules/text_understander/training_data/intents_dataset.json', 'w', encoding='utf-8') as f:
            json.dump(self.intents, f, ensure_ascii=False, indent=2)