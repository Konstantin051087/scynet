"""
API интерфейс для общения с ядром системы
Обеспечивает интеграцию модуля распознавания речи с основной системой
"""

import asyncio
import aiohttp
from aiohttp import web
import json
import numpy as np
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
import base64
import io

from .model import SpeechRecognitionModel
from .audio_preprocessor import AudioPreprocessor

class SpeechAPIInterface:
    def __init__(self, config_path: Optional[Path] = None):
        """
        Инициализация API интерфейса
        
        Args:
            config_path: Путь к конфигурационному файлу
        """
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        
        # Инициализация компонентов
        self.model = SpeechRecognitionModel(
            model_size=self.config['model']['model_size'],
            device=self.config['model']['device']
        )
        
        self.preprocessor = AudioPreprocessor(
            target_sr=self.config['audio_processing']['target_sample_rate'],
            chunk_duration=self.config['audio_processing']['chunk_duration']
        )
        
        self.app = web.Application()
        self.setup_routes()
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.communication_bus_url = "http://localhost:8000"  # URL шины сообщений
        
    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Загрузка конфигурации"""
        default_config = {
            'api': {
                'host': 'localhost',
                'port': 8001,
                'max_workers': 4,
                'timeout': 30
            },
            'model': {
                'model_size': 'base',
                'device': 'auto'
            },
            'audio_processing': {
                'target_sample_rate': 16000,
                'chunk_duration': 30.0
            }
        }
        
        if config_path and config_path.exists():
            try:
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f)
                    # Рекурсивное обновление конфигурации
                    self._update_dict(default_config, loaded_config)
            except Exception as e:
                self.logger.warning(f"Не удалось загрузить конфиг {config_path}: {e}")
        
        return default_config
    
    def _update_dict(self, original: Dict, update: Dict):
        """Рекурсивное обновление словаря"""
        for key, value in update.items():
            if isinstance(value, dict) and key in original and isinstance(original[key], dict):
                self._update_dict(original[key], value)
            else:
                original[key] = value
    
    def setup_routes(self):
        """Настройка маршрутов API"""
        self.app.router.add_post('/transcribe', self.handle_transcription)
        self.app.router.add_post('/transcribe_file', self.handle_file_transcription)
        self.app.router.add_get('/health', self.handle_health_check)
        self.app.router.add_post('/detect_language', self.handle_language_detection)
        self.app.router.add_get('/status', self.handle_status)
        
    async def handle_transcription(self, request: web.Request) -> web.Response:
        """
        Обработка запроса транскрибации аудио данных
        """
        try:
            # Проверка Content-Type
            content_type = request.headers.get('Content-Type', '')
            
            if 'application/json' in content_type:
                data = await request.json()
                audio_data = self._decode_audio_data(data.get('audio_data'))
                language = data.get('language')
                prompt = data.get('prompt')
                
            elif 'multipart/form-data' in content_type:
                reader = await request.multipart()
                audio_field = await reader.next()
                
                if audio_field.name != 'audio_data':
                    return web.json_response(
                        {'error': 'Audio data field not found'}, 
                        status=400
                    )
                
                audio_bytes = await audio_field.read()
                audio_data = self._bytes_to_audio(audio_bytes)
                language = (await reader.next()).data.decode() if await reader.next() else None
                
            else:
                return web.json_response(
                    {'error': 'Unsupported Content-Type'}, 
                    status=415
                )
            
            # Выполнение транскрибации
            result = await self._transcribe_audio(audio_data, language, prompt)
            
            # Отправка результата в шину сообщений
            await self._send_to_communication_bus('speech_transcription_result', result)
            
            return web.json_response(result)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки транскрибации: {e}")
            return web.json_response(
                {'error': f'Transcription failed: {str(e)}'}, 
                status=500
            )
    
    async def handle_file_transcription(self, request: web.Request) -> web.Response:
        """
        Обработка транскрибации аудио файла
        """
        try:
            reader = await request.multipart()
            file_field = await reader.next()
            
            if file_field.name != 'file':
                return web.json_response(
                    {'error': 'File field not found'}, 
                    status=400
                )
            
            # Чтение файла
            file_content = await file_field.read()
            file_name = file_field.filename
            
            # Определение формата файла
            file_ext = Path(file_name).suffix.lower()
            supported_formats = ['.wav', '.mp3', '.flac', '.ogg', '.m4a']
            
            if file_ext not in supported_formats:
                return web.json_response(
                    {'error': f'Unsupported file format: {file_ext}'}, 
                    status=400
                )
            
            # Временное сохранение файла
            temp_dir = Path('temp')
            temp_dir.mkdir(exist_ok=True)
            temp_file = temp_dir / f"upload_{hash(file_content)}_{file_name}"
            
            with open(temp_file, 'wb') as f:
                f.write(file_content)
            
            try:
                # Загрузка и обработка аудио
                audio_data, original_sr = self.preprocessor.load_audio(temp_file)
                processed_audio = self.preprocessor.preprocess(audio_data, original_sr)
                
                # Транскрибация
                language = request.query.get('language')
                result = await self._transcribe_audio(processed_audio, language)
                
                # Очистка временного файла
                temp_file.unlink()
                
                return web.json_response(result)
                
            except Exception as e:
                # Очистка в случае ошибки
                if temp_file.exists():
                    temp_file.unlink()
                raise e
                
        except Exception as e:
            self.logger.error(f"Ошибка обработки файла: {e}")
            return web.json_response(
                {'error': f'File processing failed: {str(e)}'}, 
                status=500
            )
    
    async def handle_health_check(self, request: web.Request) -> web.Response:
        """Проверка здоровья модуля"""
        health_status = {
            'status': 'healthy',
            'module': 'speech_recognizer',
            'version': '1.0.0',
            'model_loaded': self.model.model is not None,
            'components': {
                'model': 'operational',
                'preprocessor': 'operational',
                'api': 'operational'
            },
            'timestamp': self._get_timestamp()
        }
        
        return web.json_response(health_status)
    
    async def handle_language_detection(self, request: web.Request) -> web.Response:
        """Определение языка речи"""
        try:
            data = await request.json()
            audio_data = self._decode_audio_data(data.get('audio_data'))
            
            language = self.model.detect_language(audio_data)
            
            result = {
                'detected_language': language,
                'confidence': 0.9,  # Заглушка для уверенности
                'timestamp': self._get_timestamp()
            }
            
            return web.json_response(result)
            
        except Exception as e:
            self.logger.error(f"Ошибка определения языка: {e}")
            return web.json_response(
                {'error': f'Language detection failed: {str(e)}'}, 
                status=500
            )
    
    async def handle_status(self, request: web.Request) -> web.Response:
        """Получение статуса модуля"""
        status = {
            'module': 'speech_recognizer',
            'status': 'running',
            'model_size': self.model.model_size,
            'device': self.model.device,
            'vocabulary_size': len(self.model.vocabulary),
            'custom_words_count': len(self.model.custom_words),
            'supported_languages': ['russian', 'english'],
            'timestamp': self._get_timestamp()
        }
        
        return web.json_response(status)
    
    def _decode_audio_data(self, audio_data: Any) -> np.ndarray:
        """Декодирование аудио данных из различных форматов"""
        if isinstance(audio_data, str):
            # Base64 encoded string
            audio_bytes = base64.b64decode(audio_data)
            return self._bytes_to_audio(audio_bytes)
        elif isinstance(audio_data, list):
            # List of numbers
            return np.array(audio_data, dtype=np.float32)
        else:
            raise ValueError(f"Unsupported audio data format: {type(audio_data)}")
    
    def _bytes_to_audio(self, audio_bytes: bytes) -> np.ndarray:
        """Конвертация bytes в numpy array"""
        import wave
        import io
        
        try:
            # Попытка загрузки как WAV
            with wave.open(io.BytesIO(audio_bytes)) as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                audio_data = np.frombuffer(frames, dtype=np.int16)
                return audio_data.astype(np.float32) / 32768.0
        except:
            # Если не WAV, используем librosa
            import librosa
            audio_data, _ = librosa.load(io.BytesIO(audio_bytes), sr=None)
            return audio_data
    
    async def _transcribe_audio(self, 
                              audio_data: np.ndarray, 
                              language: Optional[str] = None,
                              prompt: Optional[str] = None) -> Dict[str, Any]:
        """Асинхронная транскрибация аудио"""
        # Запуск в thread pool executor для избежания блокировки event loop
        loop = asyncio.get_event_loop()
        
        def sync_transcribe():
            return self.model.transcribe(audio_data, language, prompt)
        
        result = await loop.run_in_executor(None, sync_transcribe)
        return result
    
    async def _send_to_communication_bus(self, message_type: str, data: Dict[str, Any]):
        """Отправка сообщения в шину сообщений"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        
        message = {
            'type': message_type,
            'source': 'speech_recognizer',
            'timestamp': self._get_timestamp(),
            'data': data
        }
        
        try:
            async with self.session.post(
                f"{self.communication_bus_url}/message",
                json=message,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    self.logger.warning(f"Не удалось отправить сообщение в шину: {response.status}")
        except Exception as e:
            self.logger.error(f"Ошибка отправки в шину сообщений: {e}")
    
    def _get_timestamp(self) -> str:
        """Получение текущей временной метки"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def start(self):
        """Запуск API сервера"""
        # Загрузка модели
        self.logger.info("Загрузка модели распознавания речи...")
        self.model.load_model()
        
        # Запуск сервера
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(
            runner, 
            self.config['api']['host'], 
            self.config['api']['port']
        )
        
        await site.start()
        self.logger.info(f"Speech Recognizer API запущен на {self.config['api']['host']}:{self.config['api']['port']}")
    
    async def stop(self):
        """Остановка API сервера"""
        if self.session:
            await self.session.close()
        self.logger.info("Speech Recognizer API остановлен")