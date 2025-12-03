from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from .core.manager import ModuleManager

@register("cy_tools", "YourName", "一个模块化的工具大全插件", "1.0.0")
class CyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.manager = None

    async def initialize(self):
        self.manager = ModuleManager(self.context)
        logger.info("CyPlugin initialized and modules loaded.")

    @filter.command("cy")
    async def cy_command(self, event: AstrMessageEvent, *args):
        """工具大全入口指令"""
        # AstrBot 会自动解析参数并作为 tuple 传入 args
        # 例如 /cy sub on 北京 -> args=("sub", "on", "北京")
        
        # 将 tuple 转为 list 方便处理
        arg_list = list(args)
        
        async for result in self.manager.dispatch(event, arg_list):
            yield result

    async def terminate(self):
        pass
