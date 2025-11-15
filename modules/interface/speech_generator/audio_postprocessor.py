"""
ПОСТПРОЦЕССОР АУДИО
Обработка сгенерированного аудио: шумоподавление, нормализация, эффекты
"""

import os
import tempfile
import logging
from typing import Dict, Any, Optional
import numpy as np

try:
    import librosa
    import soundfile as sf
    HAS_AUDIO_LIBS = True
except ImportError:
    HAS_AUDIO_LIBS = False
    logging.warning("Библиотеки librosa/soundfile не установлены, аудиообработка ограничена")

class AudioPostprocessor:
    """Постпроцессор аудио сигналов"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Параметры обработки
        self.processing_params = {
            'normalization': config.get('normalization', True),
            'noise_reduction': config.get('noise_reduction', True),
            'compression': config.get('compression', True),
            'equalization': config.get('equalization', True),
            'reverb': config.get('reverb', False)
        }
        
        # Настройки эффектов для разных эмоций
        self.emotional_effects = {
            'happy': {
                'brightness_boost': 1.2,
                'reverb_level': 0.1,
                'compression_ratio': 2.0
            },
            'sad': {
                'brightness_boost': 0.8,
                'reverb_level': 0.3,
                'compression_ratio': 1.5
            },
            'angry': {
                'brightness_boost': 1.1,
                'reverb_level': 0.05,
                'compression_ratio': 3.0
            },
            'neutral': {
                'brightness_boost': 1.0,
                'reverb_level': 0.0,
                'compression_ratio': 2.0
            }
        }
        
        self.logger.info("Аудио постпроцессор инициализирован")
    
    def process(self, audio_path: str, emotion: str = 'neutral') -> str:
        """
        Обработка аудиофайла
        
        Args:
            audio_path: Путь к исходному аудиофайлу
            emotion: Эмоция для применения эффектов
            
        Returns:
            Путь к обработанному аудиофайлу
        """
        if not HAS_AUDIO_LIBS:
            self.logger.warning("Библиотеки аудиообработки недоступны, возвращаем исходный файл")
            return audio_path
        
        try:
            # Загрузка аудио
            audio_data, sample_rate = self._load_audio(audio_path)
            
            if audio_data is None:
                return audio_path
            
            # Применение обработки
            processed_audio = audio_data
            
            if self.processing_params['normalization']:
                processed_audio = self._normalize_audio(processed_audio)
            
            if self.processing_params['noise_reduction']:
                processed_audio = self._reduce_noise(processed_audio, sample_rate)
            
            if self.processing_params['equalization']:
                processed_audio = self._apply_equalization(processed_audio, sample_rate, emotion)
            
            if self.processing_params['compression']:
                processed_audio = self._apply_compression(processed_audio, emotion)
            
            if self.processing_params['reverb']:
                processed_audio = self._apply_reverb(processed_audio, sample_rate, emotion)
            
            # Сохранение обработанного аудио
            output_path = self._save_processed_audio(processed_audio, sample_rate, audio_path)
            
            self.logger.debug(f"Аудио обработано: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки аудио: {str(e)}")
            return audio_path
    
    def _load_audio(self, audio_path: str) -> tuple:
        """Загрузка аудиофайла"""
        try:
            if not os.path.exists(audio_path):
                self.logger.error(f"Аудиофайл не найден: {audio_path}")
                return None, None
            
            audio_data, sample_rate = librosa.load(audio_path, sr=None)
            return audio_data, sample_rate
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки аудио: {str(e)}")
            return None, None
    
    def _normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Нормализация громкости аудио"""
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            return audio_data / max_val * 0.9  # Оставляем запас 10%
        return audio_data
    
    def _reduce_noise(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Подавление шума"""
        try:
            # Простой фильтр низких частот для подавления высокочастотного шума
            from scipy import signal
            
            # Создание ФНЧ Баттерворта
            nyquist = sample_rate / 2
            cutoff = 8000  # Частота среза 8 kHz
            normal_cutoff = cutoff / nyquist
            b, a = signal.butter(4, normal_cutoff, btype='low', analog=False)
            
            filtered_audio = signal.filtfilt(b, a, audio_data)
            return filtered_audio
            
        except ImportError:
            self.logger.warning("Scipy не установлен, пропускаем подавление шума")
            return audio_data
    
    def _apply_equalization(self, audio_data: np.ndarray, sample_rate: int, 
                          emotion: str) -> np.ndarray:
        """Применение эквалайзера в зависимости от эмоции"""
        emotional_effect = self.emotional_effects.get(
            emotion, 
            self.emotional_effects['neutral']
        )
        brightness_boost = emotional_effect.get('brightness_boost', 1.0)
        
        try:
            # Простая частотная коррекция
            stft = librosa.stft(audio_data)
            
            # Усиление высоких частот для "яркости"
            if brightness_boost > 1.0:
                freq_bins = stft.shape[0]
                boost_start_bin = int(freq_bins * 0.6)  # Усиливаем верхние 40% частот
                
                for i in range(boost_start_bin, freq_bins):
                    stft[i] *= brightness_boost
            
            processed_audio = librosa.istft(stft)
            return processed_audio
            
        except Exception as e:
            self.logger.warning(f"Ошибка эквализации: {str(e)}")
            return audio_data
    
    def _apply_compression(self, audio_data: np.ndarray, emotion: str) -> np.ndarray:
        """Применение компрессии"""
        emotional_effect = self.emotional_effects.get(
            emotion, 
            self.emotional_effects['neutral']
        )
        compression_ratio = emotional_effect.get('compression_ratio', 2.0)
        
        # Простая мягкая компрессия
        threshold = 0.5
        compressed_audio = np.copy(audio_data)
        
        # Компрессия пиков выше порога
        above_threshold = np.abs(audio_data) > threshold
        compressed_audio[above_threshold] = (
            threshold + (audio_data[above_threshold] - threshold) / compression_ratio
        )
        
        return compressed_audio
    
    def _apply_reverb(self, audio_data: np.ndarray, sample_rate: int, 
                     emotion: str) -> np.ndarray:
        """Применение реверберации"""
        emotional_effect = self.emotional_effects.get(
            emotion, 
            self.emotional_effects['neutral']
        )
        reverb_level = emotional_effect.get('reverb_level', 0.0)
        
        if reverb_level <= 0:
            return audio_data
        
        try:
            # Простой ревербератор с задержкой
            delay_samples = int(0.03 * sample_rate)  # 30ms delay
            decay = 0.5
            
            # Создание задержанного сигнала
            delayed = np.zeros_like(audio_data)
            delayed[delay_samples:] = audio_data[:-delay_samples] * decay
            
            # Смешивание с оригиналом
            wet_mix = reverb_level
            dry_mix = 1.0 - wet_mix
            
            reverberated_audio = dry_mix * audio_data + wet_mix * delayed
            return reverberated_audio
            
        except Exception as e:
            self.logger.warning(f"Ошибка применения реверберации: {str(e)}")
            return audio_data
    
    def _save_processed_audio(self, audio_data: np.ndarray, sample_rate: int, 
                            original_path: str) -> str:
        """Сохранение обработанного аудио"""
        try:
            # Создание временного файла для результата
            temp_file = tempfile.NamedTemporaryFile(
                suffix='_processed.wav', 
                delete=False
            )
            output_path = temp_file.name
            temp_file.close()
            
            # Сохранение с оригинальным sample rate
            sf.write(output_path, audio_data, sample_rate)
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения обработанного аудио: {str(e)}")
            return original_path
    
    def enable_processing_step(self, step: str, enable: bool = True):
        """Включение/выключение шага обработки"""
        if step in self.processing_params:
            self.processing_params[step] = enable
            self.logger.info(f"Шаг обработки '{step}' {'включен' if enable else 'выключен'}")
    
    def add_custom_effect(self, effect_name: str, parameters: Dict[str, Any]):
        """Добавление пользовательского эффекта"""
        self.emotional_effects[effect_name] = parameters
        self.logger.info(f"Добавлен пользовательский эффект: {effect_name}")