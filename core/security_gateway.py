"""
Шлюз безопасности (проверка всех запросов)
Обеспечивает безопасность системы на всех уровнях
"""

import logging
import re
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import hashlib
import time
import json

@dataclass
class SecurityCheckResult:
    """Результат проверки безопасности"""
    allowed: bool
    reason: str
    risk_level: str  # 'low', 'medium', 'high'
    checks_passed: List[str]
    checks_failed: List[str]

class SecurityError(Exception):
    """Исключение безопасности"""
    pass

class SecurityGateway:
    """Шлюз безопасности системы"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('core.security_gateway')
        
        # Паттерны для проверки безопасности
        self.malicious_patterns = []
        self.suspicious_keywords = []
        
        # Ограничения частоты запросов
        self.rate_limits: Dict[str, List[float]] = {}
        
        # История подозрительных действий
        self.suspicious_activities: List[Dict[str, Any]] = []
        
        # Уровень безопасности
        self.security_level = config.get('security_level', 'medium')
        
        self.is_initialized = False

    async def validate_input(self, data):
        """
        Алиас для validate_request для совместимости с тестами
    
        Args:
            data: Входные данные для проверки
        
        Returns:
            Словарь с результатом проверки безопасности
        """
        # Создаем минимальный контекст для проверки
        class SimpleContext:
            def __init__(self, data):
                self.user_input = data
                self.input_type = 'text'
                self.request_id = f"validate_input_{int(time.time())}"
    
        context = SimpleContext(data)
        result = await self.validate_request(context)
    
        # Возвращаем словарь с ожидаемыми полями
        return {
            'approved': result.allowed,
            'allowed': result.allowed,
            'reason': result.reason,
            'risk_level': result.risk_level,
            'checks_passed': result.checks_passed,
            'checks_failed': result.checks_failed
        }

    async def initialize(self):
        """Инициализация шлюза безопасности"""
        try:
            await self._load_security_patterns()
            await self._load_blacklists()
            
            self.is_initialized = True
            self.logger.info("Шлюз безопасности инициализирован")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации шлюза безопасности: {e}")
            raise

    async def validate_request(self, context) -> SecurityCheckResult:
        """
        Полная проверка безопасности запроса
        
        Args:
            context: Контекст обработки запроса
            
        Returns:
            Результат проверки безопасности
        """
        if not self.is_initialized:
            raise RuntimeError("Шлюз безопасности не инициализирован")
        
        checks_passed = []
        checks_failed = []
        
        try:
            user_input = context.user_input
            request_id = context.request_id
            
            self.logger.debug(f"Проверка безопасности запроса {request_id}")
            
            # 1. Проверка частоты запросов
            if not await self._check_rate_limit(request_id):
                checks_failed.append('rate_limit')
                return SecurityCheckResult(
                    allowed=False,
                    reason="Превышена частота запросов",
                    risk_level='high',
                    checks_passed=checks_passed,
                    checks_failed=checks_failed
                )
            checks_passed.append('rate_limit')
            
            # 2. Проверка содержимого ввода
            content_check = await self._check_content_safety(user_input, context.input_type)
            if not content_check['allowed']:
                checks_failed.append('content_safety')
                return SecurityCheckResult(
                    allowed=False,
                    reason=content_check['reason'],
                    risk_level=content_check['risk_level'],
                    checks_passed=checks_passed,
                    checks_failed=checks_failed
                )
            checks_passed.append('content_safety')
            
            # 3. Проверка структуры запроса
            if not await self._check_request_structure(context):
                checks_failed.append('request_structure')
                return SecurityCheckResult(
                    allowed=False,
                    reason="Некорректная структура запроса",
                    risk_level='medium',
                    checks_passed=checks_passed,
                    checks_failed=checks_failed
                )
            checks_passed.append('request_structure')
            
            # 4. Дополнительные проверки для высокого уровня безопасности
            if self.security_level == 'high':
                advanced_check = await self._advanced_security_checks(context)
                if not advanced_check['allowed']:
                    checks_failed.append('advanced_checks')
                    return SecurityCheckResult(
                        allowed=False,
                        reason=advanced_check['reason'],
                        risk_level=advanced_check['risk_level'],
                        checks_passed=checks_passed,
                        checks_failed=checks_failed
                    )
                checks_passed.append('advanced_checks')
            
            self.logger.info(f"Запрос {request_id} прошел проверки безопасности")
            
            return SecurityCheckResult(
                allowed=True,
                reason="Все проверки пройдены",
                risk_level='low',
                checks_passed=checks_passed,
                checks_failed=checks_failed
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки безопасности: {e}")
            checks_failed.append('system_error')
            return SecurityCheckResult(
                allowed=False,
                reason=f"Системная ошибка при проверке: {e}",
                risk_level='high',
                checks_passed=checks_passed,
                checks_failed=checks_failed
            )

    async def _check_rate_limit(self, request_id: str, window_seconds: int = 60, max_requests: int = 100) -> bool:
        """Проверка ограничения частоты запросов"""
        current_time = time.time()
        client_id = self._extract_client_id(request_id)
        
        # Инициализация счетчика для клиента
        if client_id not in self.rate_limits:
            self.rate_limits[client_id] = []
        
        # Удаляем старые запросы вне окна
        window_start = current_time - window_seconds
        self.rate_limits[client_id] = [t for t in self.rate_limits[client_id] if t > window_start]
        
        # Проверяем лимит
        if len(self.rate_limits[client_id]) >= max_requests:
            self.logger.warning(f"Превышен лимит запросов для клиента {client_id}")
            await self._log_suspicious_activity('rate_limit_exceeded', {
                'client_id': client_id,
                'request_count': len(self.rate_limits[client_id])
            })
            return False
        
        # Добавляем текущий запрос
        self.rate_limits[client_id].append(current_time)
        return True

    async def _check_content_safety(self, user_input: Any, input_type: str) -> Dict[str, Any]:
        """Проверка безопасности содержимого"""
        if input_type == 'text':
            return await self._check_text_safety(str(user_input))
        elif input_type == 'audio':
            # Для аудио проверяем длину и метаданные
            return await self._check_audio_safety(user_input)
        elif input_type == 'image':
            # Для изображений проверяем размер и формат
            return await self._check_image_safety(user_input)
        else:
            return {'allowed': False, 'reason': f'Неизвестный тип ввода: {input_type}', 'risk_level': 'medium'}

    async def _check_text_safety(self, text: str) -> Dict[str, Any]:
        """Проверка безопасности текста"""
        text_lower = text.lower()
        
        # Проверка на вредоносные паттерны
        for pattern in self.malicious_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                await self._log_suspicious_activity('malicious_pattern_detected', {
                    'pattern': pattern,
                    'text_sample': text[:100]
                })
                return {
                    'allowed': False,
                    'reason': f"Обнаружен запрещенный паттерн: {pattern}",
                    'risk_level': 'high'
                }
        
        # Проверка подозрительных ключевых слов
        suspicious_found = []
        for keyword in self.suspicious_keywords:
            if keyword in text_lower:
                suspicious_found.append(keyword)
        
        if suspicious_found:
            risk_level = 'medium' if len(suspicious_found) < 3 else 'high'
            await self._log_suspicious_activity('suspicious_keywords_detected', {
                'keywords': suspicious_found,
                'text_sample': text[:100]
            })
            
            if risk_level == 'high':
                return {
                    'allowed': False,
                    'reason': f"Обнаружены подозрительные ключевые слова: {suspicious_found}",
                    'risk_level': 'high'
                }
        
        # Проверка длины текста
        if len(text) > 10000:  # Максимальная длина текста
            return {
                'allowed': False,
                'reason': "Текст слишком длинный",
                'risk_level': 'medium'
            }
        
        return {'allowed': True, 'reason': "Текст безопасен", 'risk_level': 'low'}

    async def _check_audio_safety(self, audio_data: Any) -> Dict[str, Any]:
        """Проверка безопасности аудио данных"""
        # Здесь может быть проверка длины аудио, формата и т.д.
        # В реальной системе здесь будет анализ аудио файла
        
        try:
            # Примерная проверка - в реальной системе будет сложнее
            if hasattr(audio_data, 'size') and audio_data.size > 50 * 1024 * 1024:  # 50MB
                return {
                    'allowed': False,
                    'reason': "Аудио файл слишком большой",
                    'risk_level': 'medium'
                }
            
            return {'allowed': True, 'reason': "Аудио данные безопасны", 'risk_level': 'low'}
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки аудио: {e}")
            return {
                'allowed': False,
                'reason': f"Ошибка анализа аудио: {e}",
                'risk_level': 'medium'
            }

    async def _check_image_safety(self, image_data: Any) -> Dict[str, Any]:
        """Проверка безопасности изображений"""
        # Здесь может быть проверка размера, формата, содержания
        # В реальной системе здесь будет анализ изображения
        
        try:
            # Примерная проверка
            if hasattr(image_data, 'size') and image_data.size > 100 * 1024 * 1024:  # 100MB
                return {
                    'allowed': False,
                    'reason': "Изображение слишком большое",
                    'risk_level': 'medium'
                }
            
            return {'allowed': True, 'reason': "Изображение безопасно", 'risk_level': 'low'}
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки изображения: {e}")
            return {
                'allowed': False,
                'reason': f"Ошибка анализа изображения: {e}",
                'risk_level': 'medium'
            }

    async def _check_request_structure(self, context) -> bool:
        """Проверка структуры запроса"""
        try:
            # Проверяем обязательные поля
            if not hasattr(context, 'user_input') or not context.user_input:
                return False
            
            if not hasattr(context, 'input_type') or context.input_type not in ['text', 'audio', 'image']:
                return False
            
            if not hasattr(context, 'request_id') or not context.request_id:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки структуры запроса: {e}")
            return False

    async def _advanced_security_checks(self, context) -> Dict[str, Any]:
        """Расширенные проверки безопасности"""
        # Здесь могут быть дополнительные проверки:
        # - Анализ поведения пользователя
        # - Проверка геолокации
        # - Верификация подписи запроса
        # и т.д.
        
        return {'allowed': True, 'reason': "Расширенные проверки пройдены", 'risk_level': 'low'}

    def _extract_client_id(self, request_id: str) -> str:
        """Извлечение идентификатора клиента из request_id"""
        # В реальной системе здесь может быть более сложная логика
        # Например, извлечение из заголовков или токена
        return hashlib.md5(request_id.encode()).hexdigest()[:8]

    async def _log_suspicious_activity(self, activity_type: str, details: Dict[str, Any]):
        """Логирование подозрительной активности"""
        activity = {
            'timestamp': time.time(),
            'type': activity_type,
            'details': details,
            'security_level': self.security_level
        }
        
        self.suspicious_activities.append(activity)
        
        # Сохраняем только последние 1000 событий
        if len(self.suspicious_activities) > 1000:
            self.suspicious_activities = self.suspicious_activities[-1000:]
        
        self.logger.warning(f"Подозрительная активность: {activity_type} - {details}")

    async def _load_security_patterns(self):
        """Загрузка паттернов безопасности"""
        # Базовые паттерны для проверки
        self.malicious_patterns = [
            r'(?i)(drop\s+table|insert\s+into|select\s+\*|union\s+select)',
            r'(?i)(<script|javascript:|onload=|onerror=)',
            r'(?i)(\.\./|\.\.\\|/etc/passwd)',
            r'(?i)(bash|cmd\.exe|powershell)\s+',
            r'(?i)(phishing|malware|virus|trojan)'
        ]
        
        self.suspicious_keywords = [
            'password', 'credit card', 'social security', 'confidential',
            'hack', 'exploit', 'vulnerability', 'backdoor'
        ]
        
        self.logger.debug("Паттерны безопасности загружены")

    async def _load_blacklists(self):
        """Загрузка черных списков"""
        # Здесь может быть загрузка из внешних источников или файлов
        # Пока используем пустые списки
        self.ip_blacklist = []
        self.user_blacklist = []
        
        self.logger.debug("Черные списки загружены")

    async def update_security_patterns(self, new_patterns: Dict[str, Any]):
        """Обновление паттернов безопасности"""
        if 'malicious_patterns' in new_patterns:
            self.malicious_patterns.extend(new_patterns['malicious_patterns'])
        if 'suspicious_keywords' in new_patterns:
            self.suspicious_keywords.extend(new_patterns['suspicious_keywords'])
        
        self.logger.info("Паттерны безопасности обновлены")

    async def set_security_level(self, level: str):
        """Установка уровня безопасности"""
        allowed_levels = ['low', 'medium', 'high']
        if level in allowed_levels:
            self.security_level = level
            self.logger.info(f"Уровень безопасности изменен на: {level}")
        else:
            self.logger.warning(f"Недопустимый уровень безопасности: {level}")

    async def get_security_stats(self) -> Dict[str, Any]:
        """Получение статистики безопасности"""
        return {
            'security_level': self.security_level,
            'malicious_patterns_count': len(self.malicious_patterns),
            'suspicious_keywords_count': len(self.suspicious_keywords),
            'suspicious_activities_count': len(self.suspicious_activities),
            'rate_limits_tracked': len(self.rate_limits),
            'is_initialized': self.is_initialized
        }

    async def get_recent_suspicious_activities(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение последних подозрительных активностей"""
        return self.suspicious_activities[-limit:]
    
    async def shutdown(self):
        """Корректное завершение работы шлюза безопасности"""
        self.logger.info("Завершение работы шлюза безопасности...")
        self.is_initialized = False
        self.logger.info("Шлюз безопасности завершил работу")

    async def is_healthy(self) -> bool:
        """Проверка здоровья шлюза безопасности"""
        return self.is_initialized