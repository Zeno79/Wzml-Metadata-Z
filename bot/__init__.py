
#!/usr/bin/env python3
from tzlocal import get_localzone
from datetime import datetime
from inspect import signature
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client as tgClient, enums, utils as pyroutils
from pymongo import MongoClient
from asyncio import Lock
from dotenv import load_dotenv, dotenv_values
from threading import Thread
from time import sleep, time
from subprocess import Popen, run as srun, check_output
from os import remove as osremove, path as ospath, environ, getcwd
from aria2p import API as ariaAPI, Client as ariaClient
from qbittorrentapi import Client as qbClient
from socket import setdefaulttimeout
from logging import getLogger, Formatter, FileHandler, StreamHandler, INFO, ERROR, basicConfig, error as log_error, info as log_info, warning as log_warning
from uvloop import install

#from faulthandler import enable as faulthandler_enable
#faulthandler_enable()
install()
setdefaulttimeout(600)

pyroutils.MIN_CHAT_ID = -999999999999
pyroutils.MIN_CHANNEL_ID = -100999999999999
botStartTime = time()

basicConfig(format="[%(asctime)s] [%(levelname)s] - %(message)s", #  [%(filename)s:%(lineno)d]
            datefmt="%d-%b-%y %I:%M:%S %p",
            handlers=[FileHandler('log.txt'), StreamHandler()],
            level=INFO)

getLogger("pyrogram").setLevel(ERROR)
getLogger("aiohttp").setLevel(ERROR)
getLogger("httpx").setLevel(ERROR)

LOGGER = getLogger(__name__)

load_dotenv('config.env', override=True)

Interval = []
QbInterval = []
QbTorrents = {}
GLOBAL_EXTENSION_FILTER = ['aria2', '!qB']
user_data = {}
extra_buttons = {}
list_drives_dict = {}
shorteners_list = []
categories_dict = {}
aria2_options = {}
qbit_options = {}
queued_dl = {}
queued_up = {}
bot_cache = {}
non_queued_dl = set()
non_queued_up = set()


try:
    if bool(environ.get('_____REMOVE_THIS_LINE_____')):
        log_error('The README.md file there to be read! Exiting now!')
        exit()
except:
    pass

download_dict_lock = Lock()
status_reply_dict_lock = Lock()
queue_dict_lock = Lock()
qb_listener_lock = Lock()
status_reply_dict = {}
download_dict = {}
rss_dict = {}

BOT_TOKEN = environ.get('BOT_TOKEN', '')
if len(BOT_TOKEN) == 0:
    log_error("BOT_TOKEN variable is missing! Exiting now")
    exit(1)

bot_id = BOT_TOKEN.split(':', 1)[0]

DATABASE_URL = environ.get('DATABASE_URL', '')
if len(DATABASE_URL) == 0:
    DATABASE_URL = ''

if DATABASE_URL:
    conn = MongoClient(DATABASE_URL)
    db = conn.wzmlx
    current_config = dict(dotenv_values('config.env'))
    old_config = db.settings.deployConfig.find_one({'_id': bot_id})
    if old_config is None:
        db.settings.deployConfig.replace_one(
            {'_id': bot_id}, current_config, upsert=True)
    else:
        del old_config['_id']
    if old_config and old_config != current_config:
        db.settings.deployConfig.replace_one(
            {'_id': bot_id}, current_config, upsert=True)
    elif config_dict := db.settings.config.find_one({'_id': bot_id}):
        del config_dict['_id']
        for key, value in config_dict.items():
            environ[key] = str(value)
    if pf_dict := db.settings.files.find_one({'_id': bot_id}):
        del pf_dict['_id']
        for key, value in pf_dict.items():
            if value:
                file_ = key.replace('__', '.')
                with open(file_, 'wb+') as f:
                    f.write(value)
    if a2c_options := db.settings.aria2c.find_one({'_id': bot_id}):
        del a2c_options['_id']
        aria2_options = a2c_options
    if qbit_opt := db.settings.qbittorrent.find_one({'_id': bot_id}):
        del qbit_opt['_id']
        qbit_options = qbit_opt
    conn.close()
    BOT_TOKEN = environ.get('BOT_TOKEN', '')
    bot_id = BOT_TOKEN.split(':', 1)[0]
    DATABASE_URL = environ.get('DATABASE_URL', '')
