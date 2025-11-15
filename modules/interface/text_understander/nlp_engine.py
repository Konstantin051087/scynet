import spacy
import yaml
from typing import Dict, List, Any

class NlpEngine:
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Загрузка модели spaCy
        model_name = self.config.get('spacy_model', 'ru_core_news_sm')
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            raise Exception(f"Модель spaCy '{model_name}' не найдена. Установите: python -m spacy download {model_name}")
        
        # Загрузка грамматических правил
        self.grammar_rules = self._load_grammar_rules()
    
    def _load_grammar_rules(self) -> Dict:
        """Загрузка правил грамматики из YAML"""
        try:
            with open('modules/text_understander/grammar_rules.yaml', 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}
    
    def process(self, text: str) -> Dict[str, Any]:
        """Основной метод обработки текста"""
        doc = self.nlp(text)
        
        return {
            "tokens": [token.text for token in doc],
            "lemmas": [token.lemma_ for token in doc],
            "pos_tags": [token.pos_ for token in doc],
            "syntax_tree": self._extract_syntax(doc),
            "dependencies": [(token.text, token.dep_, token.head.text) for token in doc],
            "language": self._detect_language(text),
            "grammar_check": self._check_grammar(doc)
        }
    
    def _extract_syntax(self, doc) -> List[Dict]:
        """Извлечение синтаксической структуры"""
        syntax = []
        for token in doc:
            syntax.append({
                "text": token.text,
                "lemma": token.lemma_,
                "pos": token.pos_,
                "dep": token.dep_,
                "head": token.head.text,
                "children": [child.text for child in token.children]
            })
        return syntax
    
    def _detect_language(self, text: str) -> str:
        """Определение языка текста"""
        # Простая эвристика для русского/английского
        ru_chars = len([c for c in text if 'а' <= c <= 'я' or 'А' <= c <= 'Я'])
        en_chars = len([c for c in text if 'a' <= c <= 'z' or 'A' <= c <= 'Z'])
        
        if ru_chars > en_chars:
            return "ru"
        else:
            return "en"
    
    def _check_grammar(self, doc) -> List[Dict]:
        """Проверка грамматики на основе правил"""
        issues = []
        for token in doc:
            # Пример проверки: существительное должно иметь правильный падеж
            if token.pos_ == "NOUN" and token.dep_ == "nsubj":
                # Проверка согласования подлежащего и сказуемого
                pass
        return issues