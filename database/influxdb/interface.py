from datetime import datetime, date, time as dtime, timedelta, timezone
from config.constants import InfluxConfig, StatusMachine, WeldingConfig
from typing import List, Dict, Optional, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

class InfluxInterface:
    def __init__(self):
        pass

    def build_field_filter(self, fields: Optional[List[str]]) -> str:
        """
        |> filter(fn: (r) => contains(value: r["_field"], set: ["voltage","ampere"]))
        """
        if not fields:
            return ""

        # escape dấu " trong tên field nếu có
        esc = lambda s: str(s).replace('"', r'\"')
        set_values = ",".join([f'"{esc(f)}"' for f in fields if f])

        return f'\n  |> filter(fn: (r) => contains(value: r["_field"], set: [{set_values}]))'


    def build_tag_filters(self, tags: Optional[List[str]]) -> str:
        """
        |> filter(fn: (r) => contains(value: r["machine_name"], set: ["Máy Hàn A","Máy Hàn F"]))
        """
        if not tags:
            return ""
        # escape dấu " nếu cần
        esc = lambda s: str(s).replace('"', r'\"')
        set_values = ",".join([f'"{esc(t)}"' for t in tags if t])
        return f'\n  |> filter(fn: (r) => contains(value: r["{InfluxConfig.MACHINE_NAME_TAG}"], set: [{set_values}]))'
    

    def parse_records(self, records) -> List[Dict]:
        out = []
        for r in records:
            tags = {k: r.values.get(k) for k in r.values.keys()
                    if not k.startswith("_") and k not in ("result", "table")}
            out.append({
                "time"          : int(r.get_time().timestamp()),
                # "measurement"   : r.get_measurement(),
                # "field"         : r.get_field(),
                "value"         : r.get_value(),
                # "tags"          : tags
            })
        return out

    def safe_tz(self, tz_name: str):
        if tz_name in ("Asia/Bangkok", "Asia/Ho_Chi_Minh", "Asia/Saigon"):
            return timezone(timedelta(hours=7))
        # cuối cùng rơi về local tz
        return datetime.now().astimezone().tzinfo

    def to_utc_rfc3339(self, dt: datetime) -> str:
        return dt.astimezone(timezone.utc).isoformat()

    def start_of_day_local(self, d: date, tz: str) -> datetime:
        tzinfo = self.safe_tz(tz)
        return datetime.combine(d, dtime.min).replace(tzinfo=tzinfo)
    

    def date_to_timestamp(self, dt: datetime, tz: str = "UTC") -> int:
        """
        Chuyển datetime -> Unix timestamp.
        - unit: 's' (giây, float), 'ms' (milli), 'us' (micro), 'ns' (nano)
        - tz:   nếu dt là naive, coi dt theo tz này (mặc định 'UTC')
        """
        if dt.tzinfo is None:
            # Gán tz cho datetime naive
            try:
                tzinfo = ZoneInfo(tz)
            except ZoneInfoNotFoundError:
                # Fallback cho máy Windows chưa cài tzdata
                if tz in ("Asia/Bangkok", "Asia/Ho_Chi_Minh", "Asia/Saigon"):
                    tzinfo = timezone(timedelta(hours=7))
                else:
                    tzinfo = datetime.now().astimezone().tzinfo
            dt = dt.replace(tzinfo=tzinfo)

        # Đổi về UTC rồi tính từ epoch
        dt_utc = dt.astimezone(timezone.utc)
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        seconds = (dt_utc - epoch).total_seconds()  # float giây

        return seconds