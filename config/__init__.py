from utils.load_config import load_config
import os

current_path = os.getcwd()
cfg_path = os.path.join(current_path, "config.yaml")
config_all = load_config(url= cfg_path)


CFG_MODBUS_RTU  = config_all['CFG_MODBUS_RTU']
CFG_MODBUS_TCP  = config_all['CFG_MODBUS_TCP']
CFG_INFLUXDB     = config_all['CFG_INFLUXDB']
CFG_SERVER      = config_all['CFG_SERVER']