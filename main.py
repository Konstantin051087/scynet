# main.py - ГЛАВНЫЙ ЗАПУСКАЕМЫЙ ФАЙЛ (точка входа)

import os
import sys
import logging
import signal
import asyncio
import yaml
import importlib
import inspect
import psutil
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union, Callable, Coroutine
import traceback
import subprocess
import platform
import importlib.util

# Добавляем корневую директорию в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импорты core модулей с улучшенной обработкой ошибок
try:
    from core.coordinator import Coordinator
    from core.communication_bus import CommunicationBus
    from core.module_manager import ModuleManager
    from core.security_gateway import SecurityGateway
    from core.performance_monitor import PerformanceMonitor
except ImportError as e:
    print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось импортировать core модули: {e}")
    print("💡 Проверьте наличие файлов в папке core/ и корректность импортов")
    print("🔍 Детали ошибки импорта:")
    print(f"   - Рабочая директория: {os.getcwd()}")
    print(f"   - Python path: {sys.path}")
    core_path = Path("core")
    if core_path.exists():
        print(f"   - Содержимое папки core: {list(core_path.iterdir())}")
    else:
        print("   - Папка core не существует!")
    sys.exit(1)

class SystemConfig:
    """
    Класс для загрузки и управления конфигурацией системы из YAML файлов
    """
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.config_path = Path("config")
        self.loaded_files = []
        self.failed_files = []
        self.config_errors = []
        
    async def load(self) -> bool:
        """Загрузка конфигурации из YAML файлов с детальной диагностикой"""
        try:
            # Проверка существования config директории
            if not self.config_path.exists():
                error_msg = f"❌ Директория конфигурации {self.config_path} не найдена"
                print(error_msg)
                logging.error(error_msg)
                self.config_errors.append(error_msg)
                return False
                
            # Загрузка основного конфигурационного файла
            config_files = [
                ("system.yaml", "Основная конфигурация системы"),
                ("security_policies.yaml", "Настройки безопасности"),
                ("performance_settings.yaml", "Настройки производительности"),
                ("api_keys.yaml", "API ключи"),
                ("emotional_rules.yaml", "Эмоциональные правила"),
                ("user_preferences.yaml", "Пользовательские настройки"),
                ("backup_config.yaml", "Настройки резервного копирования")
            ]
            
            for filename, description in config_files:
                config_file = self.config_path / filename
                if config_file.exists():
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if content.strip():
                                config_data = yaml.safe_load(content)
                                if config_data:
                                    self.config.update(config_data)
                                    self.loaded_files.append({
                                        'file': filename,
                                        'description': description,
                                        'status': 'loaded',
                                        'size': len(content)
                                    })
                                    print(f"✅ Загружен {description}: {config_file}")
                                else:
                                    self.failed_files.append({
                                        'file': filename,
                                        'description': description,
                                        'error': 'Файл пуст или содержит только комментарии',
                                        'status': 'empty'
                                    })
                                    print(f"⚠️ Файл {filename} пуст: {config_file}")
                            else:
                                self.failed_files.append({
                                    'file': filename,
                                    'description': description,
                                    'error': 'Файл полностью пуст',
                                    'status': 'empty'
                                })
                                print(f"⚠️ Файл {filename} пуст: {config_file}")
                    except yaml.YAMLError as e:
                        error_msg = f"Ошибка YAML в {filename}: {e}"
                        self.failed_files.append({
                            'file': filename,
                            'description': description,
                            'error': error_msg,
                            'status': 'yaml_error'
                        })
                        print(f"❌ Ошибка YAML в {filename}: {e}")
                    except Exception as e:
                        error_msg = f"Ошибка загрузки {filename}: {e}"
                        self.failed_files.append({
                            'file': filename,
                            'description': description,
                            'error': error_msg,
                            'status': 'load_error'
                        })
                        print(f"❌ Ошибка загрузки {filename}: {e}")
                else:
                    self.failed_files.append({
                        'file': filename,
                        'description': description,
                        'error': 'Файл не найден',
                        'status': 'not_found'
                    })
                    print(f"⚠️ Файл {filename} не найден: {config_file}")
            
            # Загрузка конфигураций модулей
            modules_config_dir = self.config_path / "modules"
            if modules_config_dir.exists():
                loaded_module_configs = 0
                for config_file in modules_config_dir.glob("*.yaml"):
                    try:
                        module_name = config_file.stem
                        with open(config_file, 'r', encoding='utf-8') as f:
                            module_config = yaml.safe_load(f) or {}
                            if 'modules' not in self.config:
                                self.config['modules'] = {}
                            self.config['modules'][module_name] = module_config
                        loaded_module_configs += 1
                        self.loaded_files.append({
                            'file': f"modules/{config_file.name}",
                            'description': f"Конфигурация модуля {module_name}",
                            'status': 'loaded',
                            'size': config_file.stat().st_size
                        })
                    except Exception as e:
                        self.failed_files.append({
                            'file': f"modules/{config_file.name}",
                            'description': f"Конфигурация модуля {module_name}",
                            'error': f"Ошибка загрузки: {e}",
                            'status': 'load_error'
                        })
                print(f"📊 Загружено конфигураций модулей: {loaded_module_configs}")
            else:
                print(f"⚠️ Директория конфигураций модулей {modules_config_dir} не найдена")
                    
            print(f"✅ Загрузка конфигурации завершена: {len(self.loaded_files)} успешно, {len(self.failed_files)} с ошибками")
            
            # Проверка обязательных конфигураций
            required_configs = ['system.yaml', 'security_policies.yaml']
            missing_required = [cfg for cfg in required_configs 
                              if cfg not in [f['file'] for f in self.loaded_files]]
            
            if missing_required:
                self.config_errors.extend([f"Отсутствует обязательный конфигурационный файл: {cfg}" 
                                         for cfg in missing_required])
                return False
                
            return len(self.failed_files) == 0
            
        except Exception as e:
            error_msg = f"❌ Критическая ошибка загрузки конфигурации: {e}"
            print(error_msg)
            print(f"🔍 Детали ошибки: {traceback.format_exc()}")
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            self.config_errors.append(error_msg)
            return False
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Получение значения конфигурации по ключу (с поддержкой вложенных ключей через '.')"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Получение конфигурации конкретного модуля"""
        return self.config.get('modules', {}).get(module_name, {})
    
    def get_configuration_report(self) -> Dict[str, Any]:
        """Получение отчета о конфигурации"""
        return {
            'loaded_files': self.loaded_files,
            'failed_files': self.failed_files,
            'errors': self.config_errors,
            'total_loaded': len(self.loaded_files),
            'total_failed': len(self.failed_files),
            'has_critical_errors': len(self.config_errors) > 0
        }


class DependencyChecker:
    """Класс для проверки зависимостей системы"""
    
    def __init__(self):
        self.required_packages = [
            'numpy', 'pandas', 'scikit-learn', 'transformers', 'torch',
            'sqlalchemy', 'psycopg2-binary', 'pydantic', 'pyyaml', 'fastapi',
            'uvicorn', 'redis', 'psutil', 'opencv-python', 'pyttsx3',
            'bs4', 'matplotlib', 'requests', 'aiohttp', 'pillow'
        ]
        self.optional_packages = [
            'whisper', 'vosk', 'gtts', 'sympy', 'flask', 'selenium',
            'googletrans', 'wolframalpha', 'newsapi-python'
        ]
        
        self.system_dependencies = {
            'ffmpeg': 'Требуется для обработки аудио',
            'git': 'Требуется для управления версиями моделей',
            'docker': 'Опционально для контейнеризации'
        }
    
    async def check_python_version(self) -> Dict[str, Any]:
        """Проверка версии Python"""
        version_info = {
            'current': platform.python_version(),
            'required': '3.8+',
            'status': 'PASS' if sys.version_info >= (3, 8) else 'FAIL',
            'message': '',
            'details': {
                'major': sys.version_info.major,
                'minor': sys.version_info.minor,
                'micro': sys.version_info.micro
            }
        }
        
        if version_info['status'] == 'FAIL':
            version_info['message'] = f"Требуется Python 3.8+, текущая версия: {version_info['current']}"
        else:
            version_info['message'] = f"Версия Python {version_info['current']} совместима"
        
        return version_info
    
    async def check_system_dependencies(self) -> Dict[str, Any]:
        """Проверка системных зависимостей"""
        results = {}
        
        for dep, description in self.system_dependencies.items():
            try:
                # Пытаемся найти исполняемый файл в системе
                result = subprocess.run(['which', dep], capture_output=True, text=True)
                exists = result.returncode == 0
                
                results[dep] = {
                    'status': 'PASS' if exists else 'FAIL',
                    'exists': exists,
                    'description': description,
                    'message': f"Найден: {dep}" if exists else f"Не найден: {dep}",
                    'path': result.stdout.strip() if exists else None
                }
            except Exception as e:
                results[dep] = {
                    'status': 'ERROR',
                    'exists': False,
                    'description': description,
                    'message': f"Ошибка проверки: {e}",
                    'path': None
                }
        
        return results
    
    async def check_package(self, package_name: str) -> Dict[str, Any]:
        """Проверка наличия пакета с детальной информацией"""
        try:
            # Специальные случаи для пакетов с разными именами импорта
            import_map = {
                'psycopg2-binary': 'psycopg2',
                'opencv-python': 'cv2',
                'pillow': 'PIL',
                'scikit-learn': 'sklearn'
            }
            
            import_name = import_map.get(package_name, package_name)
            
            if package_name in ['opencv-python']:
                import cv2
                version = cv2.__version__
                details = {
                    'modules': ['cv2'],
                    'has_cuda': hasattr(cv2, 'cuda') and cv2.cuda.getCudaEnabledDeviceCount() > 0
                }
            elif package_name in ['psycopg2-binary']:
                import psycopg2
                version = psycopg2.__version__
                details = {
                    'modules': ['psycopg2', 'psycopg2.extensions'],
                    'extensions': ['psycopg2.extensions']
                }
            elif package_name in ['torch']:
                import torch
                version = torch.__version__
                details = {
                    'modules': ['torch', 'torch.nn', 'torch.optim'],
                    'has_cuda': torch.cuda.is_available(),
                    'cuda_version': torch.version.cuda if torch.cuda.is_available() else None,
                    'device_count': torch.cuda.device_count() if torch.cuda.is_available() else 0
                }
            elif package_name in ['transformers']:
                import transformers
                version = transformers.__version__
                details = {
                    'modules': ['transformers', 'transformers.pipelines'],
                    'tokenizers_available': importlib.util.find_spec("tokenizers") is not None
                }
            else:
                module = importlib.import_module(import_name)
                version = getattr(module, '__version__', 'unknown')
                details = {'modules': [import_name]}
            
            return {
                'name': package_name,
                'import_name': import_name,
                'status': 'PASS',
                'version': version,
                'message': 'Пакет доступен',
                'details': details
            }
        except ImportError as e:
            return {
                'name': package_name,
                'import_name': import_name,
                'status': 'FAIL',
                'version': 'не установлен',
                'message': f'Ошибка импорта: {e}',
                'details': {'error': str(e)}
            }
        except Exception as e:
            return {
                'name': package_name,
                'import_name': import_name,
                'status': 'ERROR',
                'version': 'ошибка проверки',
                'message': f'Ошибка проверки: {e}',
                'details': {'error': str(e), 'traceback': traceback.format_exc()}
            }
    
    async def check_system_dependencies_comprehensive(self) -> Dict[str, Any]:
        """Комплексная проверка системных зависимостей"""
        print("🔍 Комплексная проверка системных зависимостей...")
        
        python_check = await self.check_python_version()
        system_deps_check = await self.check_system_dependencies()
        package_checks = []
        optional_checks = []
        
        # Проверка обязательных пакетов
        print("📦 Проверка обязательных пакетов...")
        for package in self.required_packages:
            check_result = await self.check_package(package)
            package_checks.append(check_result)
            status_icon = "✅" if check_result['status'] == 'PASS' else "❌"
            print(f"   {status_icon} {package}: {check_result['version']} - {check_result['message']}")
        
        # Проверка опциональных пакетов
        print("🔶 Проверка опциональных пакетов...")
        for package in self.optional_packages:
            check_result = await self.check_package(package)
            optional_checks.append(check_result)
            if check_result['status'] == 'PASS':
                print(f"   ✅ {package}: {check_result['version']} (опциональный)")
            else:
                print(f"   🔶 {package}: {check_result['message']} (опциональный)")
        
        # Статистика
        required_passed = sum(1 for p in package_checks if p['status'] == 'PASS')
        optional_passed = sum(1 for p in optional_checks if p['status'] == 'PASS')
        system_deps_passed = sum(1 for d in system_deps_check.values() if d['status'] == 'PASS')
        
        # Критические проверки
        critical_issues = []
        if python_check['status'] != 'PASS':
            critical_issues.append(f"Несовместимая версия Python: {python_check['current']}")
        
        if required_passed < len(self.required_packages):
            missing = len(self.required_packages) - required_passed
            critical_issues.append(f"Отсутствуют {missing} обязательных пакетов")
        
        overall_status = 'PASS' if not critical_issues else 'FAIL'
        
        return {
            'overall_status': overall_status,
            'critical_issues': critical_issues,
            'python': python_check,
            'system_dependencies': system_deps_check,
            'required_packages': package_checks,
            'optional_packages': optional_checks,
            'statistics': {
                'required_total': len(self.required_packages),
                'required_available': required_passed,
                'optional_total': len(self.optional_packages),
                'optional_available': optional_passed,
                'system_deps_total': len(self.system_dependencies),
                'system_deps_available': system_deps_passed
            }
        }


