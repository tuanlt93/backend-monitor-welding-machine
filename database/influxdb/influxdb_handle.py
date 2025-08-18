from utils.logger import Logger
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.query_api import QueryApi
from influxdb_client.client.flux_table import FluxRecord
from datetime import datetime
from config.constants import InfluxConfig
from typing import List, Dict, Optional
from utils.pattern import Singleton

class InfluxHandle(metaclass=Singleton):
    def __init__(self, *args, **kwargs) -> None:
        self.__url = kwargs.get('url', "http://localhost:8086")
        self.__org = kwargs.get('org', "xmax")
        self.__bucket = kwargs.get('bucket', "monitor_welding_machines")
        self.__token = kwargs.get('token', "")

        self.__client = InfluxDBClient(url = self.__url, token = self.__token, org = self.__org)
        self.__write = self.__client.write_api(write_options=SYNCHRONOUS)
        self.__query: QueryApi = self.__client.query_api()

        self.__tags = []

        Logger().info("INFLUXDB READY")


    def write_sample(self,* , machine_name: str, volt_value: float, ampe_value: float):
        p1 = Point(InfluxConfig.VOLT_POINT).tag(InfluxConfig.MACHINE_NAME_TAG, machine_name) \
              .field(InfluxConfig.VOLT_FEILD, float(volt_value)).time(datetime.utcnow(), WritePrecision.S)
        
        p2 = Point(InfluxConfig.AMPE_POINT).tag(InfluxConfig.MACHINE_NAME_TAG, machine_name) \
              .field(InfluxConfig.AMPE_FEILD, float(ampe_value)).time(datetime.utcnow(), WritePrecision.S)

        self.__write.write(bucket=self.__bucket, org=self.__org, record=[p1, p2])


    def read_latest(self, measurement: str) -> Dict:
        """
        Đọc bản ghi MỚI NHẤT (global last) theo measurement (và field nếu chỉ định).
        Kết quả:
        {
        "Máy Hàn A": {"voltage": 814.53, "time": 1755461173},
        "Máy Hàn B": {"voltage": 820.12, "time": 1755461201}
        }
        """

        field_query = self.__build_field_filter([InfluxConfig.VOLT_FEILD, InfluxConfig.AMPE_FEILD])
        tags_query = self.__build_tag_filters(self.__tags)
        tags_cfg = self.__tags.copy()

        cmd_query = f'''
        from(bucket: "{self.__bucket}")
        |> range(start: -10s)
        |> filter(fn: (r) => r["_measurement"] == "{measurement}"){field_query}{tags_query}
        |> group(columns: ["{InfluxConfig.MACHINE_NAME_TAG}", "_field"])
        |> last()
        |> keep(columns: ["_time","_value","_field","{InfluxConfig.MACHINE_NAME_TAG}"])
        '''
        tables = self.__query.query(cmd_query, org=self.__org)
        records = [rec for tbl in tables for rec in tbl.records]

        # parse về dict theo (tag -> field -> {value, time})
        out: Dict[str, Dict] = {}
        for r in records:
            tag = r.values.get(InfluxConfig.MACHINE_NAME_TAG)
            if tag in tags_cfg:
                field = r.get_field()
                value = r.get_value()
                time   = r.get_time()
                epoch = int(time.timestamp())

                out[tag] = {field: value, "time": epoch}
                tags_cfg.remove(tag)
                
        for t in tags_cfg:
            out[t] = {}
        return out


    def __build_field_filter(self, fields: Optional[List[str]]) -> str:
        """
        |> filter(fn: (r) => contains(value: r["_field"], set: ["voltage","ampere"]))
        """
        if not fields:
            return ""

        # escape dấu " trong tên field nếu có
        esc = lambda s: str(s).replace('"', r'\"')
        set_values = ",".join([f'"{esc(f)}"' for f in fields if f])

        return f'\n  |> filter(fn: (r) => contains(value: r["_field"], set: [{set_values}]))'


    def __build_tag_filters(self, tags: Optional[List[str]]) -> str:
        """
        |> filter(fn: (r) => contains(value: r["machine_name"], set: ["Máy Hàn A","Máy Hàn F"]))
        """
        if not tags:
            return ""
        # escape dấu " nếu cần
        esc = lambda s: str(s).replace('"', r'\"')
        set_values = ",".join([f'"{esc(t)}"' for t in tags if t])
        return f'\n  |> filter(fn: (r) => contains(value: r["{InfluxConfig.MACHINE_NAME_TAG}"], set: [{set_values}]))'

    
    def get_tags(self, slaves_info: List):
        """
        - slave = [ 
                "id" , "name" , "volt_regs" , "ampe_regs" , "resolution" , "ampe_max" , "ampe_min" , "volt_max" , "volt_min"
            ]
        - tag = name
        """
        self.__tags.clear()
        for slave in slaves_info:
            self.__tags.append(slave['name'])