else:
    config_dict = {}

OWNER_ID = environ.get('OWNER_ID', '')
if len(OWNER_ID) == 0:
    log_error("OWNER_ID variable is missing! Exiting now")
    exit(1)
else:
    OWNER_ID = int(OWNER_ID)

TELEGRAM_API = environ.get('TELEGRAM_API', '')
if len(TELEGRAM_API) == 0:
    log_error("TELEGRAM_API variable is missing! Exiting now")
    exit(1)
else:
    TELEGRAM_API = int(TELEGRAM_API)

TELEGRAM_HASH = environ.get('TELEGRAM_HASH', '')
if len(TELEGRAM_HASH) == 0:
    log_error("TELEGRAM_HASH variable is missing! Exiting now")
    exit(1)

TIMEZONE = environ.get('TIMEZONE', '')
if len(TIMEZONE) == 0:
    TIMEZONE = 'Asia/Kolkata'

def changetz(*args):
    return datetime.now(timezone(TIMEZONE)).timetuple()
Formatter.converter = changetz
log_info("TIMEZONE synced with logging status")

GDRIVE_ID = environ.get('GDRIVE_ID', '')
if len(GDRIVE_ID) == 0:
    GDRIVE_ID = ''

RCLONE_PATH = environ.get('RCLONE_PATH', '')
if len(RCLONE_PATH) == 0:
    RCLONE_PATH = ''

RCLONE_FLAGS = environ.get('RCLONE_FLAGS', '')
if len(RCLONE_FLAGS) == 0:
    RCLONE_FLAGS = ''

DEFAULT_UPLOAD = environ.get('DEFAULT_UPLOAD', '')
if DEFAULT_UPLOAD != 'rc' and DEFAULT_UPLOAD != 'ddl':
    DEFAULT_UPLOAD = 'gd'

DOWNLOAD_DIR = environ.get('DOWNLOAD_DIR', '')
if len(DOWNLOAD_DIR) == 0:
    DOWNLOAD_DIR = '/usr/src/app/downloads/'
elif not DOWNLOAD_DIR.endswith("/"):
    DOWNLOAD_DIR = f'{DOWNLOAD_DIR}/'

AUTHORIZED_CHATS = environ.get('AUTHORIZED_CHATS', '')
if AUTHORIZED_CHATS:
    aid = AUTHORIZED_CHATS.split()
    for id_ in aid:
        chat_id, *topic_ids = id_.split(':')
        chat_id = int(chat_id)
        user_data.setdefault(chat_id, {'is_auth': True})
        if topic_ids:
            user_data[chat_id].setdefault('topic_ids', []).extend(map(int, topic_ids))

SUDO_USERS = environ.get('SUDO_USERS', '')
if len(SUDO_USERS) != 0:
    aid = SUDO_USERS.split()
    for id_ in aid:
        user_data[int(id_.strip())] = {'is_sudo': True}

BLACKLIST_USERS = environ.get('BLACKLIST_USERS', '')
if len(BLACKLIST_USERS) != 0:
    for id_ in BLACKLIST_USERS.split():
        user_data[int(id_.strip())] = {'is_blacklist': True}

EXTENSION_FILTER = environ.get('EXTENSION_FILTER', '')
if len(EXTENSION_FILTER) > 0:
    fx = EXTENSION_FILTER.split()
    for x in fx:
        x = x.lstrip('.')
        GLOBAL_EXTENSION_FILTER.append(x.strip().lower())

LINKS_LOG_ID = environ.get('LINKS_LOG_ID', '')
LINKS_LOG_ID = '' if len(LINKS_LOG_ID) == 0 else int(LINKS_LOG_ID)

MIRROR_LOG_ID = environ.get('MIRROR_LOG_ID', '')
if len(MIRROR_LOG_ID) == 0:
    MIRROR_LOG_ID = ''

LEECH_LOG_ID = environ.get('LEECH_LOG_ID', '')
if len(LEECH_LOG_ID) == 0:
    LEECH_LOG_ID = ''

EXCEP_CHATS = environ.get('EXCEP_CHATS', '')
if len(EXCEP_CHATS) == 0:
    EXCEP_CHATS = ''

def wztgClient(*args, **kwargs):
    if 'max_concurrent_transmissions' in signature(tgClient.__init__).parameters:
        kwargs['max_concurrent_transmissions'] = 1000
    return tgClient(*args, **kwargs)
            
