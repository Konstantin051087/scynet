"""
СИНТЕЗАТОР ГОЛОСА
Управление голосовыми профилями и характеристиками голоса
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import numpy as np

class VoiceSynthesizer:
    """Синтезатор голосовых характеристик"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Базовая директория голосовых профилей
        self.voice_profiles_dir = config.get('voice_profiles_dir', 'voice_profiles')
        
        # Загрузка голосовых профилей
        self.voice_profiles = self._load_voice_profiles()
        
        # Текущие параметры голоса
        self.current_parameters = {
            'pitch': config.get('base_pitch', 1.0),
            'timbre': config.get('base_timbre', 1.0),
            'resonance': config.get('resonance', 1.0),
            'breathiness': config.get('breathiness', 0.1),
            'brightness': config.get('brightness', 0.5)
        }
        
        self.logger.info("Синтезатор голоса инициализирован")
    
    def _load_voice_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Загрузка всех голосовых профилей"""
        profiles = {}
        
        if not os.path.exists(self.voice_profiles_dir):
            self.logger.warning(f"Директория голосовых профилей не найдена: {self.voice_profiles_dir}")
            return profiles
        
        # Рекурсивный поиск файлов .vpr
        for root, dirs, files in os.walk(self.voice_profiles_dir):
            for file in files:
                if file.endswith('.vpr'):
                    profile_path = os.path.join(root, file)
                    profile_name = os.path.relpath(profile_path, self.voice_profiles_dir)
                    profile_name = profile_name.replace('.vpr', '').replace('\\', '/')
                    
                    try:
                        with open(profile_path, 'r', encoding='utf-8') as f:
                            profile_data = json.load(f)
                        
                        profiles[profile_name] = profile_data
                        self.logger.debug(f"Загружен голосовой профиль: {profile_name}")
                        
                    except Exception as e:
                        self.logger.error(f"Ошибка загрузки профиля {profile_path}: {str(e)}")
        
        # Создание базовых профилей, если директория пуста
        if not profiles:
            self._create_default_profiles()
            profiles = self._load_voice_profiles()
        
        return profiles
    
    def _create_default_profiles(self):
        """Создание базовых голосовых профилей по умолчанию"""
        default_profiles = {
            'neutral/male_neutral': {
                'name': 'Мужской нейтральный',
                'gender': 'male',
                'age_group': 'adult',
                'pitch': 0.8,
                'timbre': 1.0,
                'resonance': 0.9,
                'breathiness': 0.05,
                'brightness': 0.4,
                'description': 'Стандартный мужской голос'
            },
            'neutral/female_neutral': {
                'name': 'Женский нейтральный',
                'gender': 'female',
                'age_group': 'adult',
                'pitch': 1.2,
                'timbre': 1.1,
                'resonance': 1.0,
                'breathiness': 0.08,
                'brightness': 0.6,
                'description': 'Стандартный женский голос'
            },
            'emotional/happy_voice': {
                'name': 'Радостный голос',
                'gender': 'neutral',
                'age_group': 'adult',
                'pitch': 1.3,
                'timbre': 1.2,
                'resonance': 1.1,
                'breathiness': 0.1,
                'brightness': 0.8,
                'description': 'Энергичный и позитивный голос'
            },
            'emotional/sad_voice': {
                'name': 'Грустный голос',
                'gender': 'neutral',
                'age_group': 'adult',
                'pitch': 0.7,
                'timbre': 0.8,
                'resonance': 0.7,
                'breathiness': 0.15,
                'brightness': 0.3,
                'description': 'Тихий и меланхоличный голос'
            },
            'emotional/angry_voice': {
                'name': 'Сердитый голос',
                'gender': 'neutral',
                'age_group': 'adult',
                'pitch': 1.1,
                'timbre': 1.3,
                'resonance': 1.2,
                'breathiness': 0.02,
                'brightness': 0.5,
                'description': 'Напряженный и агрессивный голос'
            }
        }
        
        # Создание директорий и файлов
        for profile_path, profile_data in default_profiles.items():
            full_path = os.path.join(self.voice_profiles_dir, profile_path + '.vpr')
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info("Созданы голосовые профили по умолчанию")
    
    def synthesize(self, text: str, voice_profile: str) -> str:
        """
        Синтез голоса с использованием указанного профиля
        
        Args:
            text: Текст для синтеза
            voice_profile: Имя голосового профиля
            
        Returns:
            Идентификатор синтезированного голоса
        """
        if voice_profile not in self.voice_profiles:
            self.logger.warning(f"Голосовой профиль {voice_profile} не найден, используется нейтральный")
            voice_profile = 'neutral/male_neutral'
        
        profile = self.voice_profiles[voice_profile]
        
        # Применение параметров профиля
        self.current_parameters.update({
            k: v for k, v in profile.items() 
            if k in self.current_parameters
        })
        
        self.logger.debug(f"Применен голосовой профиль: {voice_profile}")
        
        # Здесь будет реальный синтез голоса
        # Пока возвращаем идентификатор профиля
        return f"voice_{hash(voice_profile) % 10000:04d}"
    
    def get_available_profiles(self) -> List[Dict[str, Any]]:
        """Получить список доступных голосовых профилей"""
        profiles = []
        
        for profile_id, profile_data in self.voice_profiles.items():
            profile_info = {
                'id': profile_id,
                'name': profile_data.get('name', profile_id),
                'gender': profile_data.get('gender', 'unknown'),
                'age_group': profile_data.get('age_group', 'adult'),
                'description': profile_data.get('description', '')
            }
            profiles.append(profile_info)
        
        return profiles
    
    def create_custom_profile(self, profile_name: str, parameters: Dict[str, Any]) -> bool:
        """
        Создание пользовательского голосового профиля
        
        Args:
            profile_name: Имя профиля
            parameters: Параметры голоса
            
        Returns:
            Успешность создания
        """
        try:
            # Проверка обязательных параметров
            required_params = ['name', 'pitch', 'timbre']
            for param in required_params:
                if param not in parameters:
                    raise ValueError(f"Отсутствует обязательный параметр: {param}")
            
            # Сохранение профиля
            profile_path = os.path.join(self.voice_profiles_dir, 'custom', profile_name + '.vpr')
            os.makedirs(os.path.dirname(profile_path), exist_ok=True)
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(parameters, f, ensure_ascii=False, indent=2)
            
            # Перезагрузка профилей
            self.voice_profiles = self._load_voice_profiles()
            
            self.logger.info(f"Создан пользовательский голосовой профиль: {profile_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка создания профиля {profile_name}: {str(e)}")
            return False
    
    def update_parameters(self, parameters: Dict[str, Any]):
        """Обновление текущих параметров голоса"""
        self.current_parameters.update(parameters)
        self.logger.debug("Параметры голоса обновлены")
    
    def get_current_parameters(self) -> Dict[str, Any]:
        """Получить текущие параметры голоса"""
        return self.current_parameters.copy()