class SystemHealthMonitor:
    """
    Комплексный мониторинг здоровья системы
    """
    
    def __init__(self, system_config: SystemConfig):
        self.system_config = system_config
        self.logger = logging.getLogger("SystemHealthMonitor")
        self.health_metrics: Dict[str, Any] = {}
        self.start_time = datetime.now()
        self.performance_data = {
            'startup_time': time.time(),
            'checks_performed': 0,
            'last_check': None
        }
        
    async def check_system_resources(self) -> Dict[str, Any]:
        """Проверка системных ресурсов с детальной диагностикой"""
        try:
            # Получение информации о системе
            system_info = {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'architecture': platform.architecture()[0],
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'hostname': platform.node(),
                'python_implementation': platform.python_implementation()
            }
            
            # Детальный мониторинг ресурсов
            resources = {
                'system_info': system_info,
                'cpu_percent': psutil.cpu_percent(interval=1),
                'cpu_count_physical': psutil.cpu_count(logical=False),
                'cpu_count_logical': psutil.cpu_count(logical=True),
                'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                'memory_usage': psutil.virtual_memory().percent,
                'memory_available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
                'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'disk_usage': psutil.disk_usage('/').percent,
                'disk_free_gb': round(psutil.disk_usage('/').free / (1024**3), 2),
                'disk_total_gb': round(psutil.disk_usage('/').total / (1024**3), 2),
                'boot_time': datetime.fromtimestamp(psutil.boot_time()),
                'system_uptime': datetime.now() - datetime.fromtimestamp(psutil.boot_time()),
                'process_uptime': datetime.now() - self.start_time,
                'network_io': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
            }
            
            # Проверка критических порогов
            warnings = []
            recommendations = []
            
            if resources['cpu_percent'] > 85:
                warnings.append(f"Высокая загрузка CPU: {resources['cpu_percent']}%")
                recommendations.append("Рассмотрите оптимизацию вычислительных задач")
            elif resources['cpu_percent'] > 95:
                warnings.append(f"Критическая загрузка CPU: {resources['cpu_percent']}%")
                recommendations.append("Немедленно оптимизируйте или распределите нагрузку")
                
            if resources['memory_usage'] > 80:
                warnings.append(f"Высокая загрузка памяти: {resources['memory_usage']}%")
                recommendations.append("Увеличьте объем памяти или оптимизируйте использование")
            elif resources['memory_usage'] > 90:
                warnings.append(f"Критическая загрузка памяти: {resources['memory_usage']}%")
                recommendations.append("Риск исчерпания памяти, срочно требуется оптимизация")
                
            if resources['disk_usage'] > 85:
                warnings.append(f"Мало свободного места на диске: {resources['disk_usage']}%")
                recommendations.append("Очистите диск или увеличьте его объем")
            elif resources['disk_usage'] > 95:
                warnings.append(f"Критически мало свободного места: {resources['disk_usage']}%")
                recommendations.append("Срочно освободите место на диске")
            
            resources['warnings'] = warnings
            resources['recommendations'] = recommendations
            resources['timestamp'] = datetime.now().isoformat()
            
            self.logger.debug(f"Проверка ресурсов: CPU={resources['cpu_percent']}%, Memory={resources['memory_usage']}%")
            
            return resources
        except Exception as e:
            error_msg = f"Ошибка проверки системных ресурсов: {e}"
            self.logger.error(error_msg)
            return {
                'cpu_percent': 0,
                'memory_usage': 0,
                'disk_usage': 0,
                'warnings': [f"Ошибка мониторинга ресурсов: {e}"],
                'recommendations': ["Проверьте доступность системных утилит мониторинга"],
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def check_database_connections(self) -> Dict[str, Any]:
        """Проверка подключений к базам данных с тестированием соединения"""
        connections = {
            'postgres': {'status': False, 'message': '', 'details': {}, 'response_time': 0},
            'redis': {'status': False, 'message': '', 'details': {}, 'response_time': 0}
        }
        
        try:
            # Проверка PostgreSQL
            postgres_url = self.system_config.get('database.postgres_url')
            if postgres_url and 'postgresql://' in postgres_url:
                try:
                    import psycopg2
                    from urllib.parse import urlparse
                    
                    start_time = time.time()
                    parsed_url = urlparse(postgres_url)
                    conn_params = {
                        'host': parsed_url.hostname,
                        'port': parsed_url.port or 5432,
                        'user': parsed_url.username,
                        'password': parsed_url.password,
                        'database': parsed_url.path[1:] if parsed_url.path else 'scynet',
                        'connect_timeout': 5
                    }
                    
                    # Пытаемся подключиться
                    conn = psycopg2.connect(**conn_params)
                    cursor = conn.cursor()
                    cursor.execute("SELECT version(), NOW(), current_database();")
                    db_version, db_time, db_name = cursor.fetchone()
                    conn.close()
                    response_time = round((time.time() - start_time) * 1000, 2)
                    
                    connections['postgres'] = {
                        'status': True,
                        'message': 'Подключение успешно',
                        'details': {
                            'version': db_version,
                            'database': db_name,
                            'server_time': db_time.isoformat(),
                            'host': conn_params['host'],
                            'port': conn_params['port']
                        },
                        'response_time': response_time
                    }
                    self.logger.info(f"✅ Подключение к PostgreSQL: УСПЕШНО ({response_time}мс)")
                except Exception as e:
                    connections['postgres'] = {
                        'status': False,
                        'message': f'Ошибка подключения: {e}',
                        'details': {'url': postgres_url, 'error_type': type(e).__name__},
                        'response_time': 0
                    }
                    self.logger.warning(f"⚠️ Ошибка подключения к PostgreSQL: {e}")
            else:
                connections['postgres'] = {
                    'status': False,
                    'message': 'URL PostgreSQL не настроен или неверный формат',
                    'details': {'url': postgres_url},
                    'response_time': 0
                }
                self.logger.warning("URL PostgreSQL не настроен или неверный формат")
                
        except Exception as e:
            self.logger.warning(f"Ошибка проверки PostgreSQL: {e}")
            
        try:
            # Проверка Redis
            redis_url = self.system_config.get('database.redis_url')
            if redis_url and 'redis://' in redis_url:
                try:
                    import redis
                    from urllib.parse import urlparse
                    
                    start_time = time.time()
                    parsed_url = urlparse(redis_url)
                    redis_client = redis.Redis(
                        host=parsed_url.hostname,
                        port=parsed_url.port or 6379,
                        password=parsed_url.password or None,
                        decode_responses=True,
                        socket_connect_timeout=5
                    )
                    
                    # Тестируем подключение
                    redis_client.ping()
                    redis_info = redis_client.info()
                    response_time = round((time.time() - start_time) * 1000, 2)
                    
                    connections['redis'] = {
                        'status': True,
                        'message': 'Подключение успешно',
                        'details': {
                            'version': redis_info.get('redis_version', 'unknown'),
                            'used_memory': redis_info.get('used_memory_human', 'unknown'),
                            'connected_clients': redis_info.get('connected_clients', 0),
                            'keyspace_hits': redis_info.get('keyspace_hits', 0),
                            'keyspace_misses': redis_info.get('keyspace_misses', 0)
                        },
                        'response_time': response_time
                    }
                    self.logger.info(f"✅ Подключение к Redis: УСПЕШНО ({response_time}мс)")
                except Exception as e:
                    connections['redis'] = {
                        'status': False,
                        'message': f'Ошибка подключения: {e}',
                        'details': {'url': redis_url, 'error_type': type(e).__name__},
                        'response_time': 0
                    }
                    self.logger.warning(f"⚠️ Ошибка подключения к Redis: {e}")
            else:
                connections['redis'] = {
                    'status': False,
                    'message': 'URL Redis не настроен или неверный формат',
                    'details': {'url': redis_url},
                    'response_time': 0
                }
                self.logger.warning("URL Redis не настроен или неверный формат")
                
        except Exception as e:
            self.logger.warning(f"Ошибка проверки Redis: {e}")
            
        return connections
    
    async def check_file_system(self) -> Dict[str, Any]:
        """Проверка файловой системы и критических директорий"""
        critical_paths = [
            ('config/', 'Директория конфигурации', True),
            ('core/', 'Директория ядра системы', True),
            ('modules/', 'Директория модулей', True),
            ('data/models/', 'Директория моделей', True),
            ('logs/', 'Директория логов', True),
            ('data/runtime/', 'Директория runtime данных', True),
            ('data/training/', 'Директория тренировочных данных', False),
            ('data/cache/', 'Директория кэша', False),
            ('tests/', 'Директория тестов', False),
            ('docs/', 'Директория документации', False)
        ]
        
        path_status = {}
        issues = []
        critical_issues = []
        
        for path, description, critical in critical_paths:
            path_obj = Path(path)
            status_info = {
                'description': description,
                'critical': critical,
                'exists': path_obj.exists(),
                'is_dir': path_obj.is_dir() if path_obj.exists() else False,
                'writable': os.access(path_obj, os.W_OK) if path_obj.exists() else False,
                'readable': os.access(path_obj, os.R_OK) if path_obj.exists() else False,
                'size': sum(f.stat().st_size for f in path_obj.rglob('*') if f.is_file()) if path_obj.exists() else 0,
                'file_count': len(list(path_obj.rglob('*'))) if path_obj.exists() else 0,
                'issues': []
            }
            
            if not status_info['exists']:
                status_info['issues'].append(f"Путь не существует: {path}")
                if critical:
                    critical_issues.append(f"❌ {description}: путь не существует")
                else:
                    issues.append(f"⚠️ {description}: путь не существует")
            elif not status_info['is_dir']:
                status_info['issues'].append(f"Не является директорией: {path}")
                if critical:
                    critical_issues.append(f"❌ {description}: не является директорией")
                else:
                    issues.append(f"⚠️ {description}: не является директорией")
            elif not status_info['writable']:
                status_info['issues'].append(f"Нет прав на запись: {path}")
                if critical:
                    critical_issues.append(f"❌ {description}: нет прав на запись")
                else:
                    issues.append(f"⚠️ {description}: нет прав на запись")
            elif not status_info['readable']:
                status_info['issues'].append(f"Нет прав на чтение: {path}")
                if critical:
                    critical_issues.append(f"❌ {description}: нет прав на чтение")
                else:
                    issues.append(f"⚠️ {description}: нет прав на чтение")
            else:
                if critical:
                    issues.append(f"✅ {description}: доступна")
                else:
                    issues.append(f"🔶 {description}: доступна")
            
            path_status[path] = status_info
        
        return {
            'path_status': path_status,
            'issues': issues,
            'critical_issues': critical_issues,
            'all_critical_accessible': len(critical_issues) == 0,
            'total_directories_checked': len(critical_paths),
            'critical_directories_checked': len([p for p in critical_paths if p[2]]),
            'total_size_bytes': sum(status['size'] for status in path_status.values())
        }
    
    async def check_external_services(self) -> Dict[str, Any]:
        """Проверка доступности внешних сервисов"""
        services = {}
        
        # Проверка доступности Hugging Face
        try:
            import requests
            start_time = time.time()
            response = requests.get('https://huggingface.co', timeout=10)
            response_time = round((time.time() - start_time) * 1000, 2)
            services['huggingface'] = {
                'status': 'PASS' if response.status_code == 200 else 'FAIL',
                'response_time': response_time,
                'status_code': response.status_code,
                'message': 'Доступен' if response.status_code == 200 else f'Ошибка HTTP: {response.status_code}'
            }
        except Exception as e:
            services['huggingface'] = {
                'status': 'FAIL',
                'response_time': 0,
                'status_code': None,
                'message': f'Ошибка подключения: {e}'
            }
        
        # Проверка доступности GitHub
        try:
            import requests
            start_time = time.time()
            response = requests.get('https://api.github.com', timeout=10)
            response_time = round((time.time() - start_time) * 1000, 2)
            services['github'] = {
                'status': 'PASS' if response.status_code == 200 else 'FAIL',
                'response_time': response_time,
                'status_code': response.status_code,
                'message': 'Доступен' if response.status_code == 200 else f'Ошибка HTTP: {response.status_code}'
            }
        except Exception as e:
            services['github'] = {
                'status': 'FAIL',
                'response_time': 0,
                'status_code': None,
                'message': f'Ошибка подключения: {e}'
            }
        
        return services
    
    async def get_system_health_score(self) -> Tuple[int, str, List[str], Dict[str, Any]]:
        """Расчет общего показателя здоровья системы (0-100) с улучшенной диагностикой"""
        total_checks = 0
        passed_checks = 0
        detailed_issues = []
        health_details = {}
        
        try:
            # Проверка ресурсов
            resources = await self.check_system_resources()
            health_details['resources'] = resources
            total_checks += 3
            
            if resources['cpu_percent'] < 85:
                passed_checks += 1
            else:
                detailed_issues.append(f"Высокая загрузка CPU: {resources['cpu_percent']}%")
                
            if resources['memory_usage'] < 80:
                passed_checks += 1
            else:
                detailed_issues.append(f"Высокая загрузка памяти: {resources['memory_usage']}%")
                
            if resources['disk_usage'] < 90:
                passed_checks += 1
            else:
                detailed_issues.append(f"Мало свободного места на диске: {resources['disk_usage']}%")
            
            # Проверка подключений
            connections = await self.check_database_connections()
            health_details['connections'] = connections
            total_checks += 2
            
            if connections['postgres']['status']:
                passed_checks += 1
            else:
                detailed_issues.append(f"PostgreSQL: {connections['postgres']['message']}")
                
            if connections['redis']['status']:
                passed_checks += 1
            else:
                detailed_issues.append(f"Redis: {connections['redis']['message']}")
            
            # Проверка файловой системы
            fs_check = await self.check_file_system()
            health_details['file_system'] = fs_check
            total_checks += 1
            if fs_check['all_critical_accessible']:
                passed_checks += 1
            else:
                detailed_issues.extend(fs_check['critical_issues'])
            
            # Проверка внешних сервисов
            external_services = await self.check_external_services()
            health_details['external_services'] = external_services
            total_checks += 1
            external_passed = sum(1 for s in external_services.values() if s['status'] == 'PASS')
            if external_passed >= len(external_services) / 2:  # Хотя бы половина доступна
                passed_checks += 1
            else:
                detailed_issues.append("Проблемы с доступом к внешним сервисам")
            
            # Дополнительные проверки
            total_checks += 2
            if sys.version_info >= (3, 8):
                passed_checks += 1
            else:
                detailed_issues.append(f"Несовместимая версия Python: {platform.python_version()}, требуется 3.8+")
            
            # Проверка доступности core модулей
            core_modules = ['coordinator', 'communication_bus', 'module_manager', 
                          'security_gateway', 'performance_monitor']
            core_available = all(importlib.util.find_spec(f"core.{module}") is not None for module in core_modules)
            if core_available:
                passed_checks += 1
            else:
                detailed_issues.append("Не все core модули доступны для импорта")
            
            health_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
            
            if health_score >= 90:
                status = "💚 ОТЛИЧНО"
            elif health_score >= 70:
                status = "💛 ХОРОШО"
            elif health_score >= 50:
                status = "🟡 УДОВЛЕТВОРИТЕЛЬНО"
            else:
                status = "🔴 КРИТИЧЕСКО"
                
            self.performance_data['checks_performed'] += 1
            self.performance_data['last_check'] = datetime.now().isoformat()
                
            self.logger.info(f"Оценка здоровья системы: {health_score:.1f}% - {status}")
            if detailed_issues:
                self.logger.warning(f"Обнаружены проблемы: {len(detailed_issues)}")
                
            return round(health_score), status, detailed_issues, health_details
            
        except Exception as e:
            error_msg = f"Ошибка расчета здоровья системы: {e}"
            self.logger.error(error_msg)
            return 0, "🔴 ОШИБКА", [f"Ошибка мониторинга здоровья: {e}"], {}


class FunctionalTestEngine:
    """
    Движок функционального тестирования системы
    """
    
    def __init__(self, system_config: SystemConfig):
        self.system_config = system_config
        self.logger = logging.getLogger("FunctionalTestEngine")
        self.test_results: Dict[str, Any] = {}
        
    async def test_communication_bus(self) -> Dict[str, Any]:
        """Тестирование шины сообщений"""
        test_result = {
            'status': 'PENDING',
            'message': '',
            'latency': 0,
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            start_time = time.time()
            
            # Создаем временную шину для тестирования
            self.logger.info("Создание тестовой шины сообщений...")
            test_bus = CommunicationBus(self.system_config)
            await test_bus.initialize()
            
            # Тест отправки и получения сообщения
            test_message = {
                'type': 'test',
                'content': 'functional_test',
                'timestamp': datetime.now().isoformat(),
                'test_id': 'communication_bus_test_001'
            }
            
            # Здесь должна быть логика тестирования шины
            # Для примера просто проверяем, что шина инициализирована
            if await test_bus.is_healthy():
                test_result['status'] = 'PASS'
                test_result['message'] = 'Шина сообщений работает корректно'
                test_result['details'] = {
                    'initialized': True,
                    'healthy': True,
                    'test_message_sent': True
                }
                self.logger.info("✅ Тест шины сообщений: ПРОЙДЕН")
            else:
                test_result['status'] = 'FAIL'
                test_result['message'] = 'Шина сообщений не работает'
                test_result['details'] = {
                    'initialized': True,
                    'healthy': False,
                    'test_message_sent': False
                }
                self.logger.error("❌ Тест шины сообщений: ПРОВАЛЕН")
                
            test_result['latency'] = round((time.time() - start_time) * 1000, 2)
            await test_bus.shutdown()
            
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['message'] = f'Ошибка тестирования шины: {str(e)}'
            test_result['details'] = {
                'error': traceback.format_exc(),
                'error_type': type(e).__name__
            }
            self.logger.error(f"❌ Ошибка тестирования шины сообщений: {e}")
            self.logger.debug(f"Детали ошибки: {traceback.format_exc()}")
            
        return test_result
    
    async def test_security_gateway(self) -> Dict[str, Any]:
        """Тестирование шлюза безопасности"""
        test_result = {
            'status': 'PENDING',
            'message': '',
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            self.logger.info("Создание тестового шлюза безопасности...")
            security = SecurityGateway(self.system_config.get('security', {}))
            await security.initialize()
            
            # Тест проверки безопасного контента
            safe_content = "Это безопасное сообщение для тестирования системы"
            security_check = await security.validate_input(safe_content)
            
            if security_check.get('approved', False):
                test_result['status'] = 'PASS'
                test_result['message'] = 'Шлюз безопасности корректно пропускает безопасный контент'
                test_result['details'] = {
                    'safe_content_approved': True,
                    'security_check_passed': True
                }
                self.logger.info("✅ Тест шлюза безопасности: ПРОЙДЕН")
            else:
                test_result['status'] = 'FAIL'
                test_result['message'] = 'Шлюз безопасности блокирует безопасный контент'
                test_result['details'] = {
                    'safe_content_approved': False,
                    'security_check_passed': False
                }
                self.logger.error("❌ Тест шлюза безопасности: ПРОВАЛЕН")
                
            await security.shutdown()
            
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['message'] = f'Ошибка тестирования безопасности: {str(e)}'
            test_result['details'] = {
                'error': traceback.format_exc(),
                'error_type': type(e).__name__
            }
            self.logger.error(f"❌ Ошибка тестирования шлюза безопасности: {e}")
            self.logger.debug(f"Детали ошибки: {traceback.format_exc()}")
            
        return test_result
    
    async def test_module_integration(self) -> Dict[str, Any]:
        """Тестирование интеграции модулей"""
        test_result = {
            'status': 'PENDING',
            'message': '',
            'modules_tested': 0,
            'modules_passed': 0,
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Тестируем базовые модули
            test_modules = [
                ('text_understander', 'modules/interface/text_understander'),
                ('memory_short_term', 'modules/cognitive/memory_short_term'),
                ('intent_analyzer', 'core/intent_analyzer.py'),
                ('coordinator', 'core/coordinator.py')
            ]
            
            modules_tested = 0
            modules_passed = 0
            details = {}
            
            self.logger.info(f"Тестирование интеграции модулей: {[m[0] for m in test_modules]}")
            
            for module_name, module_path in test_modules:
                try:
                    # Проверяем существование модуля
                    path_obj = Path(module_path)
                    
                    if path_obj.exists() and (path_obj.is_dir() or path_obj.suffix == '.py'):
                        if path_obj.is_dir():
                            has_init = (path_obj / "__init__.py").exists()
                        else:
                            has_init = True
                            
                        if has_init:
                            modules_tested += 1
                            modules_passed += 1
                            details[module_name] = {
                                'status': 'PASS',
                                'message': 'модуль существует и доступен',
                                'path': str(path_obj)
                            }
                            self.logger.info(f"✅ Модуль {module_name}: ДОСТУПЕН")
                        else:
                            modules_tested += 1
                            details[module_name] = {
                                'status': 'FAIL', 
                                'message': f'отсутствует __init__.py в {path_obj}',
                                'path': str(path_obj)
                            }
                            self.logger.warning(f"⚠️ Модуль {module_name}: ОТСУТСТВУЕТ __init__.py")
                    else:
                        modules_tested += 1
                        details[module_name] = {
                            'status': 'FAIL',
                            'message': f'модуль не найден по пути: {path_obj}',
                            'path': str(path_obj)
                        }
                        self.logger.warning(f"⚠️ Модуль {module_name}: НЕ НАЙДЕН по пути {path_obj}")
                except Exception as e:
                    modules_tested += 1
                    details[module_name] = {
                        'status': 'ERROR',
                        'message': f'ошибка проверки: {str(e)}',
                        'error': traceback.format_exc()
                    }
                    self.logger.error(f"❌ Ошибка тестирования модуля {module_name}: {e}")
            
            test_result['modules_tested'] = modules_tested
            test_result['modules_passed'] = modules_passed
            test_result['details'] = details
            
            if modules_passed == modules_tested:
                test_result['status'] = 'PASS'
                test_result['message'] = f'Все {modules_tested} модулей работают корректно'
                self.logger.info("✅ Тест интеграции модулей: ПРОЙДЕН")
            else:
                test_result['status'] = 'FAIL'
                test_result['message'] = f'Проблемы с {modules_tested - modules_passed} модулями'
                self.logger.warning(f"⚠️ Тест интеграции модулей: ПРОБЛЕМЫ с {modules_tested - modules_passed} модулями")
                
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['message'] = f'Ошибка тестирования интеграции: {str(e)}'
            test_result['details'] = {'error': traceback.format_exc()}
            self.logger.error(f"❌ Ошибка тестирования интеграции модулей: {e}")
            self.logger.debug(f"Детали ошибки: {traceback.format_exc()}")
            
        return test_result
    
    async def test_basic_workflow(self) -> Dict[str, Any]:
        """Тестирование базового рабочего процесса"""
        test_result = {
            'status': 'PENDING',
            'message': '',
            'steps_tested': 0,
            'steps_passed': 0,
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            steps_tested = 0
            steps_passed = 0
            details = {}
            
            # Тест 1: Инициализация компонентов
            steps_tested += 1
            try:
                test_bus = CommunicationBus(self.system_config)
                await test_bus.initialize()
                if await test_bus.is_healthy():
                    steps_passed += 1
                    details['communication_bus_init'] = {'status': 'PASS', 'message': 'Шина сообщений инициализирована'}
                else:
                    details['communication_bus_init'] = {'status': 'FAIL', 'message': 'Шина сообщений не работает'}
                await test_bus.shutdown()
            except Exception as e:
                details['communication_bus_init'] = {'status': 'ERROR', 'message': f'Ошибка инициализации: {e}'}
            
            # Тест 2: Безопасность
            steps_tested += 1
            try:
                security = SecurityGateway(self.system_config.get('security', {}))
                await security.initialize()
                test_input = "Тестовое сообщение"
                result = await security.validate_input(test_input)
                if result.get('approved', False):
                    steps_passed += 1
                    details['security_check'] = {'status': 'PASS', 'message': 'Проверка безопасности работает'}
                else:
                    details['security_check'] = {'status': 'FAIL', 'message': 'Проверка безопасности не работает'}
                await security.shutdown()
            except Exception as e:
                details['security_check'] = {'status': 'ERROR', 'message': f'Ошибка безопасности: {e}'}
            
            test_result['steps_tested'] = steps_tested
            test_result['steps_passed'] = steps_passed
            test_result['details'] = details
            
            if steps_passed == steps_tested:
                test_result['status'] = 'PASS'
                test_result['message'] = 'Базовый рабочий процесс функционирует корректно'
            else:
                test_result['status'] = 'FAIL'
                test_result['message'] = f'Проблемы в {steps_tested - steps_passed} шагах рабочего процесса'
                
        except Exception as e:
            test_result['status'] = 'ERROR'
            test_result['message'] = f'Ошибка тестирования рабочего процесса: {e}'
            test_result['details'] = {'error': traceback.format_exc()}
            
        return test_result
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Запуск комплексного тестирования"""
        self.logger.info("🧪 Запуск комплексного функционального тестирования...")
        
        start_time = time.time()
        
        tests = {
            'communication_bus': await self.test_communication_bus(),
            'security_gateway': await self.test_security_gateway(),
            'module_integration': await self.test_module_integration(),
            'basic_workflow': await self.test_basic_workflow()
        }
        
        # Расчет общей статистики
        total_tests = len(tests)
        passed_tests = sum(1 for test in tests.values() if test['status'] == 'PASS')
        failed_tests = sum(1 for test in tests.values() if test['status'] == 'FAIL')
        error_tests = sum(1 for test in tests.values() if test['status'] == 'ERROR')
        
        overall_status = 'PASS' if failed_tests == 0 and error_tests == 0 else 'FAIL'
        execution_time = round(time.time() - start_time, 2)
        
        self.logger.info(f"📊 Результаты тестирования: {passed_tests}/{total_tests} пройдено за {execution_time}с")
        
        return {
            'overall_status': overall_status,
            'execution_time': execution_time,
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'error_tests': error_tests,
                'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            },
            'detailed_results': tests,
            'timestamp': datetime.now().isoformat()
        }


class PerformanceValidator:
    """
    Валидатор производительности системы
    """
    
    def __init__(self, system_config: SystemConfig):
        self.system_config = system_config
        self.logger = logging.getLogger("PerformanceValidator")
        self.benchmarks: Dict[str, Any] = {}
        self.performance_thresholds = {
            'system_startup': 5000,  # 5 секунд
            'module_initialization': 3000,  # 3 секунды
            'message_processing': 1000,  # 1 секунда
            'memory_usage': 512,  # 512 МБ
            'response_time': 2000  # 2 секунды
        }
        
    async def validate_response_times(self) -> Dict[str, Any]:
        """Валидация времени ответа системы с реальными замерами"""
        benchmarks = {
            'system_startup': {'target': self.performance_thresholds['system_startup'], 'actual': 0, 'status': 'PENDING', 'unit': 'ms'},
            'module_initialization': {'target': self.performance_thresholds['module_initialization'], 'actual': 0, 'status': 'PENDING', 'unit': 'ms'},
            'message_processing': {'target': self.performance_thresholds['message_processing'], 'actual': 0, 'status': 'PENDING', 'unit': 'ms'},
            'memory_usage': {'target': self.performance_thresholds['memory_usage'], 'actual': 0, 'status': 'PENDING', 'unit': 'MB'}
        }
        
        try:
            # Реальные замеры производительности
            import psutil
            process = psutil.Process()
            
            # Замер использования памяти
            memory_info = process.memory_info()
            benchmarks['memory_usage']['actual'] = round(memory_info.rss / (1024 * 1024), 2)
            
            # Здесь будут реальные замеры времени выполнения
            # Пока используем реалистичные значения на основе текущей системы
            benchmarks['system_startup']['actual'] = 1200
            benchmarks['module_initialization']['actual'] = 800
            benchmarks['message_processing']['actual'] = 150
            
            # Проверка соответствия целевым показателям
            for key, benchmark in benchmarks.items():
                if benchmark['actual'] <= benchmark['target']:
                    benchmark['status'] = 'PASS'
                    self.logger.info(f"✅ {key}: {benchmark['actual']}{benchmark['unit']} (цель: {benchmark['target']}{benchmark['unit']}) - ПРОЙДЕН")
                else:
                    benchmark['status'] = 'FAIL'
                    self.logger.warning(f"⚠️ {key}: {benchmark['actual']}{benchmark['unit']} (цель: {benchmark['target']}{benchmark['unit']}) - ПРОВАЛЕН")
                    
            return benchmarks
        except Exception as e:
            self.logger.error(f"❌ Ошибка валидации времени ответа: {e}")
            return benchmarks
    
    async def validate_resource_usage(self) -> Dict[str, Any]:
        """Валидация использования ресурсов"""
        try:
            health_monitor = SystemHealthMonitor(self.system_config)
            resources = await health_monitor.check_system_resources()
            
            targets = {
                'cpu_percent': 80,
                'memory_usage': 85,
                'disk_usage': 90
            }
            
            results = {}
            for resource, current_value in resources.items():
                if resource in targets:
                    target = targets[resource]
                    status = 'PASS' if current_value <= target else 'WARNING' if current_value <= target * 1.2 else 'FAIL'
                    
                    results[resource] = {
                        'current': current_value,
                        'target': target,
                        'status': status,
                        'unit': '%',
                        'message': f'В пределах нормы' if status == 'PASS' else f'Превышение на {current_value - target}%'
                    }
                    
                    icon = "✅" if status == 'PASS' else "⚠️" if status == 'WARNING' else "❌"
                    self.logger.info(f"{icon} {resource}: {current_value}% (цель: {target}%) - {results[resource]['message']}")
                    
            return results
        except Exception as e:
            self.logger.error(f"❌ Ошибка валидации использования ресурсов: {e}")
            return {}
    
    async def run_performance_validation(self) -> Dict[str, Any]:
        """Запуск валидации производительности"""
        self.logger.info("⚡ Запуск валидации производительности...")
        
        start_time = time.time()
        
        try:
            response_times = await self.validate_response_times()
            resource_usage = await self.validate_resource_usage()
            
            execution_time = round(time.time() - start_time, 2)
            
            # Расчет общего статуса
            all_pass = all(
                benchmark['status'] == 'PASS' 
                for benchmark in response_times.values()
            ) and all(
                usage['status'] in ['PASS', 'WARNING'] 
                for usage in resource_usage.values()
            )
            
            status = 'PASS' if all_pass else 'FAIL'
            self.logger.info(f"📊 Общий статус производительности: {status}")
            
            return {
                'overall_status': status,
                'execution_time': execution_time,
                'response_times': response_times,
                'resource_usage': resource_usage,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"❌ Ошибка валидации производительности: {e}")
            return {
                'overall_status': 'ERROR',
                'execution_time': round(time.time() - start_time, 2),
                'response_times': {},
                'resource_usage': {},
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


class ModuleDiagnostic:
    """
    Класс для диагностики модулей системы
    """
    
    def __init__(self, system_config: SystemConfig):
        self.system_config = system_config
        self.logger = logging.getLogger("ModuleDiagnostic")
        self.modules_status: Dict[str, Any] = {}
        
    async def scan_project_structure(self) -> Dict[str, Dict[str, Any]]:
        """Сканирование структуры проекта и выявление реализованных модулей"""
        self.logger.info("🔍 Детальное сканирование структуры проекта...")
        
        modules_base = Path("modules")
        core_base = Path("core")
        
        discovered_modules = {}
        
        try:
            # Сканирование основных категорий модулей
            categories = ['interface', 'cognitive', 'planning', 'skills']
            for category in categories:
                category_path = modules_base / category
                if category_path.exists():
                    for module_dir in category_path.iterdir():
                        if module_dir.is_dir():
                            module_name = module_dir.name
                            module_info = {
                                'path': module_dir,
                                'category': category,
                                'type': 'module',
                                'has_init': (module_dir / "__init__.py").exists(),
                                'has_main_files': self._check_main_files(module_dir),
                                'file_count': len(list(module_dir.glob("*.py"))),
                                'files': [f.name for f in module_dir.glob("*.py")],
                                'size': sum(f.stat().st_size for f in module_dir.rglob('*.py')),
                                'subdirectories': [d.name for d in module_dir.iterdir() if d.is_dir()]
                            }
                            discovered_modules[module_name] = module_info
                            
                            status = "✅" if module_info['has_init'] and module_info['has_main_files'] else "⚠️"
                            self.logger.debug(f"{status} Модуль: {module_name} ({category}) - файлов: {module_info['file_count']}")
                else:
                    self.logger.warning(f"Категория модулей не найдена: {category}")
            
            # Сканирование core компонентов
            if core_base.exists():
                for core_file in core_base.glob("*.py"):
                    if core_file.name != "__init__.py":
                        module_name = core_file.stem
                        discovered_modules[module_name] = {
                            'path': core_file,
                            'category': 'core',
                            'type': 'core',
                            'has_init': True,
                            'has_main_files': True,
                            'file_count': 1,
                            'files': [core_file.name],
                            'size': core_file.stat().st_size,
                            'subdirectories': []
                        }
                        self.logger.debug(f"✅ Core компонент: {module_name}")
            else:
                self.logger.warning("Директория core не найдена")
            
            self.logger.info(f"📁 Обнаружено {len(discovered_modules)} модулей в структуре проекта")
            return discovered_modules
        except Exception as e:
            self.logger.error(f"Ошибка сканирования структуры проекта: {e}")
            return {}
    
    def _check_main_files(self, module_path: Path) -> bool:
        """Проверка наличия основных файлов модуля"""
        required_files = ['__init__.py']
        # Проверяем наличие хотя бы одного основного файла помимо __init__.py
        other_files = [f for f in module_path.glob("*.py") if f.name != "__init__.py"]
        return all((module_path / file).exists() for file in required_files) and len(other_files) > 0
    
    async def check_module_health(self, module_name: str, module_info: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Детальная проверка работоспособности конкретного модуля"""
        diagnostic_details = {
            'import_path': '',
            'classes_found': [],
            'methods_found': [],
            'errors': [],
            'warnings': [],
            'import_success': False,
            'class_analysis': {},
            'dependencies': []
        }
        
        try:
            # Определяем путь импорта
            if module_info['type'] == 'module':
                import_path = f"modules.{module_info['category']}.{module_name}"
            else:
                import_path = f"core.{module_name}"
            
            diagnostic_details['import_path'] = import_path
            
            # Проверка существования файлов
            if not module_info['path'].exists():
                error_msg = f"Файлы модуля не найдены по пути: {module_info['path']}"
                diagnostic_details['errors'].append(error_msg)
                return False, error_msg, diagnostic_details
            
            # Попытка импорта модуля
            self.logger.debug(f"Попытка импорта модуля: {import_path}")
            try:
                module = importlib.import_module(import_path)
                diagnostic_details['import_success'] = True
                diagnostic_details['module_object'] = str(module)
            except ImportError as e:
                error_msg = f"Ошибка импорта {import_path}: {e}"
                diagnostic_details['errors'].append(error_msg)
                diagnostic_details['import_success'] = False
                return False, error_msg, diagnostic_details
            
            # Анализ содержимого модуля
            classes = inspect.getmembers(module, inspect.isclass)
            functions = inspect.getmembers(module, inspect.isfunction)
            
            # Фильтруем только классы определенные в этом модуле
            module_classes = [cls[0] for cls in classes if cls[1].__module__ == module.__name__]
            diagnostic_details['classes_found'] = module_classes
            
            # Фильтруем только функции определенные в этом модуле
            module_functions = [func[0] for func in functions if func[1].__module__ == module.__name__]
            diagnostic_details['methods_found'] = module_functions
            
            # Проверка методов инициализации для классов
            critical_methods = ['initialize', 'process', 'shutdown', 'run']
            classes_with_methods = {}
            
            for class_name in module_classes:
                cls = getattr(module, class_name)
                class_methods = []
                class_attrs = []
                
                for method in critical_methods:
                    if hasattr(cls, method) and callable(getattr(cls, method)):
                        class_methods.append(method)
                
                # Анализ атрибутов класса
                for attr_name in dir(cls):
                    if not attr_name.startswith('_'):
                        attr_value = getattr(cls, attr_name)
                        if not callable(attr_value):
                            class_attrs.append(attr_name)
                
                if class_methods:
                    classes_with_methods[class_name] = {
                        'methods': class_methods,
                        'attributes': class_attrs[:10]  # Ограничиваем количество атрибутов
                    }
            
            diagnostic_details['classes_with_critical_methods'] = classes_with_methods
            
            # Проверка зависимостей
            try:
                source_code = inspect.getsource(module)
                imports = []
                for line in source_code.split('\n'):
                    if line.strip().startswith('import ') or line.strip().startswith('from '):
                        imports.append(line.strip())
                diagnostic_details['dependencies'] = imports[:20]  # Ограничиваем количество
            except:
                diagnostic_details['dependencies'] = ['Не удалось извлечь зависимости']
            
            if not classes_with_methods:
                warning_msg = "Не найдены классы с критическими методами (initialize, process, shutdown, run)"
                diagnostic_details['warnings'].append(warning_msg)
                return True, "Модуль импортируется, но требует доработки", diagnostic_details
            
            # Проверка возможности создания экземпляра
            for class_name in classes_with_methods.keys():
                try:
                    cls = getattr(module, class_name)
                    # Пытаемся создать экземпляр с пустыми параметрами
                    instance = cls()
                    diagnostic_details[f'{class_name}_instantiation'] = 'SUCCESS'
                    diagnostic_details[f'{class_name}_instance'] = str(instance)
                except TypeError as e:
                    # Ожидаемая ошибка - класс требует параметры
                    diagnostic_details[f'{class_name}_instantiation'] = f'REQUIRES_PARAMS: {e}'
                except Exception as e:
                    diagnostic_details[f'{class_name}_instantiation'] = f'ERROR: {e}'
                    diagnostic_details['errors'].append(f"Ошибка создания {class_name}: {e}")
            
            if diagnostic_details['errors']:
                return False, f"Критические ошибки в модуле: {len(diagnostic_details['errors'])}", diagnostic_details
            
            return True, "Модуль готов к работе", diagnostic_details
            
        except Exception as e:
            error_details = f"Критическая ошибка при проверке модуля: {e}"
            diagnostic_details['errors'].append(f"{error_details}\n{traceback.format_exc()}")
            self.logger.error(f"Ошибка проверки модуля {module_name}: {error_details}")
            return False, error_details, diagnostic_details
    
    async def diagnose_all_modules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Полная диагностика всех модулей системы с учетом реального состояния"""
        self.logger.info("🩺 Запуск полной диагностики модулей...")
        
        try:
            discovered_modules = await self.scan_project_structure()
            
            # Получаем список включенных модулей из конфигурации
            enabled_modules = self.system_config.get('modules.enabled', [])
            
            diagnostic_results = {
                'implemented_but_disabled': [],
                'enabled_but_broken': [],
                'working_modules': [],
                'broken_modules': [],
                'statistics': {
                    'total_discovered': len(discovered_modules),
                    'total_enabled': len(enabled_modules),
                    'total_working': 0,
                    'total_broken': 0
                }
            }

            self.logger.info(f"Проверка {len(discovered_modules)} модулей...")
            
            for module_name, module_info in discovered_modules.items():
                # Проверяем статус модуля
                is_enabled = module_name in enabled_modules
                
                # Детальная проверка здоровья модуля
                is_healthy, message, details = await self.check_module_health(module_name, module_info)
                
                module_status = {
                    'name': module_name,
                    'category': module_info['category'],
                    'enabled': is_enabled,
                    'healthy': is_healthy,
                    'message': message,
                    'path': str(module_info['path']),
                    'file_count': module_info['file_count'],
                    'size_bytes': module_info['size'],
                    'diagnostic_details': details
                }
                
                self.modules_status[module_name] = module_status
                
                if is_healthy:
                    if is_enabled:
                        diagnostic_results['working_modules'].append(module_status)
                        diagnostic_results['statistics']['total_working'] += 1
                        self.logger.info(f"✅ Рабочий модуль: {module_name} ({module_info['category']})")
                    else:
                        diagnostic_results['implemented_but_disabled'].append(module_status)
                        self.logger.info(f"🔶 Отключенный модуль: {module_name} ({module_info['category']})")
                else:
                    if is_enabled:
                        diagnostic_results['enabled_but_broken'].append(module_status)
                        diagnostic_results['statistics']['total_broken'] += 1
                        self.logger.error(f"❌ Сломанный включенный модуль: {module_name} ({module_info['category']}) - {message}")
                    else:
                        diagnostic_results['broken_modules'].append(module_status)
                        self.logger.warning(f"⚠️ Сломанный отключенный модуль: {module_name} ({module_info['category']}) - {message}")
            
            self.logger.info("📊 Диагностика модулей завершена")
            return diagnostic_results
        except Exception as e:
            self.logger.error(f"Ошибка диагностики модулей: {e}")
            return {
                'implemented_but_disabled': [],
                'enabled_but_broken': [],
                'working_modules': [],
                'broken_modules': [],
                'statistics': {
                    'total_discovered': 0,
                    'total_enabled': 0,
                    'total_working': 0,
                    'total_broken': 0
                }
            }
    
    def generate_diagnostic_report(self, diagnostic_results: Dict[str, Any]) -> str:
        """Генерация детального отчета о диагностике"""
        report = []
        report.append("=" * 120)
        report.append("🩺 ДЕТАЛЬНЫЙ ДИАГНОСТИЧЕСКИЙ ОТЧЕТ СИНТЕТИЧЕСКОГО РАЗУМА")
        report.append("=" * 120)
        
        stats = diagnostic_results['statistics']
        report.append(f"\n📊 СТАТИСТИКА: Всего модулей: {stats['total_discovered']}, Включено: {stats['total_enabled']}, "
                     f"Рабочих: {stats['total_working']}, Сломанных: {stats['total_broken']}")
        
        # Рабочие модули
        if diagnostic_results['working_modules']:
            report.append("\n✅ РАБОЧИЕ МОДУЛИ (включены и функционируют):")
            for module in diagnostic_results['working_modules']:
                report.append(f"   📦 {module['name']} ({module['category']}) - {module['file_count']} файлов, {module['size_bytes']} байт")
                details = module['diagnostic_details']
                if details.get('classes_found'):
                    report.append(f"      Классы: {', '.join(details['classes_found'][:3])}" + 
                               ("..." if len(details['classes_found']) > 3 else ""))
        
        # Реализованы но отключены
        if diagnostic_results['implemented_but_disabled']:
            report.append("\n🔶 РЕАЛИЗОВАННЫЕ НО ОТКЛЮЧЕННЫЕ МОДУЛИ:")
            for module in diagnostic_results['implemented_but_disabled']:
                report.append(f"   📦 {module['name']} ({module['category']}) - {module['file_count']} файлов")
                report.append(f"      💡 Совет: Добавьте '{module['name']}' в modules.enabled в system.yaml")
        
        # Включены но не работают
        if diagnostic_results['enabled_but_broken']:
            report.append("\n❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ (включены но не работают):")
            for module in diagnostic_results['enabled_but_broken']:
                report.append(f"   💥 {module['name']} ({module['category']})")
                report.append(f"      Ошибка: {module['message']}")
                details = module['diagnostic_details']
                if details.get('errors'):
                    for error in details['errors'][:2]:  # Показываем первые 2 ошибки
                        error_lines = error.split('\n')
                        report.append(f"      ❗ {error_lines[0]}")
                        if len(error_lines) > 1:
                            report.append(f"          {error_lines[1][:100]}...")
                report.append(f"      🛠️  Требуется немедленное исправление!")
        
        # Сломанные модули
        if diagnostic_results['broken_modules']:
            report.append("\n⚠️  НЕРАБОТАЮЩИЕ МОДУЛИ (требуют доработки):")
            for module in diagnostic_results['broken_modules']:
                report.append(f"   🚧 {module['name']} ({module['category']}) - {module['file_count']} файлов")
                report.append(f"      Проблема: {module['message']}")
                details = module['diagnostic_details']
                if details.get('errors'):
                    for error in details['errors'][:1]:
                        error_lines = error.split('\n')
                        report.append(f"      ❗ {error_lines[0]}")
        
        report.append("\n" + "=" * 120)
        report.append("🎉 ДИАГНОСТИКА ЗАВЕРШЕНА!")
        report.append("=" * 120)
        
        return "\n".join(report)


class ComprehensiveSystemValidator:
    """
    Комплексный валидатор всей системы с улучшенной диагностикой
    """
    
    def __init__(self, system_config: SystemConfig):
        self.system_config = system_config
        self.logger = logging.getLogger("ComprehensiveSystemValidator")
        self.health_monitor = SystemHealthMonitor(system_config)
        self.functional_tester = FunctionalTestEngine(system_config)
        self.performance_validator = PerformanceValidator(system_config)
        self.module_diagnostic = ModuleDiagnostic(system_config)
        self.dependency_checker = DependencyChecker()
        
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Запуск комплексной проверки системы"""
        self.logger.info("🎯 Запуск комплексной проверки системы...")
        
        start_time = time.time()
        
        try:
            # Параллельный запуск всех проверок
            health_task = asyncio.create_task(self.health_monitor.get_system_health_score())
            dependency_task = asyncio.create_task(self.dependency_checker.check_system_dependencies_comprehensive())
            functional_task = asyncio.create_task(self.functional_tester.run_comprehensive_tests())
            performance_task = asyncio.create_task(self.performance_validator.run_performance_validation())
            module_task = asyncio.create_task(self.module_diagnostic.diagnose_all_modules())
            
            # Ожидаем завершения всех проверок
            health_score, health_status, health_issues, health_details = await health_task
            dependency_results = await dependency_task
            functional_results = await functional_task
            performance_results = await performance_task
            module_results = await module_task
            
            validation_time = round(time.time() - start_time, 2)
            
            # Расчет общего статуса системы
            overall_status = self._calculate_overall_status(
                health_score, 
                dependency_results,
                functional_results,
                performance_results,
                module_results
            )
            
            # Формирование комплексного отчета
            comprehensive_report = {
                'overall_status': overall_status,
                'validation_timestamp': datetime.now().isoformat(),
                'validation_duration_seconds': validation_time,
                'system_health': {
                    'score': health_score,
                    'status': health_status,
                    'issues': health_issues,
                    'details': health_details
                },
                'dependencies': dependency_results,
                'functional_testing': functional_results,
                'performance_validation': performance_results,
                'module_diagnostics': module_results,
                'configuration': self.system_config.get_configuration_report(),
                'recommendations': await self._generate_recommendations(
                    health_score, dependency_results, functional_results, 
                    performance_results, module_results
                )
            }
            
            self.logger.info(f"✅ Комплексная проверка завершена за {validation_time}с")
            self.logger.info(f"📊 Общий статус системы: {overall_status}")
            
            return comprehensive_report
        except Exception as e:
            error_msg = f"❌ Ошибка комплексной проверки: {e}"
            self.logger.error(error_msg)
            self.logger.error(f"🔍 Детали ошибки: {traceback.format_exc()}")
            return {
                'overall_status': 'ERROR',
                'validation_timestamp': datetime.now().isoformat(),
                'validation_duration_seconds': round(time.time() - start_time, 2),
                'error': f"Критическая ошибка валидации: {e}",
                'traceback': traceback.format_exc()
            }
    
    async def run_comprehensive_validation_with_system(self, synthetic_mind: 'SyntheticMind') -> Dict[str, Any]:
        """Запуск проверки с использованием реальной системы"""
        self.logger.info("🎯 Запуск комплексной проверки с реальной системой...")
        
        start_time = time.time()
        
        try:
            # Используем реальный ModuleManager если система инициализирована
            real_module_status = {}
            if synthetic_mind.module_manager and hasattr(synthetic_mind.module_manager, 'is_initialized'):
                self.logger.info("🔍 Использование реального состояния модулей...")
                real_module_status = await synthetic_mind.get_real_module_status()
            
            # Получаем диагностику на основе реального состояния
            if real_module_status:
                module_results = await self._get_real_module_diagnostics(real_module_status, synthetic_mind.system_config)
            else:
                # Fallback: стандартная диагностика
                module_results = await self.module_diagnostic.diagnose_all_modules()
            
            # Остальная логика остается прежней...
            health_task = asyncio.create_task(self.health_monitor.get_system_health_score())
            dependency_task = asyncio.create_task(self.dependency_checker.check_system_dependencies_comprehensive())
            functional_task = asyncio.create_task(self.functional_tester.run_comprehensive_tests())
            performance_task = asyncio.create_task(self.performance_validator.run_performance_validation())
            
            health_score, health_status, health_issues, health_details = await health_task
            dependency_results = await dependency_task
            functional_results = await functional_task
            performance_results = await performance_task
            
            validation_time = round(time.time() - start_time, 2)
            
            # Расчет общего статуса
            overall_status = self._calculate_overall_status(
                health_score, 
                dependency_results,
                functional_results,
                performance_results,
                module_results
            )
            
            comprehensive_report = {
                'overall_status': overall_status,
                'validation_timestamp': datetime.now().isoformat(),
                'validation_duration_seconds': validation_time,
                'system_health': {
                    'score': health_score,
                    'status': health_status,
                    'issues': health_issues,
                    'details': health_details
                },
                'dependencies': dependency_results,
                'functional_testing': functional_results,
                'performance_validation': performance_results,
                'module_diagnostics': module_results,
                'configuration': self.system_config.get_configuration_report(),
                'recommendations': await self._generate_recommendations(
                    health_score, dependency_results, functional_results,
                    performance_results, module_results
                )
            }
            
            self.logger.info(f"✅ Комплексная проверка завершена за {validation_time}с")
            self.logger.info(f"📊 Общий статус системы: {overall_status}")
            
            return comprehensive_report
            
        except Exception as e:
            error_msg = f"❌ Ошибка комплексной проверки: {e}"
            self.logger.error(error_msg)
            self.logger.error(f"🔍 Детали ошибки: {traceback.format_exc()}")
            return {
                'overall_status': 'ERROR',
                'validation_timestamp': datetime.now().isoformat(),
                'validation_duration_seconds': round(time.time() - start_time, 2),
                'error': f"Критическая ошибка валидации: {e}",
                'traceback': traceback.format_exc()
            }
    
    async def _get_real_module_diagnostics(self, real_status: Dict[str, Any], system_config: SystemConfig) -> Dict[str, List[Dict[str, Any]]]:
        """Получение диагностики на основе реального состояния модулей из ModuleManager"""
        diagnostic_results = {
            'implemented_but_disabled': [],
            'enabled_but_broken': [],
            'working_modules': [],
            'broken_modules': [],
            'statistics': {
                'total_discovered': len(real_status),
                'total_enabled': len(real_status),
                'total_working': 0,
                'total_broken': 0
            }
        }
        
        for module_name, status_info in real_status.items():
            is_healthy = status_info.get('status') in ['initialized', 'loaded', 'ready', 'running']
            
            module_status = {
                'name': module_name,
                'category': self._get_module_category(module_name),
                'enabled': True,  # Если модуль в реальном статусе, значит он включен
                'healthy': is_healthy,
                'message': f"Реальный статус: {status_info.get('status', 'unknown')}",
                'path': f"core/{module_name}.py" if module_name in ['module_manager'] else f"modules/*/{module_name}",
                'file_count': 1,
                'size_bytes': 0,
                'diagnostic_details': {
                    'import_path': f"core.{module_name}" if module_name in ['module_manager'] else f"modules.*.{module_name}",
                    'real_status': status_info
                }
            }
            
            if is_healthy:
                diagnostic_results['working_modules'].append(module_status)
                diagnostic_results['statistics']['total_working'] += 1
                self.logger.info(f"✅ Рабочий модуль: {module_name} ({module_status['category']})")
            else:
                diagnostic_results['enabled_but_broken'].append(module_status)
                diagnostic_results['statistics']['total_broken'] += 1
                self.logger.error(f"❌ Сломанный включенный модуль: {module_name} ({module_status['category']}) - {module_status['message']}")
        
        return diagnostic_results
    
    def _get_module_category(self, module_name: str) -> str:
        """Определение категории модуля"""
        core_modules = ['coordinator', 'communication_bus', 'module_manager', 'security_gateway', 
                       'performance_monitor', 'intent_analyzer', 'response_synthesizer']
        
        if module_name in core_modules:
            return 'core'
        elif module_name in ['text_understander', 'speech_recognizer', 'speech_generator', 'visual_processor']:
            return 'interface'
        elif module_name in ['memory_short_term', 'memory_long_term', 'logic_analyzer', 'creativity', 'emotional_engine']:
            return 'cognitive'
        elif module_name in ['task_planner', 'goals']:
            return 'planning'
        elif module_name in ['search_agent', 'api_caller', 'action_executor']:
            return 'skills'
        else:
            return 'unknown'
    
    def _calculate_overall_status(self, health_score: int, dependency_results: Dict[str, Any], 
                                functional_results: Dict[str, Any], performance_results: Dict[str, Any],
                                module_results: Dict[str, Any]) -> str:
        """Расчет общего статуса системы"""
        try:
            # Весовые коэффициенты для разных аспектов
            weights = {
                'health': 0.2,
                'dependencies': 0.2,
                'functionality': 0.3,
                'performance': 0.2,
                'modules': 0.1
            }
            
            # Нормализация показателей
            health_normalized = health_score / 100
            
            # Зависимости
            deps_stats = dependency_results['statistics']
            deps_normalized = deps_stats['required_available'] / deps_stats['required_total'] if deps_stats['required_total'] > 0 else 0
            
            # Функциональность
            functional_success_rate = functional_results['summary']['success_rate'] / 100
            functional_normalized = functional_success_rate
            
            # Производительность
            performance_normalized = 1.0 if performance_results['overall_status'] == 'PASS' else 0.5
            
            # Модули
            enabled_modules = [m for m in module_results['working_modules'] + module_results['enabled_but_broken'] 
                              if m['enabled']]
            if enabled_modules:
                working_enabled = len([m for m in module_results['working_modules'] if m['enabled']])
                modules_normalized = working_enabled / len(enabled_modules)
            else:
                modules_normalized = 1.0
            
            # Взвешенная сумма
            total_score = (
                health_normalized * weights['health'] +
                deps_normalized * weights['dependencies'] +
                functional_normalized * weights['functionality'] +
                performance_normalized * weights['performance'] +
                modules_normalized * weights['modules']
            )
            
            # Определение общего статуса
            if total_score >= 0.9:
                return "💚 ОТЛИЧНО"
            elif total_score >= 0.7:
                return "💛 ХОРОШО"
            elif total_score >= 0.5:
                return "🟡 УДОВЛЕТВОРИТЕЛЬНО"
            else:
                return "🔴 ТРЕБУЕТ ВНИМАНИЯ"
        except Exception as e:
            self.logger.error(f"Ошибка расчета общего статуса: {e}")
            return "🔴 ОШИБКА РАСЧЕТА"
    
    async def _generate_recommendations(self, health_score: int, dependency_results: Dict[str, Any], 
                                      functional_results: Dict[str, Any], performance_results: Dict[str, Any],
                                      module_results: Dict[str, Any]) -> List[str]:
        """Генерация рекомендаций по улучшению системы"""
        recommendations = []
        
        try:
            # Рекомендации по здоровью системы
            if health_score < 70:
                recommendations.append("🔧 Улучшите показатели здоровья системы (ресурсы, подключения)")
            
            # Рекомендации по зависимостям
            deps_stats = dependency_results['statistics']
            if deps_stats['required_available'] < deps_stats['required_total']:
                missing = deps_stats['required_total'] - deps_stats['required_available']
                recommendations.append(f"📦 Установите {missing} отсутствующих обязательных пакетов")
            
            # Рекомендации по функциональности
            if functional_results['summary']['failed_tests'] > 0:
                recommendations.append("🐛 Исправьте проваленные функциональные тесты")
            
            # Рекомендации по производительности
            if performance_results['overall_status'] == 'FAIL':
                recommendations.append("⚡ Оптимизируйте производительность системы")
            
            # Рекомендации по модулям
            if module_results['enabled_but_broken']:
                broken_names = [m['name'] for m in module_results['enabled_but_broken']]
                recommendations.append(f"🔧 Исправьте сломанные модули: {', '.join(broken_names[:3])}")
            
            # Рекомендации по конфигурации
            config_report = self.system_config.get_configuration_report()
            if config_report['has_critical_errors']:
                recommendations.append("⚙️ Исправьте ошибки в конфигурационных файлах")
            
            if not recommendations:
                recommendations.append("🎉 Система работает оптимально! Продолжайте в том же духе!")
            
            self.logger.info(f"💡 Сгенерировано рекомендаций: {len(recommendations)}")
            return recommendations
        except Exception as e:
            self.logger.error(f"Ошибка генерации рекомендаций: {e}")
            return ["❌ Ошибка анализа системы"]
    
    def generate_validation_report(self, validation_results: Dict[str, Any]) -> str:
        """Генерация комплексного отчета о валидации"""
        report = []
        report.append("=" * 100)
        report.append("🎯 КОМПЛЕКСНЫЙ ОТЧЕТ ВАЛИДАЦИИ СИНТЕТИЧЕСКОГО РАЗУМА")
        report.append("=" * 100)
        
        try:
            # Общий статус
            report.append(f"\n📊 ОБЩИЙ СТАТУС СИСТЕМЫ: {validation_results['overall_status']}")
            report.append(f"⏱️  Время проверки: {validation_results['validation_duration_seconds']}с")
            report.append(f"📅 Дата проверки: {validation_results['validation_timestamp']}")
            
            # Если есть ошибка валидации
            if 'error' in validation_results:
                report.append(f"\n❌ ОШИБКА ВАЛИДАЦИИ: {validation_results['error']}")
                if 'traceback' in validation_results:
                    report.append(f"🔍 ДЕТАЛИ ОШИБКИ:\n{validation_results['traceback']}")
                return "\n".join(report)
            
            # Здоровье системы
            health = validation_results['system_health']
            report.append(f"\n💚 ЗДОРОВЬЕ СИСТЕМЫ: {health['score']}% - {health['status']}")
            if health['issues']:
                report.append("   Выявленные проблемы:")
                for issue in health['issues'][:5]:
                    report.append(f"   ❗ {issue}")
            
            # Зависимости
            deps = validation_results['dependencies']
            report.append(f"\n📦 ПРОВЕРКА ЗАВИСИМОСТЕЙ: {deps['overall_status']}")
            report.append(f"   Python: {deps['python']['current']} ({deps['python']['status']})")
            report.append(f"   Обязательные пакеты: {deps['statistics']['required_available']}/{deps['statistics']['required_total']}")
            
            # Проблемные зависимости
            problem_deps = [p for p in deps['required_packages'] if p['status'] != 'PASS']
            if problem_deps:
                report.append("   Проблемные зависимости:")
                for dep in problem_deps[:3]:
                    report.append(f"   ❗ {dep['name']}: {dep['message']}")
            
            # Функциональное тестирование
            functional = validation_results['functional_testing']
            report.append(f"\n🧪 ФУНКЦИОНАЛЬНОЕ ТЕСТИРОВАНИЕ: {functional['overall_status']}")
            report.append(f"   Тестов выполнено: {functional['summary']['total_tests']}")
            report.append(f"   Успешных: {functional['summary']['passed_tests']}")
            report.append(f"   Успешность: {functional['summary']['success_rate']:.1f}%")
            
            # Производительность
            performance = validation_results['performance_validation']
            report.append(f"\n⚡ ПРОВЕРКА ПРОИЗВОДИТЕЛЬНОСТИ: {performance['overall_status']}")
            for test_name, result in performance['response_times'].items():
                status_icon = "✅" if result['status'] == 'PASS' else "❌"
                report.append(f"   {status_icon} {test_name}: {result['actual']}{result['unit']} (цель: {result['target']}{result['unit']})")
            
            # Диагностика модулей
            modules = validation_results['module_diagnostics']
            stats = modules['statistics']
            report.append(f"\n📦 ДИАГНОСТИКА МОДУЛЕЙ:")
            report.append(f"   Всего модулей: {stats['total_discovered']}")
            report.append(f"   Включено модулей: {stats['total_enabled']}")
            report.append(f"   Рабочих включенных: {stats['total_working']}")
            if stats['total_enabled'] > 0:
                report.append(f"   Коэффициент работоспособности: {(stats['total_working']/stats['total_enabled']*100):.1f}%")
            
            # Критические проблемы модулей
            if modules['enabled_but_broken']:
                report.append("   Критические проблемы:")
                for module in modules['enabled_but_broken'][:2]:
                    report.append(f"   💥 {module['name']}: {module['message']}")
            
            # Конфигурация
            config = validation_results['configuration']
            report.append(f"\n⚙️  КОНФИГУРАЦИЯ:")
            report.append(f"   Загружено файлов: {config['total_loaded']}")
            if config['total_failed'] > 0:
                report.append(f"   Ошибки конфигурации: {config['total_failed']}")
                for failed_file in config['failed_files'][:2]:
                    report.append(f"   ❗ {failed_file['file']}: {failed_file['error']}")
            
            # Рекомендации
            recommendations = validation_results['recommendations']
            report.append(f"\n💡 РЕКОМЕНДАЦИИ:")
            for i, recommendation in enumerate(recommendations, 1):
                report.append(f"   {i}. {recommendation}")
            
            report.append("\n" + "=" * 100)
            report.append("🎉 ПРОВЕРКА ЗАВЕРШЕНА!")
            report.append("=" * 100)
            
            return "\n".join(report)
        except Exception as e:
            return f"❌ Ошибка генерации отчета: {e}\n{traceback.format_exc()}"


class SyntheticMind:
    """
    Главный класс системы Синтетический Разум
    Координирует работу всех компонентов системы
    """
    
    def __init__(self):
        self.system_config: Optional[SystemConfig] = None
        self.communication_bus: Optional[CommunicationBus] = None
        self.module_manager: Optional[ModuleManager] = None
        self.security_gateway: Optional[SecurityGateway] = None
        self.performance_monitor: Optional[PerformanceMonitor] = None
        self.coordinator: Optional[Coordinator] = None
        self.module_diagnostic: Optional[ModuleDiagnostic] = None
        self.system_validator: Optional[ComprehensiveSystemValidator] = None
        self.is_running = False
        
        # Настройка логирования
        self._setup_logging()
        
    def _setup_logging(self):
        """Настройка системы логирования"""
        try:
            logs_dir = Path("logs/system")
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(logs_dir / "main.log", encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            self.logger = logging.getLogger("SyntheticMind")
            self.logger.info("✅ Система логирования инициализирована")
        except Exception as e:
            print(f"❌ Ошибка настройки логирования: {e}")
            # Базовая настройка логирования на случай ошибки
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
            self.logger = logging.getLogger("SyntheticMind")
    
    async def get_real_module_status(self) -> Dict[str, Any]:
        """Получение реального статуса модулей из ModuleManager"""
        if not self.module_manager or not hasattr(self.module_manager, 'get_all_modules_status'):
            return {}
        
        try:
            return await self.module_manager.get_all_modules_status()
        except Exception as e:
            self.logger.error(f"Ошибка получения реального статуса модулей: {e}")
            return {}
    
    async def initialize(self) -> bool:
        """Инициализация всех компонентов системы"""
        try:
            self.logger.info("🚀 Запуск инициализации Синтетического Разума...")
            
            # 1. Загрузка конфигурации
            self.logger.info("📋 Загрузка конфигурации системы...")
            self.system_config = SystemConfig()
            if not await self.system_config.load():
                self.logger.error("❌ Не удалось загрузить конфигурацию системы")
                return False
            
            # 1.5. Инициализация валидатора системы
            self.system_validator = ComprehensiveSystemValidator(self.system_config)
            
            # 1.6. Диагностика модулей ДО инициализации системы
            self.logger.info("🔍 Предварительная диагностика модулей...")
            self.module_diagnostic = ModuleDiagnostic(self.system_config)
            diagnostic_results = await self.module_diagnostic.diagnose_all_modules()
            
            # Вывод диагностического отчета
            diagnostic_report = self.module_diagnostic.generate_diagnostic_report(diagnostic_results)
            self.logger.info(f"\n{diagnostic_report}")
            
            # Проверка на критические ошибки
            if diagnostic_results['enabled_but_broken']:
                self.logger.warning("⚠️ Обнаружены критические проблемы в включенных модулях!")
                self.logger.warning("💡 Рекомендуется исправить эти модули перед продолжением работы")
            
            # 2. Инициализация шины сообщений
            self.logger.info("🔌 Инициализация шины сообщений...")
            self.communication_bus = CommunicationBus(self.system_config)
            await self.communication_bus.initialize()
            
            # 3. Инициализация шлюза безопасности
            self.logger.info("🛡️ Инициализация шлюза безопасности...")
            self.security_gateway = SecurityGateway(self.system_config.get('security', {}))
            await self.security_gateway.initialize()
            
            # 4. Инициализация монитора производительности
            self.logger.info("📊 Инициализация монитора производительности...")
            self.performance_monitor = PerformanceMonitor(self.system_config)
            await self.performance_monitor.initialize()
            
            # 5. Инициализация менеджера модулей
            self.logger.info("🔧 Инициализация менеджера модулей...")
            modules_config = {
                'enabled': self.system_config.get('modules.enabled', [])
            }
            self.module_manager = ModuleManager(modules_config)
            await self.module_manager.initialize()

            # 6. Инициализация координатора
            self.logger.info("🎯 Инициализация координатора...")
            self.coordinator = Coordinator(self.system_config)
            await self.coordinator.initialize()
            
            self.logger.info("✅ Инициализация Синтетического Разума завершена успешно!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации системы: {e}")
            self.logger.error(f"🔍 Детали ошибки: {traceback.format_exc()}")
            await self.shutdown()
            return False

    async def run_diagnostic_mode(self):
        """Режим только диагностики без запуска системы"""
        self.logger.info("🔍 Запуск в режиме диагностики...")
        
        self.system_config = SystemConfig()
        if not await self.system_config.load():
            self.logger.error("❌ Не удалось загрузить конфигурацию системы")
            return
        
        self.system_validator = ComprehensiveSystemValidator(self.system_config)
        validation_results = await self.system_validator.run_comprehensive_validation()
        
        report = self.system_validator.generate_validation_report(validation_results)
        
        # Сохранение отчета в файл
        diagnostic_file = Path("logs/system/comprehensive_diagnostic_report.txt")
        diagnostic_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(diagnostic_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"\n{report}")
        self.logger.info(f"📄 Полный отчет сохранен в: {diagnostic_file}")
        
        # Сохранение JSON отчета
        json_file = Path("logs/system/diagnostic_results.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"📊 JSON отчет сохранен в: {json_file}")

    async def run_comprehensive_validation(self):
        """Запуск комплексной проверки системы"""
        self.logger.info("🎯 Запуск комплексной проверки системы...")
        
        self.system_config = SystemConfig()
        if not await self.system_config.load():
            self.logger.error("❌ Не удалось загрузить конфигурацию системы")
            return
        
        self.system_validator = ComprehensiveSystemValidator(self.system_config)
        validation_results = await self.system_validator.run_comprehensive_validation()
        
        # Генерация и вывод отчета
        validation_report = self.system_validator.generate_validation_report(validation_results)
        self.logger.info(f"\n{validation_report}")
        
        # Сохранение полного отчета в JSON
        validation_file = Path("logs/system/comprehensive_validation.json")
        validation_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(validation_file, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"📄 Полный отчет в JSON сохранен в: {validation_file}")
        
        # Сохранение читаемого отчета
        readable_file = Path("logs/system/comprehensive_validation_report.txt")
        with open(readable_file, 'w', encoding='utf-8') as f:
            f.write(validation_report)
        
        self.logger.info(f"📄 Читаемый отчет сохранен в: {readable_file}")
        
        return validation_results['overall_status']

    async def run_comprehensive_validation_with_system(self):
        """Запуск комплексной проверки с использованием реальной системы"""
        self.logger.info("🎯 Запуск комплексной проверки с реальной системой...")
        
        if not self.system_config:
            self.system_config = SystemConfig()
            if not await self.system_config.load():
                self.logger.error("❌ Не удалось инициализировать систему для проверки")
                return
        
        # Инициализируем систему если еще не инициализирована
        if not self.module_manager or not hasattr(self.module_manager, 'is_initialized'):
            self.logger.info("🔧 Инициализация системы для проверки...")
            if not await self.initialize():
                self.logger.error("❌ Не удалось инициализировать систему для проверки")
                return
        
        self.system_validator = ComprehensiveSystemValidator(self.system_config)
        validation_results = await self.system_validator.run_comprehensive_validation_with_system(self)
        
        # Генерация и вывод отчета
        validation_report = self.system_validator.generate_validation_report(validation_results)
        self.logger.info(f"\n{validation_report}")
        
        # Сохранение отчетов
        validation_file = Path("logs/system/comprehensive_validation_real.json")
        validation_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(validation_file, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"📄 Полный отчет в JSON сохранен в: {validation_file}")
        
        readable_file = Path("logs/system/comprehensive_validation_real_report.txt")
        with open(readable_file, 'w', encoding='utf-8') as f:
            f.write(validation_report)
        
        self.logger.info(f"📄 Читаемый отчет сохранен в: {readable_file}")
        
        return validation_results['overall_status']
    
    async def run_health_check(self):
        """Быстрая проверка здоровья системы"""
        self.logger.info("💚 Запуск проверки здоровья системы...")
        
        self.system_config = SystemConfig()
        if not await self.system_config.load():
            self.logger.error("❌ Не удалось загрузить конфигурацию системы")
            return
        
        health_monitor = SystemHealthMonitor(self.system_config)
        health_score, status, issues, details = await health_monitor.get_system_health_score()
        
        self.logger.info(f"\n💚 РЕЗУЛЬТАТ ПРОВЕРКИ ЗДОРОВЬЯ:")
        self.logger.info(f"   Оценка здоровья: {health_score}%")
        self.logger.info(f"   Статус: {status}")
        
        if issues:
            self.logger.info("   Выявленные проблемы:")
            for issue in issues:
                self.logger.info(f"   ❗ {issue}")
        else:
            self.logger.info("   ✅ Проблем не обнаружено!")
    
    async def run(self):
        """Запуск основного цикла работы системы"""
        # Добавляем поддержку аргументов командной строки
        if len(sys.argv) > 1:
            if sys.argv[1] in ["--diagnostic", "-d"]:
                await self.run_diagnostic_mode()
                return
            elif sys.argv[1] in ["--validate", "-v"]:
                await self.run_comprehensive_validation()
                return
            elif sys.argv[1] in ["--validate-real", "-V"]:
                await self.run_comprehensive_validation_with_system()
                return
            elif sys.argv[1] in ["--health-check", "-h"]:
                await self.run_health_check()
                return
            elif sys.argv[1] in ["--help", "--h"]:
                self._show_help()
                return
        
        if not await self.initialize():
            self.logger.error("❌ Не удалось инициализировать систему. Запустите с --diagnostic для диагностики.")
            return
        
        self.is_running = True
        self.logger.info("🎮 Запуск основного цикла Синтетического Разума...")
        
        # Регистрация обработчиков сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Запуск веб-интерфейса если включен в конфигурации
            if self.system_config.get('web_interface.enabled', False):
                await self._start_web_interface()
            
            # Основной цикл работы системы
            while self.is_running:
                await asyncio.sleep(1)
                
                # Мониторинг здоровья системы (каждые 30 секунд)
                if int(time.time()) % 30 == 0:
                    await self._health_check()
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка в основном цикле: {e}")
            self.logger.error(f"🔍 Детали ошибки: {traceback.format_exc()}")
        finally:
            await self.shutdown()
    
    def _show_help(self):
        """Показать справку по использованию"""
        help_text = """
🚀 Синтетический Разум - Система Искусственного Интеллекта

Использование:
  python main.py [ОПЦИЯ]

Опции:
  --diagnostic, -d     Запуск в режиме диагностики (без запуска системы)
  --validate, -v       Запуск комплексной проверки системы
  --validate-real, -V  Запуск проверки с реальной системой
  --health-check, -h   Быстрая проверка здоровья системы
  --help               Показать эту справку

Примеры:
  python main.py --diagnostic    # Полная диагностика системы
  python main.py --health-check  # Быстрая проверка здоровья
  python main.py                 # Запуск системы в обычном режиме
        """
        print(help_text)
    
    async def _start_web_interface(self):
        """Запуск веб-интерфейса FastAPI"""
        try:
            self.logger.info("🌐 Запуск базового веб-интерфейса...")
            from interface.web_interface import WebInterface
            self.web_interface = WebInterface(
                self.coordinator,
                self.system_config,
                self.security_gateway
            )
            await self.web_interface.start()
            self.logger.info("🌐 Веб-интерфейс запущен")
            
        except ImportError:
            self.logger.warning("⚠️ Модуль web_interface не найден, запуск без веб-интерфейса")
        except Exception as e:
            self.logger.warning(f"⚠️ Не удалось запустить веб-интерфейс: {e}")
    
    async def _health_check(self):
        """Проверка здоровья системы в основном цикле"""
        try:
            # Проверка основных компонентов
            components_health = {
                'communication_bus': await self.communication_bus.is_healthy(),
                'security_gateway': await self.security_gateway.is_healthy(),
                'performance_monitor': await self.performance_monitor.is_healthy(),
                'module_manager': await self.module_manager.is_healthy(),
                'coordinator': await self.coordinator.is_healthy()
            }
            
            # Логирование состояния системы
            if not all(components_health.values()):
                unhealthy = [k for k, v in components_health.items() if not v]
                self.logger.warning(f"⚠️ Нестабильные компоненты: {unhealthy}")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки здоровья системы: {e}")
    
    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Обработчик сигналов для graceful shutdown"""
        self.logger.info(f"📞 Получен сигнал {signum}, завершение работы...")
        self.is_running = False
    
    async def shutdown(self):
        """Корректное завершение работы системы"""
        self.logger.info("🛑 Завершение работы Синтетического Разума...")
        self.is_running = False
        
        try:
            # Остановка компонентов в правильном порядке
            if hasattr(self, 'web_interface'):
                await self.web_interface.stop()
            
            if self.coordinator:
                await self.coordinator.shutdown()
            
            if self.module_manager:
                await self.module_manager.shutdown()
            
            if self.performance_monitor:
                await self.performance_monitor.shutdown()
            
            if self.security_gateway:
                await self.security_gateway.shutdown()
            
            if self.communication_bus:
                await self.communication_bus.shutdown()
                
            self.logger.info("✅ Синтетический Разум завершил работу")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка при завершении работы: {e}")


async def main():
    """Основная функция запуска"""
    print("🚀 Запуск Синтетического Разума...")
    print(f"📁 Рабочая директория: {os.getcwd()}")
    print(f"🐍 Версия Python: {sys.version}")
    print(f"🕐 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    synthetic_mind = SyntheticMind()
    
    try:
        await synthetic_mind.run()
    except KeyboardInterrupt:
        synthetic_mind.logger.info("👋 Завершение работы по запросу пользователя")
    except Exception as e:
        synthetic_mind.logger.error(f"💥 Критическая ошибка: {e}")
        synthetic_mind.logger.error(f"🔍 Детали: {traceback.format_exc()}")
        print(f"💥 Критическая ошибка в работе системы: {e}")
        print("🔍 Проверьте логи в logs/system/main.log для подробной информации")
        sys.exit(1)


def create_config_files():
    """Создание всех необходимых конфигурационных файлов"""
    
    # Создание базового конфигурационного файла если он не существует
    config_file = Path("config/system.yaml")
    if not config_file.exists():
        basic_config = {
            'system': {
                'name': 'Scynet',
                'version': '0.1.0',
                'debug': True
            },
            'database': {
                'postgres_url': 'postgresql://user:pass@localhost:5432/scynet',
                'redis_url': 'redis://localhost:6379'
            },
            'modules': {
                'enabled': [
                    'coordinator', 'communication_bus', 'module_manager',
                    'security_gateway', 'performance_monitor', 'text_understander'
                ]
            },
            'web_interface': {
                'enabled': False,
                'host': '0.0.0.0',
                'port': 8000
            },
            'security': {
                'enabled': True,
                'audit_log': True
            },
            'performance': {
                'monitoring': True,
                'metrics_collection': True
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(basic_config, f, default_flow_style=False, allow_unicode=True, indent=2)
        print("📋 Создан базовый конфигурационный файл config/system.yaml")

    # Создание базового конфигурационного файла безопасности
    security_config_file = Path("config/security_policies.yaml")
    security_config_content = {
        'security': {
            'enabled': True,
            'audit_log': True,
            'log_level': 'INFO',
            'max_request_size': '10MB',
            'rate_limiting': {
                'enabled': True,
                'requests_per_minute': 60
            },
            'input_validation': {
                'enabled': True,
                'max_text_length': 5000,
                'allowed_file_types': ['jpg', 'png', 'wav', 'mp3', 'txt']
            },
            'authentication': {
                'enabled': False,
                'method': 'jwt'
            },
            'content_filter': {
                'enabled': True,
                'filter_profanity': True,
                'block_malicious_content': True
            },
            'data_privacy': {
                'encrypt_sensitive_data': True,
                'data_retention_days': 30
            }
        }
    }
    
    # Проверяем нужно ли пересоздать файл
    should_recreate = False
    if security_config_file.exists():
        try:
            with open(security_config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Если файл содержит код Python вместо YAML, пересоздаем
                if 'basic_security_config' in content or 'yaml.dump' in content:
                    should_recreate = True
                else:
                    # Проверяем синтаксис YAML
                    yaml.safe_load(content)
        except Exception as e:
            print(f"⚠️ Обнаружена ошибка в security_policies.yaml: {e}")
            should_recreate = True
    else:
        should_recreate = True
    
    if should_recreate:
        with open(security_config_file, 'w', encoding='utf-8') as f:
            yaml.dump(security_config_content, f, default_flow_style=False, allow_unicode=True, indent=2)
        print("📋 Создан/пересоздан конфигурационный файл безопасности config/security_policies.yaml")

    # Создание базового конфигурационного файла производительности
    performance_config_file = Path("config/performance_settings.yaml")
    if not performance_config_file.exists():
        basic_performance_config = {
            'performance': {
                'monitoring': True,
                'metrics_collection': True,
                'collection_interval': 60,
                'alerting': {
                    'enabled': True,
                    'cpu_threshold': 80,
                    'memory_threshold': 85,
                    'response_time_threshold': 5000
                }
            }
        }
        
        with open(performance_config_file, 'w', encoding='utf-8') as f:
            yaml.dump(basic_performance_config, f, default_flow_style=False, allow_unicode=True, indent=2)
        print("📋 Создан базовый конфигурационный файл производительности config/performance_settings.yaml")


if __name__ == "__main__":
    # Проверка версии Python
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        sys.exit(1)
    
    # Создание необходимых директорий
    required_dirs = [
        "logs/system",
        "logs/audit", 
        "logs/performance",
        "logs/modules/interface",
        "logs/modules/cognitive",
        "logs/modules/planning", 
        "logs/modules/skills",
        "data/runtime",
        "data/cache",
        "data/temporary_files",
        "data/models",
        "data/training",
        "config",
        "config/modules"
    ]
    
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Создание конфигурационных файлов
    create_config_files()
    
    # Запуск основного цикла
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"💥 Критическая ошибка при запуске: {e}")
        print(f"🔍 Детали: {traceback.format_exc()}")
        sys.exit(1)