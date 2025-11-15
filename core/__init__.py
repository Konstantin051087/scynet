"""
Ядро системы Синтетический Разум
Координатор и основные системные компоненты
"""

from .coordinator import Coordinator
from .communication_bus import CommunicationBus
from .intent_analyzer import IntentAnalyzer
from .response_synthesizer import ResponseSynthesizer
from .module_manager import ModuleManager
from .security_gateway import SecurityGateway
from .performance_monitor import PerformanceMonitor

__all__ = [
    'Coordinator',
    'CommunicationBus', 
    'IntentAnalyzer',
    'ResponseSynthesizer',
    'ModuleManager',
    'SecurityGateway',
    'PerformanceMonitor'
]

__version__ = "1.0.0"
__author__ = "Synthetic Mind Team"