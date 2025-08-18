from PLC.rtu_interface import RtuInterface
from utils.threadpool import Worker
from config import CFG_MODBUS_RTU
from config.constants import WeldingConfig
from database import sqlite_handle, influx_handle
import time
from utils.logger import Logger
from utils.pattern import Singleton

class PlcHandle(metaclass=Singleton):
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
        self.__influx_handle = influx_handle

        self.__plan = []
        self.get_plan()

        Logger().info("PLC SERVICE READY")
        self.__PLC_service()
    
    def get_plan(self):
        """
        Tạo kế hoạch đọc cho từng slave:
        - start: địa chỉ bắt đầu (min)
        - quantity: số thanh ghi cần đọc (max - min + 1)
        - offsets: map tên field -> offset trong kết quả đọc
        - slave = [ 
                "id" , "name" , "volt_regs" , "ampe_regs" , "resolution" , "ampe_max" , "ampe_min" , "volt_max" , "volt_min"
            ]
        """
        self.__plan.clear()
        slaves = self.__sqlite_handle.get_all()  # list[dict] mỗi dict có id, name, volt_regs, ampe_regs, ...
        for slave in slaves:
            start = min(slave['volt_regs'], slave['ampe_regs'])
            end   = max(slave['volt_regs'], slave['ampe_regs'])
            quantity = end - start + 1

            offsets = {
                'volt': slave['volt_regs'] - start,
                'ampe': slave['ampe_regs'] - start,
            }

            self.__plan.append({
                'slave_id'  : slave['id'],
                'name'      : slave['name'],
                'resolution': slave['resolution'],
                'ampe_max'  : slave['ampe_max'],
                'ampe_min'  : slave['ampe_min'],
                'volt_max'  : slave['volt_max'],
                'volt_min'  : slave['volt_min'],
                'volt_regs' : slave['volt_regs'],
                'ampe_regs' : slave['ampe_regs'],

                # 'start': start,
                # 'quantity': quantity,
                # 'offsets': offsets,
            })

        self.__influx_handle.get_tags(self.__plan)


    @Worker.employ
    def __PLC_service(self):
        while True:
            for p in self.__plan:
                # regs_value = self.__PLC_interface.read_datas(address= p['start'], num_register= p['quantity'], slave_id= p['slave_id'])
                # if regs_value:
                #     volt_current: float = round(
                #         (p['volt_max'] - p['volt_min']) / p['resolution'] * regs_value[p['offsets']['volt']],
                #         2
                #     )

                #     ampe_current: float = round(
                #         (p['ampe_max'] - p['ampe_min']) / p['resolution'] * regs_value[p['offsets']['ampe']],
                #         2
                #     )

                #     self.__influx_handle.write_sample(machine_name= p['name'],
                #                                     volt_value= volt_current,
                #                                     ampe_value= ampe_current
                #                                     )
                    
                regs_value = self.__PLC_interface.read_datas(address= 0, num_register= 9, slave_id= p['slave_id'])
                if regs_value:
                    volt_current: float = round(
                        (p['volt_max'] - p['volt_min']) / (p['resolution']) * regs_value[p['volt_regs']],
                        2
                    )

                    ampe_current: float = round(
                        (p['ampe_max'] - p['ampe_min']) / (p['resolution']) * regs_value[p['ampe_regs']],
                        2
                    )

                    self.__influx_handle.write_sample(machine_name= p['name'],
                                                    volt_value= volt_current,
                                                    ampe_value= ampe_current
                                                    )

