import spacy
import re
import json
import yaml
from typing import Dict, List, Tuple

class EntityExtractor:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Загрузка модели NER
        self.ner_model = spacy.load(self.config.get('ner_model', 'ru_core_news_sm'))
        
        # Загрузка датасета сущностей
        self.entity_patterns = self._load_entity_patterns()
        
        # Регулярные выражения для извлечения сущностей
        self.patterns = self._compile_patterns()
    
    def _load_entity_patterns(self) -> Dict:
        """Загрузка паттернов сущностей"""
        try:
            with open('modules/text_understander/training_data/entities_dataset.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"entities": []}
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Компиляция regex паттернов для сущностей"""
        patterns = {}
        
        # Паттерны для дат
        patterns['date'] = re.compile(r'\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{1,2}\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{2,4})\b', re.IGNORECASE)
        
        # Паттерны для времени
        patterns['time'] = re.compile(r'\b(\d{1,2}:\d{2}(?::\d{2})?\s*(?:утра|вечера|AM|PM)?)\b', re.IGNORECASE)
        
        # Паттерны для email
        patterns['email'] = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # Паттерны для телефонов
        patterns['phone'] = re.compile(r'\b(?:\+7|8)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}\b')
        
        return patterns
    
    def extract(self, text: str, nlp_result: Dict = None) -> List[Dict]:
        """Извлечение сущностей из текста"""
        entities = []
        
        # Извлечение с помощью модели NER
        doc = self.ner_model(text)
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "source": "ner_model"
            })
        
        # Извлечение с помощью regex паттернов
        entities.extend(self._extract_with_patterns(text))
        
        # Извлечение с помощью кастомных паттернов из датасета
        entities.extend(self._extract_custom_entities(text))
        
        return entities
    
    def _extract_with_patterns(self, text: str) -> List[Dict]:
        """Извлечение сущностей с помощью regex"""
        entities = []
        
        for entity_type, pattern in self.patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                entities.append({
                    "text": match.group(),
                    "label": entity_type,
                    "start": match.start(),
                    "end": match.end(),
                    "source": "regex"
                })
        
        return entities
    
    def _extract_custom_entities(self, text: str) -> List[Dict]:
        """Извлечение кастомных сущностей из датасета"""
        entities = []
        text_lower = text.lower()
        
        for entity_data in self.entity_patterns.get('entities', []):
            entity_type = entity_data.get('type')
            patterns = entity_data.get('patterns', [])
            
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    start = text_lower.find(pattern.lower())
                    entities.append({
                        "text": text[start:start + len(pattern)],
                        "label": entity_type,
                        "start": start,
                        "end": start + len(pattern),
                        "source": "custom_dataset"
                    })
        
        return entities
    
    def add_entity_pattern(self, entity_type: str, patterns: List[str]):
        """Добавление нового паттерна сущности"""
        new_entity = {
            "type": entity_type,
            "patterns": patterns
        }
        self.entity_patterns['entities'].append(new_entity)
        
        # Сохранение обновленного датасета
        with open('modules/text_understander/training_data/entities_dataset.json', 'w', encoding='utf-8') as f:
            json.dump(self.entity_patterns, f, ensure_ascii=False, indent=2)