IS_PREMIUM_USER = False
user = ''
USER_SESSION_STRING = environ.get('USER_SESSION_STRING', '')
if len(USER_SESSION_STRING) != 0:
    log_info("Creating client from USER_SESSION_STRING")
    try:
        user = wztgClient('user', TELEGRAM_API, TELEGRAM_HASH, session_string=USER_SESSION_STRING,
                        parse_mode=enums.ParseMode.HTML, no_updates=True).start()
        IS_PREMIUM_USER = user.me.is_premium
    except Exception as e:
        log_error(f"Failed making client from USER_SESSION_STRING : {e}")
        user = ''
                
MEGA_EMAIL = environ.get('MEGA_EMAIL', '')
MEGA_PASSWORD = environ.get('MEGA_PASSWORD', '')
if len(MEGA_EMAIL) == 0 or len(MEGA_PASSWORD) == 0:
    log_warning('MEGA Credentials not provided!')
    MEGA_EMAIL = ''
    MEGA_PASSWORD = ''

METADATA = environ.get('METADATA', '')

GDTOT_CRYPT = environ.get('GDTOT_CRYPT', '')
if len(GDTOT_CRYPT) == 0:
    GDTOT_CRYPT = ''

JIODRIVE_TOKEN = environ.get('JIODRIVE_TOKEN', '')
if len(JIODRIVE_TOKEN) == 0:
    JIODRIVE_TOKEN = ''

REAL_DEBRID_API = environ.get('REAL_DEBRID_API', '')
if len(REAL_DEBRID_API) == 0:
    REAL_DEBRID_API = ''

DEBRID_LINK_API = environ.get('DEBRID_LINK_API', '')
if len(DEBRID_LINK_API) == 0:
    DEBRID_LINK_API = ''

INDEX_URL = environ.get('INDEX_URL', '').rstrip("/")
if len(INDEX_URL) == 0:
    INDEX_URL = ''

SEARCH_API_LINK = environ.get('SEARCH_API_LINK', '').rstrip("/")
if len(SEARCH_API_LINK) == 0:
    SEARCH_API_LINK = ''

CAP_FONT = environ.get('CAP_FONT', '').lower()
if CAP_FONT.strip() not in ['', 'b', 'i', 'u', 's', 'spoiler', 'code']:
    CAP_FONT = 'code'

LEECH_FILENAME_PREFIX = environ.get('LEECH_FILENAME_PREFIX', '')
if len(LEECH_FILENAME_PREFIX) == 0:
    LEECH_FILENAME_PREFIX = ''

LEECH_FILENAME_SUFFIX = environ.get('LEECH_FILENAME_SUFFIX', '')
if len(LEECH_FILENAME_SUFFIX) == 0:
    LEECH_FILENAME_SUFFIX = ''

LEECH_FILENAME_CAPTION = environ.get('LEECH_FILENAME_CAPTION', '')
if len(LEECH_FILENAME_CAPTION) == 0:
    LEECH_FILENAME_CAPTION = ''

LEECH_FILENAME_REMNAME = environ.get('LEECH_FILENAME_REMNAME', '')
if len(LEECH_FILENAME_REMNAME) == 0:
    LEECH_FILENAME_REMNAME = ''

MIRROR_FILENAME_PREFIX = environ.get('MIRROR_FILENAME_PREFIX', '')
if len(MIRROR_FILENAME_PREFIX) == 0:
    MIRROR_FILENAME_PREFIX = ''

MIRROR_FILENAME_SUFFIX = environ.get('MIRROR_FILENAME_SUFFIX', '')
if len(MIRROR_FILENAME_SUFFIX) == 0:
    MIRROR_FILENAME_SUFFIX = ''

MIRROR_FILENAME_REMNAME = environ.get('MIRROR_FILENAME_REMNAME', '')
if len(MIRROR_FILENAME_REMNAME) == 0:
    MIRROR_FILENAME_REMNAME = ''

SEARCH_PLUGINS = environ.get('SEARCH_PLUGINS', '')
if len(SEARCH_PLUGINS) == 0:
    SEARCH_PLUGINS = ''

MAX_SPLIT_SIZE = 4194304000 if IS_PREMIUM_USER else 2097152000

