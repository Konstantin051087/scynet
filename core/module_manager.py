"""
Менеджер загрузки и выгрузки модулей
Управляет жизненным циклом всех модулей системы
"""

import asyncio
import logging
import importlib
from typing import Dict, Any, List, Optional, Type
from pathlib import Path
import yaml
import json

class ModuleManager:
    """Менеджер модулей системы"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('core.module_manager')
        
        # Реестр загруженных модулей
        self.loaded_modules: Dict[str, Any] = {}
        
        # Состояния модулей
        self.module_states: Dict[str, str] = {}  # 'loaded', 'initialized', 'error', 'unloaded'
        
        # Зависимости между модулями
        self.module_dependencies: Dict[str, List[str]] = {}
        
        self.is_initialized = False

    async def initialize(self):
        """Инициализация менеджера модулей"""
        try:
            # Загрузка конфигурации модулей
            await self._load_module_configs()
            
            # Загрузка обязательных модулей
            required_modules = self.config.get('required_modules', [])
            for module_name in required_modules:
                await self.load_module(module_name)
            
            self.is_initialized = True
            self.logger.info("Менеджер модулей инициализирован")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации менеджера модулей: {e}")
            raise

    async def load_module(self, module_name: str, module_config: Dict[str, Any] = None) -> bool:
        """
        Загрузка модуля по имени
        
        Args:
            module_name: Имя модуля для загрузки
            module_config: Конфигурация модуля (если None - загружается из файла)
            
        Returns:
            True если модуль успешно загружен
        """
        if module_name in self.loaded_modules:
            self.logger.warning(f"Модуль {module_name} уже загружен")
            return True
        
        try:
            self.logger.info(f"Загрузка модуля: {module_name}")
            
            # Получаем конфигурацию модуля
            if module_config is None:
                module_config = await self._get_module_config(module_name)
            
            # Проверяем зависимости
            dependencies = module_config.get('dependencies', [])
            for dep in dependencies:
                if dep not in self.loaded_modules:
                    self.logger.info(f"Загрузка зависимости {dep} для модуля {module_name}")
                    await self.load_module(dep)
            
            # Динамическая загрузка модуля
            module_class = await self._import_module_class(module_name, module_config)
            
            # Создаем экземпляр модуля
            module_instance = module_class(module_config)
            
            # Инициализация модуля
            await module_instance.initialize()
            
            # Регистрируем модуль
            self.loaded_modules[module_name] = module_instance
            self.module_states[module_name] = 'initialized'
            
            self.logger.info(f"Модуль {module_name} успешно загружен и инициализирован")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модуля {module_name}: {e}")
            self.module_states[module_name] = 'error'
            return False

    async def unload_module(self, module_name: str) -> bool:
        """
        Выгрузка модуля
        
        Args:
            module_name: Имя модуля для выгрузки
            
        Returns:
            True если модуль успешно выгружен
        """
        if module_name not in self.loaded_modules:
            self.logger.warning(f"Модуль {module_name} не загружен")
            return True
        
        try:
            self.logger.info(f"Выгрузка модуля: {module_name}")
            
            # Проверяем зависимости других модулей
            dependent_modules = []
            for other_module, deps in self.module_dependencies.items():
                if module_name in deps and other_module in self.loaded_modules:
                    dependent_modules.append(other_module)
            
            if dependent_modules:
                self.logger.warning(f"Модуль {module_name} требуется для: {dependent_modules}")
                return False
            
            # Корректное завершение работы модуля
            module_instance = self.loaded_modules[module_name]
            if hasattr(module_instance, 'shutdown'):
                await module_instance.shutdown()
            
            # Удаляем из реестра
            del self.loaded_modules[module_name]
            self.module_states[module_name] = 'unloaded'
            
            self.logger.info(f"Модуль {module_name} успешно выгружен")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка выгрузки модуля {module_name}: {e}")
            return False

    async def reload_module(self, module_name: str) -> bool:
        """
        Перезагрузка модуля
        
        Args:
            module_name: Имя модуля для перезагрузки
            
        Returns:
            True если модуль успешно перезагружен
        """
        self.logger.info(f"Перезагрузка модуля: {module_name}")
        
        # Сохраняем конфигурацию
        module_config = self.config.get('modules', {}).get(module_name, {})
        
        # Выгружаем и загружаем заново
        if await self.unload_module(module_name):
            return await self.load_module(module_name, module_config)
        
        return False

    async def get_module(self, module_name: str) -> Optional[Any]:
        """
        Получение экземпляра модуля
        
        Args:
            module_name: Имя модуля
            
        Returns:
            Экземпляр модуля или None если не найден
        """
        return self.loaded_modules.get(module_name)

    async def get_module_status(self, module_name: str) -> Dict[str, Any]:
        """
        Получение статуса модуля
        
        Args:
            module_name: Имя модуля
            
        Returns:
            Статус модуля
        """
        if module_name not in self.loaded_modules:
            return {'status': 'not_loaded'}
        
        module_instance = self.loaded_modules[module_name]
        status = {
            'status': self.module_states.get(module_name, 'unknown'),
            'name': module_name
        }
        
        # Дополнительная информация от модуля если доступна
        if hasattr(module_instance, 'get_status'):
            try:
                module_status = await module_instance.get_status()
                status.update(module_status)
            except Exception as e:
                self.logger.warning(f"Не удалось получить статус модуля {module_name}: {e}")
        
        return status

    async def get_all_modules_status(self) -> Dict[str, Dict[str, Any]]:
        """Получение статуса всех модулей"""
        status = {}
        for module_name in self.loaded_modules.keys():
            status[module_name] = await self.get_module_status(module_name)
        return status

    async def _import_module_class(self, module_name: str, module_config: Dict[str, Any]) -> Type:
        """
        Динамический импорт класса модуля
        
        Args:
            module_name: Имя модуля
            module_config: Конфигурация модуля
            
        Returns:
            Класс модуля
        """
        try:
            # Определяем путь к модулю
            module_path = module_config.get('path', f"modules.{module_name}")
            class_name = module_config.get('class_name', f"{module_name.capitalize()}Module")
            
            # Импортируем модуль
            module = importlib.import_module(module_path)
            
            # Получаем класс
            module_class = getattr(module, class_name)
            
            return module_class
            
        except ImportError as e:
            self.logger.error(f"Не удалось импортировать модуль {module_name}: {e}")
            raise
        except AttributeError as e:
            self.logger.error(f"Не найден класс {class_name} в модуле {module_path}: {e}")
            raise

    async def _load_module_configs(self):
        """Загрузка конфигураций всех модулей"""
        modules_config_path = Path('config/modules/')
        
        if modules_config_path.exists():
            for config_file in modules_config_path.glob('*.yaml'):
                module_name = config_file.stem
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        module_config = yaml.safe_load(f)
                    
                    # Сохраняем в общую конфигурацию
                    if 'modules' not in self.config:
                        self.config['modules'] = {}
                    self.config['modules'][module_name] = module_config
                    
                    # Сохраняем зависимости
                    if 'dependencies' in module_config:
                        self.module_dependencies[module_name] = module_config['dependencies']
                    
                    self.logger.debug(f"Загружена конфигурация модуля: {module_name}")
                    
                except Exception as e:
                    self.logger.error(f"Ошибка загрузки конфигурации {config_file}: {e}")
        
        self.logger.info("Конфигурации модулей загружены")

    async def _get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Получение конфигурации модуля"""
        return self.config.get('modules', {}).get(module_name, {})

    async def update_module_config(self, module_name: str, new_config: Dict[str, Any]):
        """
        Обновление конфигурации модуля
        
        Args:
            module_name: Имя модуля
            new_config: Новая конфигурация
        """
        if 'modules' not in self.config:
            self.config['modules'] = {}
        
        self.config['modules'][module_name] = new_config
        
        # Если модуль загружен - перезагружаем его
        if module_name in self.loaded_modules:
            self.logger.info(f"Обновление конфигурации и перезагрузка модуля: {module_name}")
            await self.reload_module(module_name)
        
        self.logger.info(f"Конфигурация модуля {module_name} обновлена")

    async def shutdown(self):
        """Корректное завершение работы всех модулей"""
        self.logger.info("Завершение работы всех модулей")
        
        # Выгружаем модули в обратном порядке для учета зависимостей
        modules_to_unload = list(self.loaded_modules.keys())[::-1]
        
        for module_name in modules_to_unload:
            try:
                await self.unload_module(module_name)
            except Exception as e:
                self.logger.error(f"Ошибка при выгрузке модуля {module_name}: {e}")
        
        self.is_initialized = False
        self.logger.info("Все модули выгружены")

    async def get_manager_stats(self) -> Dict[str, Any]:
        """Получение статистики менеджера модулей"""
        return {
            'loaded_modules_count': len(self.loaded_modules),
            'available_modules': list(self.loaded_modules.keys()),
            'module_states': self.module_states,
            'is_initialized': self.is_initialized
        }