"""
Модуль распознавания речи (Speech Recognizer)
Орган слуха системы - преобразует аудио в текст
"""

from .model import SpeechRecognitionModel
from .trainer import SpeechTrainer
from .audio_preprocessor import AudioPreprocessor
from .api_interface import SpeechAPIInterface

__version__ = "1.0.0"
__author__ = "Synthetic Mind Team"
__all__ = ['SpeechRecognitionModel', 'SpeechTrainer', 'AudioPreprocessor', 'SpeechAPIInterface']