LEECH_SPLIT_SIZE = environ.get('LEECH_SPLIT_SIZE', '')
if str(LEECH_SPLIT_SIZE) in ["4194304000", "2097152000"] or len(LEECH_SPLIT_SIZE) == 0 or int(LEECH_SPLIT_SIZE) > MAX_SPLIT_SIZE:
    LEECH_SPLIT_SIZE = MAX_SPLIT_SIZE
else:
    LEECH_SPLIT_SIZE = int(LEECH_SPLIT_SIZE)

BOT_MAX_TASKS = environ.get('BOT_MAX_TASKS', '')
BOT_MAX_TASKS = int(BOT_MAX_TASKS) if BOT_MAX_TASKS.isdigit() else ''

STATUS_UPDATE_INTERVAL = environ.get('STATUS_UPDATE_INTERVAL', '')
if len(STATUS_UPDATE_INTERVAL) == 0:
    STATUS_UPDATE_INTERVAL = 10
else:
    STATUS_UPDATE_INTERVAL = int(STATUS_UPDATE_INTERVAL)

AUTO_DELETE_MESSAGE_DURATION = environ.get('AUTO_DELETE_MESSAGE_DURATION', '')
if len(AUTO_DELETE_MESSAGE_DURATION) == 0:
    AUTO_DELETE_MESSAGE_DURATION = 30
else:
    AUTO_DELETE_MESSAGE_DURATION = int(AUTO_DELETE_MESSAGE_DURATION)

YT_DLP_OPTIONS = environ.get('YT_DLP_OPTIONS', '')
if len(YT_DLP_OPTIONS) == 0:
    YT_DLP_OPTIONS = ''

SEARCH_LIMIT = environ.get('SEARCH_LIMIT', '')
SEARCH_LIMIT = 0 if len(SEARCH_LIMIT) == 0 else int(SEARCH_LIMIT)

STATUS_LIMIT = environ.get('STATUS_LIMIT', '')
STATUS_LIMIT = 6 if len(STATUS_LIMIT) == 0 else int(STATUS_LIMIT)

CMD_SUFFIX = environ.get('CMD_SUFFIX', '')

RSS_CHAT = environ.get('RSS_CHAT', '')
RSS_CHAT = '' if len(RSS_CHAT) == 0 else RSS_CHAT
if RSS_CHAT.isdigit() or RSS_CHAT.startswith('-'):
    RSS_CHAT = int(RSS_CHAT)

RSS_DELAY = environ.get('RSS_DELAY', '')
RSS_DELAY = 600 if len(RSS_DELAY) == 0 else int(RSS_DELAY)

TORRENT_TIMEOUT = environ.get('TORRENT_TIMEOUT', '')
TORRENT_TIMEOUT = '' if len(TORRENT_TIMEOUT) == 0 else int(TORRENT_TIMEOUT)

QUEUE_ALL = environ.get('QUEUE_ALL', '')
QUEUE_ALL = '' if len(QUEUE_ALL) == 0 else int(QUEUE_ALL)

QUEUE_DOWNLOAD = environ.get('QUEUE_DOWNLOAD', '')
QUEUE_DOWNLOAD = '' if len(QUEUE_DOWNLOAD) == 0 else int(QUEUE_DOWNLOAD)

QUEUE_UPLOAD = environ.get('QUEUE_UPLOAD', '')
QUEUE_UPLOAD = '' if len(QUEUE_UPLOAD) == 0 else int(QUEUE_UPLOAD)

INCOMPLETE_TASK_NOTIFIER = environ.get('INCOMPLETE_TASK_NOTIFIER', '')
INCOMPLETE_TASK_NOTIFIER = INCOMPLETE_TASK_NOTIFIER.lower() == 'true'

STOP_DUPLICATE = environ.get('STOP_DUPLICATE', '')
STOP_DUPLICATE = STOP_DUPLICATE.lower() == 'true'

IS_TEAM_DRIVE = environ.get('IS_TEAM_DRIVE', '')
IS_TEAM_DRIVE = IS_TEAM_DRIVE.lower() == 'true'

USE_SERVICE_ACCOUNTS = environ.get('USE_SERVICE_ACCOUNTS', '')
USE_SERVICE_ACCOUNTS = USE_SERVICE_ACCOUNTS.lower() == 'true'

