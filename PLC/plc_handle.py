from PLC.rtu_interface import RtuInterface
from utils.threadpool import Worker
from config import CFG_MODBUS_RTU
from database import sqlite_handle
import time
from utils.logger import Logger

class PlcHandle():
    def __init__(self):
        """
        Initializes the connection parameters for the PLC station.

        Args:
            host: IP address of the PLC (default: "127.0.0.1")
            port: Modbus TCP port (default: 502)
            timeout: Timeout for Modbus operations (default: 1 second)
            unit: Modbus slave ID (default: 1)
        """
        self.__PLC_interface = RtuInterface(**CFG_MODBUS_RTU)
        self.__sqlite_handle = sqlite_handle
        Logger().info("PLC SERVICE READY")
        self.__PLC_service()
    
    def __get_read_plan(self) -> list[dict]:
        """
        Tạo kế hoạch đọc cho từng slave:
        - start: địa chỉ bắt đầu (min)
        - quantity: số thanh ghi cần đọc (max - min + 1)
        - offsets: map tên field -> offset trong kết quả đọc
        """
        plan = []
        slaves = self.__sqlite_handle.get_all()  # list[dict] mỗi dict có id, name, volt_regs, ampe_regs, ...
        for slave in slaves:
            start = min(slave['volt_regs'], slave['ampe_regs'])
            end   = max(slave['volt_regs'], slave['ampe_regs'])
            quantity = end - start + 1

            offsets = {
                'volt': slave['volt_regs'] - start,
                'ampe': slave['ampe_regs'] - start,
            }

            plan.append({
                'slave_id': slave['id'],
                'name': slave['name'],
                'start': start,
                'quantity': quantity,
                'offsets': offsets,
            })
        return plan


    @Worker.employ
    def __PLC_service(self):
        while True:
            plans = self.__get_read_plan()
            for p in plans:
                regs = self.__PLC_interface.read_datas(address= p['start'], num_register= p['quantity'], slave_id= p['slave_id'])

                data = {
                    'name': p['name'],
                    'volt': regs[p['offsets']['volt']],
                    'ampe': regs[p['offsets']['ampe']],
                }
                print(data)

            time.sleep(1.0)


