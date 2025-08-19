from database.sqlite.sqlite_handle import SqliteHandle
from database.influxdb.influxdb_handle import InfluxHandle
from config import CFG_INFLUXDB, CFG_SQLITE
from dotenv import load_dotenv
from pathlib import Path
import os

# Tự động đọc file .env cạnh file hiện tại
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
token  = os.getenv("INFLUX_TOKEN")  # nên bắt buộc phải có

CFG_INFLUXDB['token'] = token

sqlite_handle = SqliteHandle(**CFG_SQLITE)

influx_handle = InfluxHandle(**CFG_INFLUXDB)
