"""
Тренер для самообучения модели на новых акцентах и словах
"""

import torch
import numpy as np
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime
from .model import SpeechRecognitionModel

class SpeechTrainer:
    def __init__(self, model: SpeechRecognitionModel):
        """
        Инициализация тренера
        
        Args:
            model: Модель распознавания речи для обучения
        """
        self.model = model
        self.logger = logging.getLogger(__name__)
        self.training_data = []
        self.performance_metrics = {}
        
    def load_training_data(self, data_path: Path) -> bool:
        """
        Загрузка данных для обучения
        
        Args:
            data_path: Путь к данным обучения
            
        Returns:
            Успешность загрузки
        """
        try:
            if data_path.suffix == '.json':
                with open(data_path, 'r', encoding='utf-8') as f:
                    self.training_data = json.load(f)
            elif data_path.suffix == '.txt':
                with open(data_path, 'r', encoding='utf-8') as f:
                    self.training_data = [line.strip() for line in f if line.strip()]
            
            self.logger.info(f"Загружено {len(self.training_data)} примеров для обучения")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки данных обучения: {e}")
            return False
    
    def fine_tune_accent(self, 
                        audio_samples: List[np.ndarray],
                        transcripts: List[str],
                        accent_type: str,
                        epochs: int = 3,
                        learning_rate: float = 1e-5) -> Dict[str, Any]:
        """
        Тонкая настройка под конкретный акцент
        
        Args:
            audio_samples: Список аудио семплов
            transcripts: Соответствующие транскрипты
            accent_type: Тип акцента (russian_regional, english_regional, etc.)
            epochs: Количество эпох
            learning_rate: Скорость обучения
            
        Returns:
            Метрики обучения
        """
        self.logger.info(f"Начало тонкой настройки для акцента: {accent_type}")
        
        metrics = {
            "accent_type": accent_type,
            "start_time": datetime.now().isoformat(),
            "epochs": epochs,
            "learning_rate": learning_rate,
            "samples_count": len(audio_samples),
            "loss_history": [],
            "accuracy_history": []
        }
        
        try:
            # Здесь должна быть реализация тонкой настройки модели
            # В текущей версии это заглушка
            
            for epoch in range(epochs):
                epoch_loss = self._simulate_training_epoch(audio_samples, transcripts, learning_rate)
                epoch_accuracy = self._calculate_accuracy(audio_samples, transcripts)
                
                metrics["loss_history"].append(epoch_loss)
                metrics["accuracy_history"].append(epoch_accuracy)
                
                self.logger.info(f"Эпоха {epoch+1}/{epochs}: loss={epoch_loss:.4f}, accuracy={epoch_accuracy:.4f}")
            
            metrics["end_time"] = datetime.now().isoformat()
            metrics["final_accuracy"] = metrics["accuracy_history"][-1]
            
            # Сохранение обученной модели
            self._save_accent_model(accent_type, metrics)
            
            self.logger.info(f"Тонкая настройка завершена. Финальная точность: {metrics['final_accuracy']:.4f}")
            
        except Exception as e:
            self.logger.error(f"Ошибка тонкой настройки: {e}")
            metrics["error"] = str(e)
        
        return metrics
    
    def _simulate_training_epoch(self, 
                               audio_samples: List[np.ndarray],
                               transcripts: List[str],
                               learning_rate: float) -> float:
        """
        Симуляция эпохи обучения (заглушка)
        В реальной реализации здесь будет работа с моделью Whisper
        """
        # Имитация процесса обучения
        base_loss = 0.5
        improvement = 0.1 * learning_rate * 1000
        return max(0.1, base_loss - improvement)
    
    def _calculate_accuracy(self, 
                          audio_samples: List[np.ndarray], 
                          transcripts: List[str]) -> float:
        """
        Расчет точности на валидационных данных
        """
        if not audio_samples:
            return 0.0
            
        correct = 0
        for audio, true_text in zip(audio_samples[:10], transcripts[:10]):  # Тестируем на 10 примерах
            try:
                result = self.model.transcribe(audio)
                predicted_text = result["text"].lower().strip()
                if predicted_text == true_text.lower().strip():
                    correct += 1
            except:
                continue
        
        return correct / min(10, len(audio_samples))
    
    def _save_accent_model(self, accent_type: str, metrics: Dict[str, Any]):
        """
        Сохранение модели для конкретного акцента
        """
        accents_dir = Path(__file__).parent / "vocabulary" / "accents"
        accents_dir.mkdir(parents=True, exist_ok=True)
        
        accent_file = accents_dir / f"{accent_type}_accent.db"
        
        accent_data = {
            "accent_type": accent_type,
            "training_metrics": metrics,
            "trained_at": datetime.now().isoformat(),
            "model_parameters": {
                "model_size": self.model.model_size,
                "custom_words": list(self.model.custom_words)
            }
        }
        
        try:
            with open(accent_file, 'w', encoding='utf-8') as f:
                json.dump(accent_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Модель акцента сохранена: {accent_file}")
        except Exception as e:
            self.logger.error(f"Ошибка сохранения модели акцента: {e}")
    
    def add_custom_word(self, word: str, pronunciation: Optional[str] = None):
        """
        Добавление пользовательского слова в словарь
        
        Args:
            word: Пользовательское слово
            pronunciation: Вариант произношения (опционально)
        """
        try:
            custom_words_dir = Path(__file__).parent / "vocabulary" / "custom_words"
            custom_words_dir.mkdir(parents=True, exist_ok=True)
            
            custom_file = custom_words_dir / "user_added.txt"
            
            # Добавление слова в множество
            self.model.custom_words.add(word)
            
            # Сохранение в файл
            with open(custom_file, 'a', encoding='utf-8') as f:
                if pronunciation:
                    f.write(f"{word}|{pronunciation}\n")
                else:
                    f.write(f"{word}\n")
            
            self.logger.info(f"Добавлено пользовательское слово: {word}")
            
        except Exception as e:
            self.logger.error(f"Ошибка добавления пользовательского слова: {e}")
    
    def evaluate_model(self, test_audio: List[np.ndarray], test_transcripts: List[str]) -> Dict[str, float]:
        """
        Оценка производительности модели
        
        Args:
            test_audio: Тестовые аудио данные
            test_transcripts: Эталонные транскрипты
            
        Returns:
            Метрики оценки
        """
        self.logger.info("Начало оценки модели")
        
        metrics = {
            "total_samples": len(test_audio),
            "processed_samples": 0,
            "word_accuracy": 0.0,
            "sentence_accuracy": 0.0,
            "average_confidence": 0.0,
            "processing_time": 0.0
        }
        
        correct_sentences = 0
        total_words_correct = 0
        total_words = 0
        total_confidence = 0.0
        
        import time
        start_time = time.time()
        
        for i, (audio, true_text) in enumerate(zip(test_audio, test_transcripts)):
            try:
                result = self.model.transcribe(audio)
                predicted_text = result["text"].strip()
                confidence = result["confidence"]
                
                # Точность на уровне предложения
                if predicted_text.lower() == true_text.lower():
                    correct_sentences += 1
                
                # Точность на уровне слов
                true_words = true_text.lower().split()
                pred_words = predicted_text.lower().split()
                
                # Подсчет совпадающих слов
                correct_words = sum(1 for tw, pw in zip(true_words, pred_words) if tw == pw)
                total_words_correct += correct_words
                total_words += len(true_words)
                
                total_confidence += confidence
                metrics["processed_samples"] += 1
                
            except Exception as e:
                self.logger.warning(f"Ошибка обработки примера {i}: {e}")
                continue
        
        end_time = time.time()
        metrics["processing_time"] = end_time - start_time
        
        if metrics["processed_samples"] > 0:
            metrics["sentence_accuracy"] = correct_sentences / metrics["processed_samples"]
            metrics["word_accuracy"] = total_words_correct / total_words if total_words > 0 else 0.0
            metrics["average_confidence"] = total_confidence / metrics["processed_samples"]
        
        self.logger.info(f"Оценка завершена: {metrics}")
        return metrics