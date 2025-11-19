#!/usr/bin/env python3
"""ТЕСТ СТРУКТУРЫ ПРОЕКТА СИНТЕТИЧЕСКИЙ РАЗУМ"""

import json
import logging
import os
import sys
import time
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

class ProjectStructureTest:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.test_results = {
            "project": "Синтетический Разум - Структура проекта",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python_version": sys.version,
            "overall_status": "IN_PROGRESS",
            "project_structure": {},
            "required_directories": {},
            "required_files": {},
            "recommendations": [],
        }

    def print_header(self, message: str):
        """Печать заголовка раздела"""
        print(f"\n{'='*80}")
        print(f"🔍 {message}")
        print(f"{'='*80}")

    def print_section(self, message: str):
        """Печать заголовка подраздела"""
        print(f"\n{'─'*60}")
        print(f"📁 {message}")
        print(f"{'─'*60}")

    def print_result(self, test_name: str, status: bool, details: str = ""):
        """Печать результата теста"""
        icon = "✅" if status else "❌"
        status_text = "СОЗДАН" if status else "ОТСУТСТВУЕТ"
        print(f"{icon} {test_name}: {status_text}")
        if details:
            print(f"   📝 {details}")
        return status

    def scan_project_structure(self):
        """Сканирование и анализ структуры проекта Синтетический Разум"""
        self.print_header("📁 АНАЛИЗ СТРУКТУРЫ ПРОЕКТА СИНТЕТИЧЕСКИЙ РАЗУМ")

        structure = {}
        # Исключаем указанные каталоги
        excluded_dirs = {".git", "__pycache__", ".pytest_cache", "venv", "env", ".env", ".vscode", ".venv", ".pytest_cache"}
        excluded_files = {".DS_Store", "*.pyc", "*.pyo"}

        def scan_directory(path: Path, level=0):
            rel_path = path.relative_to(self.base_dir)
            dir_structure = {
                "type": "directory",
                "path": str(rel_path),
                "files": [],
                "subdirs": {},
            }

            try:
                for item in path.iterdir():
                    if item.name in excluded_dirs:
                        continue
                    if any(item.name.endswith(ext) for ext in [".pyc", ".pyo"]):
                        continue

                    if item.is_dir():
                        dir_structure["subdirs"][item.name] = scan_directory(item, level + 1)
                    else:
                        file_info = {
                            "name": item.name,
                            "size": item.stat().st_size,
                            "modified": time.ctime(item.stat().st_mtime),
                        }
                        dir_structure["files"].append(file_info)
            except PermissionError:
                dir_structure["error"] = "Permission denied"

            return dir_structure

        structure = scan_directory(self.base_dir)
        self.test_results["project_structure"] = structure

        self.print_section("ОБЩАЯ СТРУКТУРА ПРОЕКТА")
        self._print_tree(structure)

        return True

    def _print_tree(self, structure: dict, prefix: str = ""):
        """Рекурсивный вывод дерева структуры"""
        if "path" in structure:
            print(f"{prefix}📁 {structure['path']}/")

        for file_info in structure.get("files", []):
            print(f"{prefix}   📄 {file_info['name']} ({file_info['size']} bytes)")

        for dir_name, dir_structure in structure.get("subdirs", {}).items():
            self._print_tree(dir_structure, prefix + "   ")

    def check_required_directories(self):
        """Проверка обязательных директорий проекта"""
        self.print_section("ПРОВЕРКА ОБЯЗАТЕЛЬНЫХ ДИРЕКТОРИЙ")

        required_dirs = {
            "core/": "Ядро системы - координатор и основные модули",
            "modules/interface/": "Модули интерфейсов (речь, текст, изображения)",
            "modules/cognitive/": "Когнитивные модули (память, логика, творчество)",
            "modules/planning/": "Модули планирования и целеполагания",
            "modules/skills/": "Модули навыков (поиск, API, действия)",
            "data/training/": "Данные для обучения моделей",
            "data/models/": "Сохраненные модели ИИ",
            "data/runtime/": "Данные времени выполнения",
            "config/": "Конфигурационные файлы системы",
            "logs/": "Система логирования",
            "tests/": "Тесты системы",
            "docs/": "Документация проекта",
            "scripts/": "Вспомогательные скрипты",
        }

        results = {}
        for dir_path, description in required_dirs.items():
            full_path = self.base_dir / dir_path
            exists = full_path.exists() and full_path.is_dir()
            self.print_result(f"Директория {dir_path}", exists, description)
            results[dir_path] = {
                "exists": exists,
                "description": description,
                "path": str(full_path)
            }

        self.test_results["required_directories"] = results
        return all(result["exists"] for result in results.values())

    def check_required_files(self):
        """Проверка обязательных файлов проекта"""
        self.print_section("ПРОВЕРКА ОБЯЗАТЕЛЬНЫХ ФАЙЛОВ")

        required_files = {
            "main.py": "Главный запускаемый файл (точка входа)",
            "core/coordinator.py": "Главный класс-координатор системы",
            "core/communication_bus.py": "Шина сообщений между модулями",
            "core/security_gateway.py": "Шлюз безопасности системы",
            "core/performance_monitor.py": "Монитор производительности",
            "config/system.yaml": "Основные настройки системы",
            "requirements.txt": "Зависимости проекта",
        }

        results = {}
        for file_path, description in required_files.items():
            full_path = self.base_dir / file_path
            exists = full_path.exists() and full_path.is_file()
            self.print_result(f"Файл {file_path}", exists, description)
            results[file_path] = {
                "exists": exists,
                "description": description,
                "path": str(full_path)
            }

        self.test_results["required_files"] = results
        return all(result["exists"] for result in results.values())

    def check_module_structure(self):
        """Проверка структуры модулей"""
        self.print_section("ПРОВЕРКА СТРУКТУРЫ МОДУЛЕЙ")

        module_dirs = {
            "modules/interface/speech_recognizer/": "Модуль распознавания речи",
            "modules/interface/text_understander/": "Модуль понимания текста",
            "modules/interface/speech_generator/": "Модуль генерации речи",
            "modules/interface/visual_processor/": "Модуль обработки изображений",
            "modules/cognitive/memory_short_term/": "Кратковременная память",
            "modules/cognitive/memory_long_term/": "Долговременная память",
            "modules/cognitive/logic_analyzer/": "Логический анализатор",
            "modules/cognitive/creativity/": "Модуль творчества",
            "modules/cognitive/emotional_engine/": "Эмоциональный интеллект",
            "modules/planning/task_planner/": "Планировщик задач",
            "modules/planning/goals/": "Управление целями",
            "modules/skills/search_agent/": "Поисковый агент",
            "modules/skills/api_caller/": "Работа с API",
            "modules/skills/action_executor/": "Исполнитель действий",
        }

        results = {}
        for dir_path, description in module_dirs.items():
            full_path = self.base_dir / dir_path
            exists = full_path.exists() and full_path.is_dir()
            
            # Проверяем наличие __init__.py в модуле
            init_file = full_path / "__init__.py"
            has_init = init_file.exists() if exists else False
            
            status = exists and has_init
            status_text = "✅ СОЗДАН" if status else "❌ ОТСУТСТВУЕТ"
            
            print(f"{status_text} {dir_path}: {description}")
            if exists and not has_init:
                print(f"   ⚠️  Отсутствует __init__.py в модуле")
            
            results[dir_path] = {
                "exists": exists,
                "has_init": has_init,
                "description": description,
                "path": str(full_path)
            }

        self.test_results["module_structure"] = results
        return all(result["exists"] and result["has_init"] for result in results.values())

    def analyze_architecture_compliance(self):
        """Анализ соответствия архитектуре проекта"""
        self.print_section("АНАЛИЗ СООТВЕТСТВИЯ АРХИТЕКТУРЕ")

        # Ключевые компоненты из архитектуры
        architecture_components = {
            "Точка входа (main.py)": "main.py" in [f for f in self.test_results["required_files"] if self.test_results["required_files"][f]["exists"]],
            "Координатор системы": "core/coordinator.py" in [f for f in self.test_results["required_files"] if self.test_results["required_files"][f]["exists"]],
            "Шина сообщений": "core/communication_bus.py" in [f for f in self.test_results["required_files"] if self.test_results["required_files"][f]["exists"]],
            "Безопасность": "core/security_gateway.py" in [f for f in self.test_results["required_files"] if self.test_results["required_files"][f]["exists"]],
            "Интерфейсы ввода": all(self.test_results["module_structure"][f]["exists"] for f in [
                "modules/interface/speech_recognizer/",
                "modules/interface/text_understander/",
                "modules/interface/visual_processor/"
            ] if f in self.test_results["module_structure"]),
            "Когнитивные функции": all(self.test_results["module_structure"][f]["exists"] for f in [
                "modules/cognitive/memory_short_term/",
                "modules/cognitive/memory_long_term/", 
                "modules/cognitive/logic_analyzer/"
            ] if f in self.test_results["module_structure"]),
            "Система планирования": all(self.test_results["module_structure"][f]["exists"] for f in [
                "modules/planning/task_planner/",
                "modules/planning/goals/"
            ] if f in self.test_results["module_structure"]),
            "Внешние навыки": all(self.test_results["module_structure"][f]["exists"] for f in [
                "modules/skills/search_agent/",
                "modules/skills/api_caller/",
                "modules/skills/action_executor/"
            ] if f in self.test_results["module_structure"]),
        }

        results = {}
        for component, exists in architecture_components.items():
            self.print_result(f"Архитектурный компонент: {component}", exists)
            results[component] = exists

        compliance_percentage = (sum(results.values()) / len(results)) * 100 if results else 0
        print(f"\n📊 Соответствие архитектуре: {compliance_percentage:.1f}%")

        self.test_results["architecture_compliance"] = {
            "components": results,
            "compliance_percentage": compliance_percentage
        }

        return compliance_percentage >= 80

    def generate_recommendations(self):
        """Генерация рекомендаций по улучшению структуры"""
        self.print_section("РЕКОМЕНДАЦИИ ПО СТРУКТУРЕ ПРОЕКТА")

        recommendations = []

        # Анализ отсутствующих директорий
        missing_dirs = [dir_path for dir_path, info in self.test_results["required_directories"].items() 
                       if not info["exists"]]
        if missing_dirs:
            recommendations.append("📁 ОТСУТСТВУЮТ ДИРЕКТОРИИ:")
            for dir_path in missing_dirs:
                recommendations.append(f"   • Создать директорию: {dir_path}")

        # Анализ отсутствующих файлов
        missing_files = [file_path for file_path, info in self.test_results["required_files"].items() 
                        if not info["exists"]]
        if missing_files:
            recommendations.append("📄 ОТСУТСТВУЮТ ФАЙЛЫ:")
            for file_path in missing_files:
                recommendations.append(f"   • Создать файл: {file_path}")

        # Анализ модулей без __init__.py
        modules_without_init = [module_path for module_path, info in self.test_results.get("module_structure", {}).items()
                               if info["exists"] and not info["has_init"]]
        if modules_without_init:
            recommendations.append("🐍 МОДУЛИ БЕЗ __init__.py:")
            for module_path in modules_without_init:
                recommendations.append(f"   • Добавить __init__.py в: {module_path}")

        # Рекомендации по архитектуре
        if self.test_results.get("architecture_compliance", {}).get("compliance_percentage", 0) < 80:
            recommendations.append("🏗️  УЛУЧШЕНИЕ АРХИТЕКТУРЫ:")
            recommendations.append("   • Убедитесь, что все ключевые компоненты архитектуры реализованы")
            recommendations.append("   • Проверьте взаимодействие между модулями через шину сообщений")
            recommendations.append("   • Настройте конфигурацию системы в config/system.yaml")

        # Общие рекомендации
        recommendations.extend([
            "🚀 ОБЩИЕ РЕКОМЕНДАЦИИ:",
            "   • Следуйте принципам модульности из архитектуры проекта",
            "   • Используйте communication_bus для взаимодействия между модулями",
            "   • Настройте security_gateway для проверки всех запросов",
            "   • Реализуйте performance_monitor для сбора метрик",
            "   • Создайте requirements.txt со всеми зависимостями",
        ])

        self.test_results["recommendations"] = recommendations

        for recommendation in recommendations:
            print(f"• {recommendation}")

        return recommendations

    def save_report(self):
        """Сохранение отчета в файл"""
        report_dir = self.base_dir / "report"
        report_dir.mkdir(exist_ok=True)

        report_file = report_dir / "project_structure_report.json"
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
            self.print_result("Сохранение отчета", True, f"Файл: {report_file}")
            return True
        except Exception as e:
            self.print_result("Сохранение отчета", False, f"Ошибка: {e}")
            return False

    def run_comprehensive_test(self):
        """Запуск комплексного тестирования структуры проекта"""
        self.print_header("🚀 ТЕСТ СТРУКТУРЫ ПРОЕКТА СИНТЕТИЧЕСКИЙ РАЗУМ")
        print(f"📅 Время начала: {self.test_results['timestamp']}")
        print(f"🐍 Версия Python: {sys.version.split()[0]}")
        print(f"📁 Директория проекта: {self.base_dir}")

        # Запуск всех проверок
        self.scan_project_structure()
        dirs_ok = self.check_required_directories()
        files_ok = self.check_required_files()
        modules_ok = self.check_module_structure()
        architecture_ok = self.analyze_architecture_compliance()

        # Генерация рекомендаций
        self.generate_recommendations()

        # Сохранение отчета
        self.save_report()

        # Финальный отчет
        self.print_header("📊 ФИНАЛЬНЫЙ ОТЧЕТ СТРУКТУРЫ ПРОЕКТА")

        total_checks = 4
        passed_checks = sum([dirs_ok, files_ok, modules_ok, architecture_ok])
        success_rate = (passed_checks / total_checks) * 100

        print(f"🏁 ОБЩИЙ СТАТУС: {'✅ УСПЕШНО' if success_rate >= 80 else '⚠️ ТРЕБУЕТ ДОРАБОТКИ'}")
        print(f"📈 УРОВЕНЬ СООТВЕТСТВИЯ: {success_rate:.1f}%")
        print(f"✅ ВЫПОЛНЕНО ПРОВЕРОК: {passed_checks}/{total_checks}")

        print(f"\n📋 РЕЗУЛЬТАТЫ ПРОВЕРОК:")
        print(f"   📁 Директории: {'✅' if dirs_ok else '❌'}")
        print(f"   📄 Файлы: {'✅' if files_ok else '❌'}")
        print(f"   🧩 Модули: {'✅' if modules_ok else '❌'}")
        print(f"   🏗️  Архитектура: {'✅' if architecture_ok else '❌'}")

        architecture_compliance = self.test_results.get("architecture_compliance", {}).get("compliance_percentage", 0)
        print(f"\n🎯 СООТВЕТСТВИЕ АРХИТЕКТУРЕ: {architecture_compliance:.1f}%")

        if success_rate >= 80:
            print("\n🎉 СТРУКТУРА ПРОЕКТА СООТВЕТСТВУЕТ ТРЕБОВАНИЯМ!")
            print("🚀 МОЖНО ПРИСТУПАТЬ К РАЗРАБОТКЕ И ИНТЕГРАЦИИ МОДУЛЕЙ!")
        else:
            print("\n🔧 СТРУКТУРА ПРОЕКТА ТРЕБУЕТ ДОРАБОТКИ!")
            print("📝 ВЫПОЛНИТЕ РЕКОМЕНДАЦИИ ИЗ ОТЧЕТА")

        self.test_results["overall_status"] = "COMPLETED" if success_rate >= 80 else "NEEDS_IMPROVEMENT"
        self.test_results["success_rate"] = success_rate

        return success_rate >= 80

def main():
    """Основная функция"""
    print("🚀 ЗАПУСК ТЕСТА СТРУКТУРЫ ПРОЕКТА СИНТЕТИЧЕСКИЙ РАЗУМ")

    try:
        input("\nНажмите Enter для начала тестирования структуры проекта...")
    except KeyboardInterrupt:
        print("\n❌ Тестирование прервано пользователем")
        sys.exit(1)

    tester = ProjectStructureTest()
    success = tester.run_comprehensive_test()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()