WEB_PINCODE = environ.get('WEB_PINCODE', '')
WEB_PINCODE = WEB_PINCODE.lower() == 'true'

AS_DOCUMENT = environ.get('AS_DOCUMENT', '')
AS_DOCUMENT = AS_DOCUMENT.lower() == 'true'

USER_TD_MODE = environ.get('USER_TD_MODE', '')
USER_TD_MODE = USER_TD_MODE.lower() == 'true'

USER_TD_SA = environ.get('USER_TD_SA', '')
USER_TD_SA = USER_TD_SA.lower() if len(USER_TD_SA) != 0 else ''

SHOW_MEDIAINFO = environ.get('SHOW_MEDIAINFO', '')
SHOW_MEDIAINFO = SHOW_MEDIAINFO.lower() == 'true'

SCREENSHOTS_MODE = environ.get('SCREENSHOTS_MODE', '')
SCREENSHOTS_MODE = SCREENSHOTS_MODE.lower() == 'true'

SOURCE_LINK = environ.get('SOURCE_LINK', '')
SOURCE_LINK = SOURCE_LINK.lower() == 'true'

DELETE_LINKS = environ.get('DELETE_LINKS', '')
DELETE_LINKS = DELETE_LINKS.lower() == 'true'

EQUAL_SPLITS = environ.get('EQUAL_SPLITS', '')
EQUAL_SPLITS = EQUAL_SPLITS.lower() == 'true'

MEDIA_GROUP = environ.get('MEDIA_GROUP', '')
MEDIA_GROUP = MEDIA_GROUP.lower() == 'true'

BASE_URL_PORT = environ.get('BASE_URL_PORT', '')
BASE_URL_PORT = 80 if len(BASE_URL_PORT) == 0 else int(BASE_URL_PORT)

BASE_URL = environ.get('BASE_URL', '').rstrip("/")
if len(BASE_URL) == 0:
    log_warning('BASE_URL not provided!')
    BASE_URL = ''

UPSTREAM_REPO = environ.get('UPSTREAM_REPO', '')
if len(UPSTREAM_REPO) == 0:
    UPSTREAM_REPO = ''

UPSTREAM_BRANCH = environ.get('UPSTREAM_BRANCH', '')
if len(UPSTREAM_BRANCH) == 0:
    UPSTREAM_BRANCH = 'master'

UPGRADE_PACKAGES = environ.get('UPGRADE_PACKAGES', '')
UPGRADE_PACKAGES = UPGRADE_PACKAGES.lower() == 'true'

RCLONE_SERVE_URL = environ.get('RCLONE_SERVE_URL', '')
if len(RCLONE_SERVE_URL) == 0:
    RCLONE_SERVE_URL = ''

RCLONE_SERVE_PORT = environ.get('RCLONE_SERVE_PORT', '')
RCLONE_SERVE_PORT = 8080 if len(
    RCLONE_SERVE_PORT) == 0 else int(RCLONE_SERVE_PORT)

RCLONE_SERVE_USER = environ.get('RCLONE_SERVE_USER', '')
if len(RCLONE_SERVE_USER) == 0:
    RCLONE_SERVE_USER = ''

RCLONE_SERVE_PASS = environ.get('RCLONE_SERVE_PASS', '')
if len(RCLONE_SERVE_PASS) == 0:
    RCLONE_SERVE_PASS = ''

STORAGE_THRESHOLD = environ.get('STORAGE_THRESHOLD', '')
STORAGE_THRESHOLD = '' if len(STORAGE_THRESHOLD) == 0 else float(STORAGE_THRESHOLD)

TORRENT_LIMIT = environ.get('TORRENT_LIMIT', '')
TORRENT_LIMIT = '' if len(TORRENT_LIMIT) == 0 else float(TORRENT_LIMIT)

DIRECT_LIMIT = environ.get('DIRECT_LIMIT', '')
DIRECT_LIMIT = '' if len(DIRECT_LIMIT) == 0 else float(DIRECT_LIMIT)

YTDLP_LIMIT = environ.get('YTDLP_LIMIT', '')
YTDLP_LIMIT = '' if len(YTDLP_LIMIT) == 0 else float(YTDLP_LIMIT)

GDRIVE_LIMIT = environ.get('GDRIVE_LIMIT', '')
GDRIVE_LIMIT = '' if len(GDRIVE_LIMIT) == 0 else float(GDRIVE_LIMIT)

