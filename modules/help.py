from astrbot.api.star import Context
from ..core.base_module import BaseModule

class HelpModule(BaseModule):
    @property
    def name(self) -> str:
        return "help"

    @property
    def description(self) -> str:
        return "显示帮助信息"

    def help(self) -> str:
        return "使用 `cy help` 查看所有可用指令。"

    async def handle(self, args: list[str], event) -> str:
        if not self.manager:
            return "❌ 错误：无法访问模块管理器。"
            
        help_text = "🛠️ 工具大全 (cy) - 指令列表\n\n"
        for name, module in self.manager.modules.items():
            help_text += f"🔹 `cy {name}`: {module.description}\n"
        
        help_text += "\n💡 发送 `cy <模块名> help` 可查看具体模块的详细用法。"
        return help_text
