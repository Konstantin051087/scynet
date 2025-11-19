"""
Service Integrations package for API Caller module.
Contains integrations with various external services.
"""

from typing import Dict, Any, Optional

# Import weather integration
try:
    from .weather import WeatherIntegration
except ImportError as e:
    print(f"Warning: Could not import WeatherIntegration: {e}")
    WeatherIntegration = None

__all__ = ['WeatherIntegration']