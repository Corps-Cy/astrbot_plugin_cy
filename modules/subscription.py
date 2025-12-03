import json
import os
import aiohttp
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from astrbot.api.star import Context
from astrbot.api import logger
from astrbot.api.event import MessageChain
import astrbot.api.message_components as Comp
from ..core.base_module import BaseModule

class SubscriptionModule(BaseModule):
    def __init__(self, context: Context):
        super().__init__(context)
        self.data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "subscription.json")
        self.subscriptions = self.load_data()
        
        self.scheduler = AsyncIOScheduler()
        # 每天早上 8:00 执行
        self.scheduler.add_job(self.daily_push, CronTrigger(hour=8, minute=0))
        self.scheduler.start()

    @property
    def name(self) -> str:
        return "sub"

    @property
    def description(self) -> str:
        return "订阅天气和问候服务"

    def help(self) -> str:
        return (
            "订阅服务指令：\n"
            "- `cy sub on <地点>`: 开启订阅（例如 `cy sub on 北京`）\n"
            "- `cy sub off`: 取消订阅\n"
            "- `cy sub status`: 查看订阅状态"
        )

    def load_data(self):
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load subscription data: {e}")
        return {}

    def save_data(self):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.subscriptions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save subscription data: {e}")

    async def handle(self, args: list[str], event) -> str:
        if not args:
            return self.help()

        cmd = args[0].lower()
        sender_id = event.get_sender_id()
        
        if cmd == "on":
            if len(args) < 2:
                return "❌ 请指定地点，例如：`cy sub on 北京`"
            location = args[1]
            
            # 存储 unified_msg_origin 以便主动推送
            self.subscriptions[sender_id] = {
                "location": location,
                "enabled": True,
                "user_name": event.get_sender_name(),
                "unified_msg_origin": event.unified_msg_origin
            }
            self.save_data()
            return f"✅ 订阅成功！将在每天 8:00 为您推送 {location} 的天气。"

        elif cmd == "off":
            if sender_id in self.subscriptions:
                self.subscriptions[sender_id]["enabled"] = False
                self.save_data()
                return "✅ 已取消订阅。"
            return "⚠️ 您还没有订阅。"

        elif cmd == "status":
            if sender_id in self.subscriptions and self.subscriptions[sender_id]["enabled"]:
                loc = self.subscriptions[sender_id]["location"]
                return f"✅ 当前状态：已订阅 ({loc})"
            return "zk 当前状态：未订阅"

        else:
            return "❌ 未知指令。\n" + self.help()

    async def get_weather(self, location):
        try:
            # 使用 wttr.in 获取简洁格式的天气
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://wttr.in/{location}?format=%C+%t+%w") as resp:
                    if resp.status == 200:
                        return await resp.text()
        except Exception as e:
            logger.error(f"Failed to get weather: {e}")
        return "无法获取天气信息"

    async def daily_push(self):
        logger.info("Starting daily push task...")
        
        for sender_id, data in self.subscriptions.items():
            if data.get("enabled") and "unified_msg_origin" in data:
                location = data["location"]
                user_name = data.get("user_name", "用户")
                unified_msg_origin = data["unified_msg_origin"]
                
                weather = await self.get_weather(location)
                
                # 获取 AI 问候语
                greeting = "祝你今天过得愉快！"
                try:
                    provider_id = await self.context.get_current_chat_provider_id(umo=unified_msg_origin)
                    if provider_id:
                        prompt = f"请根据以下信息，为用户 {user_name} 写一段简短温馨的早安问候语（50字以内）：\n时间：{datetime.now().strftime('%Y-%m-%d %A')}\n地点：{location}\n天气：{weather}"
                        llm_resp = await self.context.llm_generate(chat_provider_id=provider_id, prompt=prompt)
                        if llm_resp and llm_resp.completion_text:
                            greeting = llm_resp.completion_text.strip()
                except Exception as e:
                    logger.error(f"Failed to generate AI greeting: {e}")

                # 构建精美的消息链
                chain = [
                    Comp.Plain(f"🌞 早上好，{user_name}！\n\n"),
                    Comp.Plain(f"📅 {datetime.now().strftime('%Y-%m-%d %A')}\n"),
                    Comp.Plain(f"📍 {location} 天气播报：\n"),
                    Comp.Plain(f"☁️ {weather}\n\n"),
                    Comp.Plain(f"🤖 AI 寄语：\n{greeting}")
                ]
                
                try:
                    await self.context.send_message(unified_msg_origin, chain)
                    logger.info(f"Pushed to {sender_id}")
                except Exception as e:
                    logger.error(f"Failed to push to {sender_id}: {e}")