CLONE_LIMIT = environ.get('CLONE_LIMIT', '')
CLONE_LIMIT = '' if len(CLONE_LIMIT) == 0 else float(CLONE_LIMIT)

MEGA_LIMIT = environ.get('MEGA_LIMIT', '')
MEGA_LIMIT = '' if len(MEGA_LIMIT) == 0 else float(MEGA_LIMIT)

LEECH_LIMIT = environ.get('LEECH_LIMIT', '')
LEECH_LIMIT = '' if len(LEECH_LIMIT) == 0 else float(LEECH_LIMIT)

USER_MAX_TASKS = environ.get('USER_MAX_TASKS', '')
USER_MAX_TASKS = int(USER_MAX_TASKS) if USER_MAX_TASKS.isdigit() else ''

USER_TIME_INTERVAL = environ.get('USER_TIME_INTERVAL', '')
USER_TIME_INTERVAL = int(USER_TIME_INTERVAL) if USER_TIME_INTERVAL.isdigit() else 0

PLAYLIST_LIMIT = environ.get('PLAYLIST_LIMIT', '')
PLAYLIST_LIMIT = '' if len(PLAYLIST_LIMIT) == 0 else int(PLAYLIST_LIMIT)

FSUB_IDS = environ.get('FSUB_IDS', '')
if len(FSUB_IDS) == 0:
    FSUB_IDS = ''

LINKS_LOG_ID = environ.get('LINKS_LOG_ID', '')
LINKS_LOG_ID = '' if len(LINKS_LOG_ID) == 0 else int(LINKS_LOG_ID)

BOT_PM = environ.get('BOT_PM', '')
BOT_PM = BOT_PM.lower() == 'true'

DAILY_TASK_LIMIT = environ.get('DAILY_TASK_LIMIT', '')
DAILY_TASK_LIMIT = '' if len(DAILY_TASK_LIMIT) == 0 else int(DAILY_TASK_LIMIT)

DAILY_MIRROR_LIMIT = environ.get('DAILY_MIRROR_LIMIT', '')
DAILY_MIRROR_LIMIT = '' if len(
    DAILY_MIRROR_LIMIT) == 0 else float(DAILY_MIRROR_LIMIT)

DAILY_LEECH_LIMIT = environ.get('DAILY_LEECH_LIMIT', '')
DAILY_LEECH_LIMIT = '' if len(
    DAILY_LEECH_LIMIT) == 0 else float(DAILY_LEECH_LIMIT)

DISABLE_DRIVE_LINK = environ.get('DISABLE_DRIVE_LINK', '')
DISABLE_DRIVE_LINK = DISABLE_DRIVE_LINK.lower() == 'true'

BOT_THEME = environ.get('BOT_THEME', '')
if len(BOT_THEME) == 0:
    BOT_THEME = 'minimal'

IMAGES = environ.get('IMAGES', '')
IMAGES = (IMAGES.replace("'", '').replace('"', '').replace(
    '[', '').replace(']', '').replace(",", "")).split()
if IMAGES:
    STATUS_LIMIT = 2

IMG_SEARCH = environ.get('IMG_SEARCH', '')
IMG_SEARCH = (IMG_SEARCH.replace("'", '').replace('"', '').replace(
    '[', '').replace(']', '').replace(",", "")).split()

IMG_PAGE = environ.get('IMG_PAGE', '')
IMG_PAGE = int(IMG_PAGE) if IMG_PAGE.isdigit() else ''

AUTHOR_NAME = environ.get('AUTHOR_NAME', '')
if len(AUTHOR_NAME) == 0:
    AUTHOR_NAME = 'WZML-X'

AUTHOR_URL = environ.get('AUTHOR_URL', '')
if len(AUTHOR_URL) == 0:
    AUTHOR_URL = 'https://t.me/WZML_X'

TITLE_NAME = environ.get('TITLE_NAME', '')
if len(TITLE_NAME) == 0:
    TITLE_NAME = 'WZ-M/L-X'

COVER_IMAGE = environ.get('COVER_IMAGE', '')
if len(COVER_IMAGE) == 0:
    COVER_IMAGE = 'https://graph.org/file/60f9f8bcb97d27f76f5c0.jpg'

GD_INFO = environ.get('GD_INFO', '')
if len(GD_INFO) == 0:
    GD_INFO = 'Uploaded by WZML-X'

