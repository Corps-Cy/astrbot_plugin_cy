import os
import pkgutil
import importlib
import inspect
from typing import Dict, Type
from astrbot.api.star import Context
from astrbot.api import logger
from .base_module import BaseModule

class ModuleManager:
    def __init__(self, context: Context):
        self.context = context
        self.modules: Dict[str, BaseModule] = {}
        self.load_modules()

    def load_modules(self):
        """
        自动加载 modules 目录下的所有模块
        """
        modules_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "modules")
        if not os.path.exists(modules_path):
            logger.warning(f"Modules directory not found: {modules_path}")
            return

        for _, name, _ in pkgutil.iter_modules([modules_path]):
            try:
                module = importlib.import_module(f"astrbot_plugin_cy.modules.{name}")
                for item_name, item in inspect.getmembers(module, inspect.isclass):
                    if issubclass(item, BaseModule) and item is not BaseModule:
                        instance = item(self.context)
                        instance.manager = self
                        self.modules[instance.name] = instance
                        logger.info(f"Loaded module: {instance.name}")
            except Exception as e:
                logger.error(f"Failed to load module {name}: {e}")

    def get_help(self) -> str:
        """
        生成总览帮助信息
        """
        help_text = "🛠️ 工具大全 (cy)\n\n可用模块：\n"
        for name, module in self.modules.items():
            help_text += f"- {name}: {module.description}\n"
        help_text += "\n使用 `cy <模块名> help` 查看具体帮助。"
        return help_text

    async def dispatch(self, event, args: list[str]):
        """
        分发指令
        """
        if not args:
            yield event.plain_result(self.get_help())
            return

        module_name = args[0]
        remaining_args = args[1:]

        if module_name in self.modules:
            module = self.modules[module_name]
            if remaining_args and remaining_args[0] == "help":
                yield event.plain_result(module.help())
            else:
                result = await module.handle(remaining_args, event)
                if result:
                    yield event.plain_result(result)
        else:
            yield event.plain_result(f"❌ 未知模块: {module_name}\n\n" + self.get_help())
