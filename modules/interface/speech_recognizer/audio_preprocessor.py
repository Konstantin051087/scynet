"""
Препроцессор аудио данных
Подготовка аудио для распознавания: нормализация, фильтрация, усиление
"""

import numpy as np
import librosa
import scipy.signal as signal
from typing import Optional, Tuple, Union, Dict
import logging
from pathlib import Path

class AudioPreprocessor:
    def __init__(self, target_sr: int = 16000, chunk_duration: float = 30.0):
        """
        Инициализация аудио препроцессора
        
        Args:
            target_sr: Целевая частота дискретизации (Гц)
            chunk_duration: Длительность чанков для обработки (секунды)
        """
        self.target_sr = target_sr
        self.chunk_duration = chunk_duration
        self.logger = logging.getLogger(__name__)
    
    def load_audio(self, 
                  file_path: Union[str, Path], 
                  sr: Optional[int] = None) -> Tuple[np.ndarray, int]:
        """
        Загрузка аудио файла
        
        Args:
            file_path: Путь к аудио файлу
            sr: Частота дискретизации (None для оригинальной)
            
        Returns:
            Аудио данные и частота дискретизации
        """
        try:
            if sr is None:
                sr = self.target_sr
                
            audio, original_sr = librosa.load(file_path, sr=sr, mono=True)
            self.logger.info(f"Аудио загружено: {file_path}, SR: {original_sr}, Длина: {len(audio)/original_sr:.2f}с")
            
            return audio, original_sr
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки аудио {file_path}: {e}")
            raise
    
    def preprocess(self, 
                  audio: np.ndarray, 
                  original_sr: int,
                  apply_filters: bool = True) -> np.ndarray:
        """
        Основная препроцессорная обработка аудио
        
        Args:
            audio: Входные аудио данные
            original_sr: Исходная частота дискретизации
            apply_filters: Применять ли фильтры
            
        Returns:
            Обработанные аудио данные
        """
        # 1. Ресемплинг до целевой частоты
        if original_sr != self.target_sr:
            audio = self.resample_audio(audio, original_sr, self.target_sr)
        
        # 2. Нормализация амплитуды
        audio = self.normalize_amplitude(audio)
        
        # 3. Удаление тишины
        audio = self.remove_silence(audio)
        
        if apply_filters:
            # 4. Применение фильтров
            audio = self.apply_bandpass_filter(audio, lowcut=300, highcut=8000)
            
            # 5. Шумоподавление
            audio = self.reduce_noise(audio)
            
            # 6. Эквалайзер
            audio = self.apply_equalizer(audio)
        
        # 7. Финальная нормализация
        audio = self.normalize_amplitude(audio)
        
        return audio
    
    def resample_audio(self, audio: np.ndarray, original_sr: int, target_sr: int) -> np.ndarray:
        """Ресемплинг аудио до целевой частоты"""
        if original_sr == target_sr:
            return audio
            
        duration = len(audio) / original_sr
        target_length = int(duration * target_sr)
        
        resampled_audio = signal.resample(audio, target_length)
        self.logger.debug(f"Ресемплинг: {original_sr}Гц -> {target_sr}Гц")
        
        return resampled_audio
    
    def normalize_amplitude(self, audio: np.ndarray, target_level: float = 0.1) -> np.ndarray:
        """Нормализация амплитуды аудио"""
        if np.max(np.abs(audio)) == 0:
            return audio
            
        # Пиковая нормализация
        peak = np.max(np.abs(audio))
        normalized = audio * (target_level / peak)
        
        # RMS нормализация
        rms = np.sqrt(np.mean(normalized**2))
        if rms > 0:
            normalized = normalized * (0.1 / rms)  # Целевой RMS = 0.1
        
        return np.clip(normalized, -1.0, 1.0)
    
    def remove_silence(self, 
                      audio: np.ndarray, 
                      threshold: float = 0.01,
                      min_silence_duration: float = 0.1) -> np.ndarray:
        """Удаление участков тишины"""
        if len(audio) == 0:
            return audio
            
        # Поиск не тихих участков
        frame_length = int(self.target_sr * 0.01)  # 10ms frames
        hop_length = frame_length // 2
        
        energy = []
        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i:i + frame_length]
            frame_energy = np.sqrt(np.mean(frame**2))
            energy.append(frame_energy)
        
        if not energy:
            return audio
        
        # Применение порога
        min_silence_frames = int(min_silence_duration * self.target_sr / hop_length)
        voiced_frames = [e > threshold for e in energy]
        
        # Поиск границ речи
        speech_segments = []
        in_speech = False
        start_frame = 0
        
        for i, is_voiced in enumerate(voiced_frames):
            if is_voiced and not in_speech:
                start_frame = i
                in_speech = True
            elif not is_voiced and in_speech:
                if i - start_frame >= min_silence_frames:
                    speech_segments.append((start_frame, i))
                in_speech = False
        
        if in_speech:
            speech_segments.append((start_frame, len(voiced_frames)))
        
        # Сборка аудио без тишины
        if not speech_segments:
            return np.array([])
            
        speech_samples = []
        for start, end in speech_segments:
            start_sample = start * hop_length
            end_sample = min(end * hop_length + frame_length, len(audio))
            speech_samples.append(audio[start_sample:end_sample])
        
        if speech_samples:
            return np.concatenate(speech_samples)
        else:
            return np.array([])
    
    def apply_bandpass_filter(self, 
                            audio: np.ndarray, 
                            lowcut: float = 300, 
                            highcut: float = 8000) -> np.ndarray:
        """Применение полосового фильтра для речевого диапазона"""
        if len(audio) == 0:
            return audio
            
        nyquist = self.target_sr / 2
        low = lowcut / nyquist
        high = highcut / nyquist
        
        b, a = signal.butter(4, [low, high], btype='band')
        filtered_audio = signal.filtfilt(b, a, audio)
        
        return filtered_audio
    
    def reduce_noise(self, audio: np.ndarray, noise_reduction_db: float = 10.0) -> np.ndarray:
        """Подавление шума спектральным вычитанием"""
        if len(audio) == 0:
            return audio
            
        # Простая реализация спектрального вычитания
        frame_size = 512
        hop_size = frame_size // 2
        
        # Расчет спектрограммы
        stft = librosa.stft(audio, n_fft=frame_size, hop_length=hop_size)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Оценка шума (первые несколько кадров)
        noise_frames = min(10, magnitude.shape[1])
        noise_estimate = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)
        
        # Спектральное вычитание
        reduction_factor = 10**(noise_reduction_db / 20)
        cleaned_magnitude = magnitude - reduction_factor * noise_estimate
        cleaned_magnitude = np.maximum(cleaned_magnitude, 0.01 * magnitude)  # Ограничение снизу
        
        # Обратное преобразование
        cleaned_stft = cleaned_magnitude * np.exp(1j * phase)
        cleaned_audio = librosa.istft(cleaned_stft, hop_length=hop_size)
        
        # Обрезка до исходной длины
        if len(cleaned_audio) > len(audio):
            cleaned_audio = cleaned_audio[:len(audio)]
        elif len(cleaned_audio) < len(audio):
            cleaned_audio = np.pad(cleaned_audio, (0, len(audio) - len(cleaned_audio)))
        
        return cleaned_audio
    
    def apply_equalizer(self, audio: np.ndarray) -> np.ndarray:
        """Применение эквалайзера для улучшения речи"""
        if len(audio) == 0:
            return audio
            
        # Усиление частот важных для разборчивости речи
        frequencies = [100, 500, 1000, 2000, 4000, 8000]
        gains = [0.5, 1.2, 1.5, 1.8, 1.3, 0.8]  # Усиление в разных полосах
        
        for freq, gain in zip(frequencies, gains):
            if freq < self.target_sr / 2:
                q = 2.0  # Добротность
                b, a = signal.iirpeak(freq / (self.target_sr / 2), q, gain)
                audio = signal.filtfilt(b, a, audio)
        
        return audio
    
    def split_into_chunks(self, audio: np.ndarray, chunk_duration: Optional[float] = None) -> list:
        """
        Разделение длинного аудио на чанки
        
        Args:
            audio: Входное аудио
            chunk_duration: Длительность чанка в секундах
            
        Returns:
            Список аудио чанков
        """
        if chunk_duration is None:
            chunk_duration = self.chunk_duration
            
        chunk_samples = int(chunk_duration * self.target_sr)
        chunks = []
        
        for start in range(0, len(audio), chunk_samples):
            end = min(start + chunk_samples, len(audio))
            chunk = audio[start:end]
            
            # Добавление плавного перехода между чанками
            if len(chunk) == chunk_samples and end < len(audio):
                fade_samples = min(512, chunk_samples // 10)
                chunk[-fade_samples:] *= np.linspace(1, 0, fade_samples)
            
            chunks.append(chunk)
        
        self.logger.info(f"Аудио разделено на {len(chunks)} чанков по {chunk_duration}с")
        return chunks
    
    def extract_features(self, audio: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Извлечение признаков из аудио для анализа
        
        Args:
            audio: Входное аудио
            
        Returns:
            Словарь с признаками
        """
        features = {}
        
        # MFCC признаки
        mfcc = librosa.feature.mfcc(y=audio, sr=self.target_sr, n_mfcc=13)
        features['mfcc'] = mfcc
        
        # Спектральные центроиды
        spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=self.target_sr)
        features['spectral_centroid'] = spectral_centroids[0]
        
        # Темп
        tempo, _ = librosa.beat.beat_track(y=audio, sr=self.target_sr)
        features['tempo'] = tempo
        
        # Zero-crossing rate
        zcr = librosa.feature.zero_crossing_rate(audio)
        features['zero_crossing_rate'] = zcr[0]
        
        # RMS energy
        rms = librosa.feature.rms(y=audio)
        features['rms_energy'] = rms[0]
        
        return features