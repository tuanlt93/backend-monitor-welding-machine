from PLC.rtu_interface import RtuInterface
from utils.threadpool import Worker
from config import CFG_MODBUS_RTU
from config.constants import WeldingConfig
from database import sqlite_handle, influx_handle
import time
from utils.logger import Logger
from utils.pattern import Singleton
import struct

typeWeldingMC=[1,1,1,1,1]
number_welder = 5
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
        self.runtimecurrent = []
        self.runtimeold = []
        self.get_plan()
        self.read_file_runtime_cr()
        Logger().info("PLC SERVICE READY")
        self.__PLC_service()
    
    def read_file_runtime_cr(self):
        """
        Docstring for read_file_runtime_cr
        Doc du lieu lu tru thời gian chạy từ file txt
        :param self: Description
        """
        with open("database/runtimecurrent.txt", "r") as f:
            a = f.readlines()
            for i in range(0,number_welder):
                if ((a[i] != None) or (a[i]!= "")):
                    self.runtimecurrent.append(float((a[i].strip())))
                else:
                    self.runtimecurrent.append(0.0)
                    f.close()
                self.runtimeold.append(time.time())
                

    def write_file_runtime_cr(self):
        with open("database/runtimecurrent.txt", "w", encoding="utf-8") as f:
            for valuecr in self.runtimecurrent:
                f.writelines(str(valuecr)+"\n")
            f.close()


    def get_plan(self):
        """
        Tạo kế hoạch đọc cho từng slave:
        - start: địa chỉ bắt đầu (min)
        - quantity: số thanh ghi cần đọc (max - min + 1)
        - offsets: map tên field -> offset trong kết quả đọc
        - slave = [ 
                "id" , "name" , "volt_regs" , "ampe_regs" , "resolution" , "ampe_max" , "ampe_min" , "volt_max" , "volt_min","mc_type"
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
                'mc_type'   : slave['mc_type'],
                

                # 'start': start,
                # 'quantity': quantity,
                # 'offsets': offsets,
            })

        self.__influx_handle.get_tags(self.__plan)


    @Worker.employ
    def __PLC_service(self):
        while True:
            i = 0
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
                try:    
                #     regs_value = self.__PLC_interface.read_datas(address= 0, num_register= 9, slave_id= p['slave_id'])
                #     regs_value2 = self.__PLC_interface.read_datas(address= 4126, num_register= 2, slave_id= p['slave_id'] + 5)
                #     # Logger().info(str(regs_value2[0]))
                #     if regs_value and  regs_value2:
                #         volt_current: float = round(
                #             (p['volt_max'] - p['volt_min']) / (p['resolution']) * regs_value[p['volt_regs']],
                #             2
                #         )

                #         ampe_current: float = round(
                #             (p['ampe_max'] - p['ampe_min']) / (p['resolution']) * regs_value[p['ampe_regs']],
                #             2
                #         )

                        
                #         statusMC = int(0) # no connect
                #         if int(volt_current) > WeldingConfig.VOLT_MIN and int(ampe_current) > WeldingConfig.AMPE_MIN:
                #             deltatime = time.time() - self.runtimeold[i]
                #             self.runtimecurrent[i] = self.runtimecurrent[i] + deltatime
                #             statusMC = int(2)   #run
                #         else:
                #             volt_current = 0
                #             ampe_current = 0
                #             statusMC = int(1) # idle
                #         self.runtimeold[i] = time.time()
                        
                #         self.write_file_runtime_cr() # ghi thơi gian han thơi diem hien tai vao file

                #         # Tinh toan cong suat tieu thu, toc do ra day va luong day
                #         u = regs_value2[0] * 65536 + regs_value2[1]
                #         power_consumption = struct.unpack('>f', u.to_bytes(4, 'big'))[0]
                #         # Logger().info(str(power_consumption))
                    
                #         self.__influx_handle.write_sample(machine_name= p['name'],
                #                                         volt_value= volt_current,
                #                                         ampe_value= ampe_current,
                #                                         run_time=self.runtimecurrent[i],
                #                                         machineStatus = statusMC,
                #                                         machine_energy_cs_value= power_consumption*100,
                #                                         wire_speed_value= 1.4,
                #                                         wire_cs_value= 1.4 * float(self.runtimecurrent[i]),
                #                                         gas_amount_value= 0.22 * float(self.runtimecurrent[i])
                #                                         )
                        
                #     else:
                #         self.__influx_handle.write_sample(machine_name= p['name'],
                #                                     volt_value= 0,
                #                                     ampe_value= 0,
                #                                     run_time=self.runtimecurrent[i],
                #                                     machineStatus = 0,
                #                                     machine_energy_cs_value= 0,
                #                                     wire_speed_value= 1.4,
                #                                     wire_cs_value= 1.4 * float(self.runtimecurrent[i]),
                #                                     gas_amount_value= 0.22 * float(self.runtimecurrent[i])
                #                                     )
                        
                # except:
                #     self.__influx_handle.write_sample(machine_name= p['name'],
                #                                     volt_value= 0,
                #                                     ampe_value= 0,
                #                                     run_time=self.runtimecurrent[i],
                #                                     machineStatus = 0,
                #                                     machine_energy_cs_value= 0,
                #                                     wire_speed_value= 1.4,
                #                                     wire_cs_value= 1.4 * float(self.runtimecurrent[i]),
                #                                     gas_amount_value= 0.22 * float(self.runtimecurrent[i])
                #                                     )

                ####  Cai tien doc tu PLC
                    regs_value = self.__PLC_interface.read_datas(address= 9999, num_register= 10, slave_id= p['slave_id'])
                    # Logger().info(str(regs_value2[0]))
                    if regs_value:
                        # volt_current: float = round(
                        #     (p['volt_max'] - p['volt_min']) / (p['resolution']) * regs_value[0],
                        #     2
                        # )

                        # ampe_current: float = round(
                        #     (p['ampe_max'] - p['ampe_min']) / (p['resolution']) * regs_value[1],
                        #     2
                        # )

                        volt_current: float = round(
                            regs_value[0]/10,
                            1
                        )

                        ampe_current: float = round(
                            regs_value[1]/10,
                            1
                        )
                        
                        tg_han = (regs_value[3] * 65536 + regs_value[2])
                        
                        statusMC = int(0) # no connect
                        if int(volt_current) > WeldingConfig.VOLT_MIN and int(ampe_current) > WeldingConfig.AMPE_MIN:
                            # deltatime = time.time() - self.runtimeold[i]
                            # self.runtimecurrent[i] = self.runtimecurrent[i] + deltatime

                            self.runtimecurrent[i] = tg_han
                            statusMC = int(2)   #run
                        else:
                            volt_current = 0
                            ampe_current = 0
                            statusMC = int(1) # idle
                        # self.runtimeold[i] = time.time()
                        self.runtimeold[i] = self.runtimecurrent[i]
                        
                        self.write_file_runtime_cr() # ghi thơi gian han thơi diem hien tai vao file

                        # Tinh toan cong suat tieu thu, toc do ra day va luong day
                        u = regs_value[5] * 65536 + regs_value[4]
                        power_consumption = struct.unpack('>f', u.to_bytes(4, 'big'))[0]

                        u1 = (regs_value[8] * 65536 + regs_value[7])/1000
                        # wire_consumption =  struct.unpack('>f', u1.to_bytes(4, 'big'))[0]
                        # Logger().info(str(power_consumption))

                        
                    
                        self.__influx_handle.write_sample(machine_name= p['name'],
                                                        volt_value= volt_current,
                                                        ampe_value= ampe_current,
                                                        run_time=self.runtimecurrent[i],
                                                        machineStatus = statusMC,
                                                        machine_energy_cs_value= power_consumption*100,
                                                        wire_speed_value= regs_value[6],
                                                        wire_cs_value= u1,
                                                        gas_amount_value= 0
                                                        )
                        
                    else:
                        self.__influx_handle.write_sample(machine_name= p['name'],
                                                    volt_value= 0,
                                                    ampe_value= 0,
                                                    run_time=self.runtimecurrent[i],
                                                    machineStatus = 0,
                                                    machine_energy_cs_value= 0,
                                                    wire_speed_value= 0,
                                                    wire_cs_value= 0,
                                                    gas_amount_value= 0
                                                    )
                        
                except:
                    self.__influx_handle.write_sample(machine_name= p['name'],
                                                    volt_value= 0,
                                                    ampe_value= 0,
                                                    run_time=self.runtimecurrent[i],
                                                    machineStatus = 0,
                                                    machine_energy_cs_value= 0,
                                                    wire_speed_value= 0,
                                                    wire_cs_value= 0,
                                                    gas_amount_value= 0
                                                    )
                    
                i = i + 1 #TestGithub

