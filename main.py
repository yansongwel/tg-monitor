import os
import asyncio
import logging
import requests
import json
from telethon import TelegramClient, events, types
from dotenv import load_dotenv

import python_socks

# Load environment variables
load_dotenv()

# Configuration
API_ID = os.getenv("TG_API_ID")
API_HASH = os.getenv("TG_API_HASH")
SESSION_NAME = os.getenv("TG_SESSION_NAME", "my_session")
DINGTALK_WEBHOOK = os.getenv("DINGTALK_WEBHOOK")
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")
SERVERCHAN_KEY = os.getenv("SERVERCHAN_KEY")

# Proxy Configuration
TG_PROXY_HOST = os.getenv("TG_PROXY_HOST")
TG_PROXY_PORT = os.getenv("TG_PROXY_PORT")
TG_PROXY_TYPE = os.getenv("TG_PROXY_TYPE", "socks5")  # socks5, socks4, http

proxy = None
if TG_PROXY_HOST and TG_PROXY_PORT:
    proxy_type_map = {
        "socks5": python_socks.ProxyType.SOCKS5,
        "socks4": python_socks.ProxyType.SOCKS4,
        "http": python_socks.ProxyType.HTTP,
    }
    p_type = proxy_type_map.get(TG_PROXY_TYPE.lower(), python_socks.ProxyType.SOCKS5)
    proxy = (p_type, TG_PROXY_HOST, int(TG_PROXY_PORT))
    print(f"Using proxy: {TG_PROXY_TYPE}://{TG_PROXY_HOST}:{TG_PROXY_PORT}")

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Client
client = TelegramClient(SESSION_NAME, API_ID, API_HASH, proxy=proxy)

def send_dingtalk_alert(message: str):
    """Send alert to DingTalk"""
    if not DINGTALK_WEBHOOK:
        return
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "msgtype": "text",
        "text": {
            "content": f"[TG Monitor Alert]\n{message}"
        }
    }
    try:
        resp = requests.post(DINGTALK_WEBHOOK, json=data, timeout=10)
        if resp.status_code != 200:
            logger.error(f"Failed to send DingTalk alert: {resp.text}")
    except Exception as e:
        logger.error(f"Error sending DingTalk alert: {e}")

def send_feishu_alert(message: str):
    """Send alert to Feishu/Lark"""
    if not FEISHU_WEBHOOK:
        return

    headers = {'Content-Type': 'application/json'}
    data = {
        "msg_type": "text",
        "content": {
            "text": f"[TG Monitor Alert]\n{message}"
        }
    }
    try:
        resp = requests.post(FEISHU_WEBHOOK, json=data, timeout=10)
        if resp.status_code != 200:
            logger.error(f"Failed to send Feishu alert: {resp.text}")
    except Exception as e:
        logger.error(f"Error sending Feishu alert: {e}")

def send_serverchan_alert(message: str):
    """Send alert to ServerChan (WeChat)"""
    if not SERVERCHAN_KEY:
        return
    
    # ServerChan Turbo/SCT URL
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
    data = {
        "title": "TG Monitor Alert",
        "desp": message
    }
    try:
        resp = requests.post(url, data=data, timeout=10)
        if resp.status_code != 200:
            logger.error(f"Failed to send ServerChan alert: {resp.text}")
    except Exception as e:
        logger.error(f"Error sending ServerChan alert: {e}")

def broadcast_alert(msg: str):
    """Send to all configured channels"""
    logger.info(f"Alert Triggered: {msg}")
    send_dingtalk_alert(msg)
    send_feishu_alert(msg)
    send_serverchan_alert(msg)

@client.on(events.NewMessage(incoming=True))
async def handle_new_message(event):
    """Handle new incoming messages"""
    try:
        sender = await event.get_sender()
        sender_name = "Unknown"
        if sender:
            sender_name = getattr(sender, 'first_name', '') or getattr(sender, 'title', 'Unknown')
            if getattr(sender, 'username', None):
                sender_name += f" (@{sender.username})"
    except Exception as e:
        logger.error(f"Error getting sender: {e}")
        sender_name = "Unknown Sender"

    try:
        chat = await event.get_chat()
        chat_title = getattr(chat, 'title', 'Private Chat')
    except Exception as e:
        logger.error(f"Error getting chat: {e}")
        chat_title = "Unknown Chat"

    # 1. Private Messages
    if event.is_private:
        msg = f"📩 New Private Message\nFrom: {sender_name}\nContent: {event.text}"
        broadcast_alert(msg)
        return

    # 2. Mentions in Groups
    if event.mentioned:
        msg = f"🔔 You were mentioned\nGroup: {chat_title}\nFrom: {sender_name}\nContent: {event.text}"
        broadcast_alert(msg)
        return

@client.on(events.ChatAction)
async def handle_chat_action(event):
    """Handle chat actions like being added to a group"""
    # 3. Added to Group
    # Check if the user added is 'me'
    if event.user_added or event.user_joined:
        me = await client.get_me()
        if event.user_id == me.id:
            chat = await event.get_chat()
            chat_title = getattr(chat, 'title', 'Unknown Group')
            
            adder = await event.get_input_user()
            adder_name = "Unknown"
            if adder:
                try:
                    adder_user = await client.get_entity(adder)
                    adder_name = getattr(adder_user, 'first_name', '') or 'Unknown'
                    if getattr(adder_user, 'username', None):
                        adder_name += f" (@{adder_user.username})"
                except:
                    pass

            action_type = "Joined" if event.user_joined else "Added to"
            msg = f"👥 {action_type} Group\nGroup: {chat_title}\nBy: {adder_name}"
            broadcast_alert(msg)

async def main():
    print("Starting Telegram Monitor...")
    # Ensure the client is connected
    await client.start()
    
    me = await client.get_me()
    print(f"Monitoring account: {me.first_name} (@{me.username})")
    
    # Run until disconnected
    await client.run_until_disconnected()

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())
