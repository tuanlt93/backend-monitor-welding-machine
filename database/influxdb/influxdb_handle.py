from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from typing import List, Tuple
import pytz
from datetime import datetime
from app.dependencies.time_converter import dateTime2Epoch
import logging

url = "http://localhost:8086"
token = "GYaRVSd5j8XVMp0R5BHA1KFlcBubU6ipBKlqEr5QDTQuSmOR31jzaitkRAPx4hF8HUe7xAdfqOihJU7D2OxYuw=="
org = "rostek"
bucket = "CLmes"

def writeData(machine_id: int, quantity: int, status_machine: int, speed: float):
    client = InfluxDBClient(url=url, token=token, org=org)

    point = (
            Point("speed_idle")
            .tag("location", f"machine_{machine_id}")
            .field("quantity", quantity)
            .field("status_machine", status_machine)
            .field("speed", speed) 
            # .time(datetime.utcnow(), WritePrecision.NS)
    )

    write_api = client.write_api(write_options=SYNCHRONOUS)
    write_api.write(bucket=bucket, org=org, record=point)
    # print("Data written successfully")
    # client.close()



def queryData(time_start: str, time_stop: str, machine_id: int) :
    client = InfluxDBClient(url=url, token=token, org=org)
    query_api = client.query_api()
    query_quantity = f'''
    from(bucket: "{bucket}")
    |> range(start: {time_start}, stop: {time_stop})
    |> filter(fn: (r) => r._measurement == "speed_idle")
    |> filter(fn: (r) => r._field == "quantity")
    |> filter(fn: (r) => r.location == "machine_{machine_id}")
    '''
    query_idle = f'''
    from(bucket: "{bucket}")
    |> range(start: {time_start}, stop: {time_stop})
    |> filter(fn: (r) => r._measurement == "speed_idle")
    |> filter(fn: (r) => r._field == "status_machine")
    |> filter(fn: (r) => r.location == "machine_{machine_id}")
    '''
    query_speed = f'''
    from(bucket: "{bucket}")
    |> range(start: {time_start}, stop: {time_stop})
    |> filter(fn: (r) => r._measurement == "speed_idle")
    |> filter(fn: (r) => r._field == "speed")
    |> filter(fn: (r) => r.location == "machine_{machine_id}")
    '''

    tables_quantity = query_api.query(query_quantity, org=org)
    tables_idle = query_api.query(query_idle, org=org)
    # print(tables_idle[0].records)
    tables_speed = query_api.query(query_speed, org=org)

    # Lấy số sản phẩm
    # Lấy số sản phẩm
    quantity: int = 0
    if tables_quantity:
        first_record = tables_quantity[0].records[0]
        last_record = tables_quantity[0].records[-1]
        first_value = first_record.get_value()
        last_value = last_record.get_value()
        quantity = last_value - first_value

    # Lấy số lần dừng máy
    data_idle: List[dict] = []
    idle_id = 1
    previous_time = None
    if tables_idle:
        for record in tables_idle[0].records:
            current_time = record.get_time()
            value = record.get_value()
            if value > 0:
                if previous_time is not None and (current_time - previous_time).total_seconds() > 30:
                    data_point = {
                        'idle_id': idle_id,
                        'start': str(previous_time.astimezone(pytz.timezone('Etc/GMT-7'))),
                        'stop': str(current_time.astimezone(pytz.timezone('Etc/GMT-7')))
                    }
                    idle_id += 1
                    data_idle.append(data_point)
                previous_time = current_time

    # Lấy vận tốc max
    speed_max: float = 0.0
    if tables_speed:
        for record in tables_speed[0].records:
            value = record.get_value()
            if value > speed_max: speed_max = value

    # client.close()
    # print(data_idle)
    return quantity, data_idle, speed_max


# t1 = "2024-05-16T02:00:00Z"
# # t2 = "2024-05-16T05:00:00Z"
# time_now = datetime.now()
# t2 = dateTime2Epoch(time_now)
# quantity, data_idle, speed_max = queryData(time_start= t1, time_stop= t2, machine_id= 1)
# print(quantity, data_idle, speed_max)