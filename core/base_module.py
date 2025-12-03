from abc import ABC, abstractmethod
from astrbot.api.star import Context

class BaseModule(ABC):
    """
    所有功能模块的基类。
    """
    def __init__(self, context: Context):
        self.context = context
        self.manager = None  # Will be injected by ModuleManager

    @property
    @abstractmethod
    def name(self) -> str:
        """模块名称，用于 cy <name> 调用"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """模块描述，用于列表显示"""
        pass

    @abstractmethod
    def help(self) -> str:
        """返回模块的帮助信息"""
        pass

    @abstractmethod
    async def handle(self, args: list[str], event) -> str:
        """
        处理指令
        :param args: 参数列表
        :param event: AstrMessageEvent 对象
        :return: 返回给用户的消息文本
        """
        pass
