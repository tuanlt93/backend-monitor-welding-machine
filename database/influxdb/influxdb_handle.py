from utils.logger import Logger
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.query_api import QueryApi
from influxdb_client.client.flux_table import FluxRecord
from datetime import datetime, date, time as dtime, timedelta, timezone
from config.constants import InfluxConfig, StatusMachine, WeldingConfig
from typing import List, Dict, Optional, Tuple, Callable
from utils.pattern import Singleton
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from database.influxdb.interface import InfluxInterface

class InfluxHandle(InfluxInterface, metaclass=Singleton):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self.__url = kwargs.get('url', "http://localhost:8086")
        self.__org = kwargs.get('org', "xmax")
        self.__bucket = kwargs.get('bucket', "monitor_welding_machines")
        self.__token = kwargs.get('token', "")

        self.__client = InfluxDBClient(url = self.__url, token = self.__token, org = self.__org)
        self.__write = self.__client.write_api(write_options=SYNCHRONOUS)
        self.__query: QueryApi = self.__client.query_api()

        # Đảm bảo bucket tồn tại
        self.__ensure_bucket_exists()

        # Gồm name và id
        self.__tags = {}
        self.__is_run =False

        Logger().info("INFLUXDB READY")

    def __ensure_bucket_exists(self) -> None:
        """
        Kiểm tra bucket; nếu chưa có thì tạo mới trong org hiện tại.
        YÊU CẦU token có quyền Buckets:Read/Buckets:Write và Orgs:Read (thường là All Access).
        """
        try:
            buckets_api = self.__client.buckets_api()
            bucket = buckets_api.find_bucket_by_name(self.__bucket)
            if bucket:
                Logger().info(f"Bucket '{self.__bucket}' đã tồn tại (id={bucket.id}).")
                return

            # Tìm org theo tên
            orgs_api = self.__client.organizations_api()
            try:
                org_list = orgs_api.find_organizations(org=self.__org)  # một số bản client hỗ trợ tham số org
            except TypeError:
                # fallback nếu client không hỗ trợ filter theo tham số
                org_list = orgs_api.find_organizations()

            org = next((o for o in org_list if getattr(o, "name", None) == self.__org), None)
            if org is None:
                Logger().error(f"Không tìm thấy org '{self.__org}' để tạo bucket '{self.__bucket}'")

            # Tạo bucket
            new_bucket = buckets_api.create_bucket(
                bucket_name=self.__bucket,
                org_id=org.id,
            )

            self.__is_run = True
            Logger().info(f"Đã tạo bucket '{new_bucket.name}' (id={new_bucket.id}) trong org '{self.__org}'.")
        except Exception as e:
            Logger().error(f"Không thể đảm bảo bucket tồn tại: {e}")


    def get_tags(self, slaves_info: List):
        """
        - slave = [ 
                "slave_id" , "name" , "volt_regs" , "ampe_regs" , "resolution" , "ampe_max" , "ampe_min" , "volt_max" , "volt_min"
            ]
        - tag = name
        """
        self.__tags.clear()
        for slave in slaves_info:
            self.__tags[(slave['name'])] = slave['slave_id']


    def write_sample(self,* , machine_name: str, volt_value: float, ampe_value: float):
        """
            Ghi dữ liệu với thời gian utc
        """
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
            "Máy Hàn A": {"voltage": 814.53, "time": 1755461173, "id": id},
            "Máy Hàn B": {"ampere": 820.12, "time": 1755461201, "id": id},
            "Máy Hàn C": {"id": id}
        }
        """

        field_query = self.build_field_filter([InfluxConfig.VOLT_FEILD, InfluxConfig.AMPE_FEILD])
        tags_query = self.build_tag_filters(self.__tags)
        tags_cfg = self.__tags.copy()

        cmd_query = f'''
        from(bucket: "{self.__bucket}")
        |> range(start: -{InfluxConfig.LATEST_READ_TIME}s)
        |> filter(fn: (r) => r["_measurement"] == "{measurement}"){field_query}{tags_query}
        |> group(columns: ["{InfluxConfig.MACHINE_NAME_TAG}", "_field"])
        |> last()
        |> keep(columns: ["_time","_value","_field","{InfluxConfig.MACHINE_NAME_TAG}"])
        '''
        tables = self.__query.query(cmd_query, org=self.__org)
        records = [rec for tbl in tables for rec in tbl.records]

        # parse về dict theo (tag -> field -> {value, time})
        out: Dict[str, Dict] = {}
        for name, id in self.__tags.items():
            for r in records:
                tag = r.values.get(InfluxConfig.MACHINE_NAME_TAG)
                if name == tag:
                    field = r.get_field()
                    value = r.get_value()
                    time   = r.get_time()
                    epoch = int(time.timestamp())

                    out[name] = {field: value, "id": id ,"time": epoch}
                    tags_cfg.pop(tag)
                
        for name, id in tags_cfg.items():
            out[name] = {"id": id}
        return out


    def read_data_today(self, machine_name: str, tz: str = "Asia/Bangkok") -> Dict:
        """Lấy dữ liệu từ 00:00 hôm nay (theo tz) đến hiện tại."""
        tzinfo = self.safe_tz(tz)
        today_local = datetime.now(tzinfo).date()
        start = self.start_of_day_local(today_local, tz)

        now_local = datetime.now(tzinfo)

        volt_datas, ampe_datas = self.read_data_between(machine_name = machine_name, start_time= start, stop_time= now_local)
        ratio = self.duration_above_below(machine_name = machine_name, start_time= start, stop_time= now_local)

        total_datas = {
            'machine_status_rate':{
                # StatusMachine.RUNNING   : ratio['ratio_above'],
                # StatusMachine.IDEL      : ratio['ratio_below']
                StatusMachine.RUNNING   : 16,
                StatusMachine.IDEL      : 17
            },
            'latest_data': {
                'voltage': 0.0,
                'ampere' : 0.0,
                'status' : StatusMachine.DISCONNECT
            },
            'ampe_datas': ampe_datas,
            'volt_datas': volt_datas
        }

        if not ampe_datas or not volt_datas:
            return total_datas
        
        if self.date_to_timestamp(now_local) - ampe_datas[-1]['time'] > InfluxConfig.LATEST_READ_TIME or \
            self.date_to_timestamp(now_local) - volt_datas[-1]['time'] > InfluxConfig.LATEST_READ_TIME:
            return total_datas
        
        v = volt_datas[-1]['value']
        a = ampe_datas[-1]['value']
        
        if v < WeldingConfig.VOLT_MIN and a < WeldingConfig.AMPE_MIN:
            total_datas['latest_data']['status'] = StatusMachine.IDEL
        else:
            total_datas['latest_data']['status'] = StatusMachine.RUNNING
        total_datas['latest_data']['ampere'] = a
        total_datas['latest_data']['voltage'] = v


        return total_datas


    def read_data_between(self,* , machine_name: str, start_time: datetime, stop_time: datetime) -> Tuple[List, List]:
        field_query = self.build_field_filter([InfluxConfig.AMPE_FEILD, InfluxConfig.VOLT_FEILD])
        tags_query = self.build_tag_filters([machine_name])

        cmd_flux_ape = f'''
        from(bucket: "{self.__bucket}")
        |> range(start: time(v: "{self.to_utc_rfc3339(start_time)}"),
                stop:  time(v: "{self.to_utc_rfc3339(stop_time)}"))
        |> filter(fn: (r) => r["_measurement"] == "{InfluxConfig.AMPE_POINT}"){field_query}{tags_query}
        |> aggregateWindow(every: {InfluxConfig.SAMPLE_READ_TIME}s, fn: last, createEmpty: false)
        |> keep(columns: ["_time","_value","_field","_measurement","{InfluxConfig.MACHINE_NAME_TAG}","location"])
        |> sort(columns: ["_time"])
        '''
        tables = self.__query.query(cmd_flux_ape, org=self.__org)
        records = [rec for tbl in tables for rec in tbl.records]
        ampe_datas = self.parse_records(records)


        cmd_flux_volt = f'''
        from(bucket: "{self.__bucket}")
        |> range(start: time(v: "{self.to_utc_rfc3339(start_time)}"),
                stop:  time(v: "{self.to_utc_rfc3339(stop_time)}"))
        |> filter(fn: (r) => r["_measurement"] == "{InfluxConfig.VOLT_POINT}"){field_query}{tags_query}
        |> aggregateWindow(every: {InfluxConfig.SAMPLE_READ_TIME}s, fn: last, createEmpty: false)
        |> keep(columns: ["_time","_value","_field","_measurement","{InfluxConfig.MACHINE_NAME_TAG}","location"])
        |> sort(columns: ["_time"])
        '''
        tables = self.__query.query(cmd_flux_volt, org=self.__org)
        records = [rec for tbl in tables for rec in tbl.records]
        volt_datas = self.parse_records(records)

        return volt_datas, ampe_datas


    def duration_above_below(self,*, machine_name: str, start_time: datetime, stop_time: datetime) -> Dict[str, float]:
        """
        Trả về:
        {
            "ratio_above":   seconds_above / total_seconds_perday,
            "ratio_below":   seconds_below / total_seconds_perday
        }
        """

        total_seconds_perday: int = 24 * 60 * 60 
        seconds_above: int = 0
        seconds_below: int = 0

        field_query = self.build_field_filter([InfluxConfig.AMPE_FEILD, InfluxConfig.VOLT_FEILD])
        tags_query = self.build_tag_filters([machine_name])

        cmd_flux_ape = f'''
        from(bucket: "{self.__bucket}")
        |> range(start: time(v: "{self.to_utc_rfc3339(start_time)}"),
                stop:  time(v: "{self.to_utc_rfc3339(stop_time)}"))
        |> filter(fn: (r) => r["_measurement"] == "{InfluxConfig.AMPE_POINT}"){field_query}{tags_query}
        |> keep(columns: ["_time","_value","_field","_measurement","{InfluxConfig.MACHINE_NAME_TAG}","location"])
        |> sort(columns: ["_time"])
        '''
        tables = self.__query.query(cmd_flux_ape, org=self.__org)
        records = [rec for tbl in tables for rec in tbl.records]
        ampe_datas: list = self.parse_records(records)

        seconds_above_crr = 0
        seconds_above_last = 0

        seconds_below_crr = 0
        seconds_below_last = 0

        for item in ampe_datas:
            if item['value'] > WeldingConfig.AMPE_MIN:
                seconds_below_crr = 0
                seconds_below_last = 0
                if seconds_above_crr == 0:
                    seconds_above_crr = item['time']
                    seconds_above_last = item['time']
                else:
                    seconds_above_crr = item['time']
                    if (seconds_above_crr - seconds_above_last) > InfluxConfig.LATEST_READ_TIME: 
                        seconds_above_last = seconds_above_crr
                        continue
                    seconds_above = seconds_above + seconds_above_crr - seconds_above_last
                    seconds_above_last = seconds_above_crr

            else:
                seconds_above_crr = 0
                seconds_above_last = 0

                if seconds_below_crr == 0:
                    seconds_below_crr = item['time']
                    seconds_below_last = item['time']
                else:
                    seconds_below_crr = item['time']
                    if (seconds_below_crr - seconds_below_last) > InfluxConfig.LATEST_READ_TIME: 
                        seconds_below_last = seconds_below_crr
                        continue
                    seconds_below = seconds_below + seconds_below_crr - seconds_below_last
                    seconds_below_last = seconds_below_crr

        return {
            "ratio_above": round(seconds_above / total_seconds_perday * 100, 2),
            "ratio_below": round(seconds_below / total_seconds_perday * 100, 2)
        }