SAVE_MSG = environ.get('SAVE_MSG', '')
SAVE_MSG = SAVE_MSG.lower() == 'true'

SAFE_MODE = environ.get('SAFE_MODE', '')
SAFE_MODE = SAFE_MODE.lower() == 'true'

SET_COMMANDS = environ.get('SET_COMMANDS', '')
SET_COMMANDS = SET_COMMANDS.lower() == 'true'

CLEAN_LOG_MSG = environ.get('CLEAN_LOG_MSG', '')
CLEAN_LOG_MSG = CLEAN_LOG_MSG.lower() == 'true'

SHOW_EXTRA_CMDS = environ.get('SHOW_EXTRA_CMDS', '')
SHOW_EXTRA_CMDS = SHOW_EXTRA_CMDS.lower() == 'true'

TOKEN_TIMEOUT = environ.get('TOKEN_TIMEOUT', '')
TOKEN_TIMEOUT = int(TOKEN_TIMEOUT) if TOKEN_TIMEOUT.isdigit() else ''

LOGIN_PASS = environ.get('LOGIN_PASS', '')
if len(LOGIN_PASS) == 0:
    LOGIN_PASS = None

FILELION_API = environ.get('FILELION_API', '')
if len(FILELION_API) == 0:
    FILELION_API = ''

IMDB_TEMPLATE = environ.get('IMDB_TEMPLATE', '')
if len(IMDB_TEMPLATE) == 0:
    IMDB_TEMPLATE = '''<b>Title: </b> {title} [{year}]
<b>Also Known As:</b> {aka}
<b>Rating ⭐️:</b> <i>{rating}</i>
<b>Release Info: </b> <a href="{url_releaseinfo}">{release_date}</a>
<b>Genre: </b>{genres}
<b>IMDb URL:</b> {url}
<b>Language: </b>{languages}
<b>Country of Origin : </b> {countries}

<b>Story Line: </b><code>{plot}</code>

<a href="{url_cast}">Read More ...</a>'''

ANIME_TEMPLATE = environ.get('ANIME_TEMPLATE', '')
if len(ANIME_TEMPLATE) == 0:
    ANIME_TEMPLATE = '''<b>{ro_title}</b>({na_title})
<b>Format</b>: <code>{format}</code>
<b>Status</b>: <code>{status}</code>
<b>Start Date</b>: <code>{startdate}</code>
<b>End Date</b>: <code>{enddate}</code>
<b>Season</b>: <code>{season}</code>
<b>Country</b>: {country}
<b>Episodes</b>: <code>{episodes}</code>
<b>Duration</b>: <code>{duration}</code>
<b>Average Score</b>: <code>{avgscore}</code>
<b>Genres</b>: {genres}
<b>Hashtag</b>: {hashtag}
<b>Studios</b>: {studios}

<b>Description</b>: <i>{description}</i>'''

MDL_TEMPLATE = environ.get('MDL_TEMPLATE', '')
if len(MDL_TEMPLATE) == 0:
    MDL_TEMPLATE = '''<b>Title:</b> {title}
<b>Also Known As:</b> {aka}
<b>Rating ⭐️:</b> <i>{rating}</i>
<b>Release Info:</b> {aired_date}
<b>Genre:</b> {genres}
<b>MyDramaList URL:</b> {url}
<b>Language:</b> #Korean
<b>Country of Origin:</b> {country}

<b>Story Line:</b> {synopsis}

<a href='{url}'>Read More ...</a>'''

config_dict = {'ANIME_TEMPLATE': ANIME_TEMPLATE,
               'AS_DOCUMENT': AS_DOCUMENT,
               'AUTHORIZED_CHATS': AUTHORIZED_CHATS,
               'AUTO_DELETE_MESSAGE_DURATION': AUTO_DELETE_MESSAGE_DURATION,
               'BASE_URL': BASE_URL,
               'BASE_URL_PORT': BASE_URL_PORT,
               'BLACKLIST_USERS': BLACKLIST_USERS,
               'BOT_TOKEN': BOT_TOKEN,
               'BOT_MAX_TASKS': BOT_MAX_TASKS,
               'CAP_FONT': CAP_FONT,
               'CMD_SUFFIX': CMD_SUFFIX,
               'DATABASE_URL': DATABAS
