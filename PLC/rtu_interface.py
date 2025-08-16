from pymodbus.client.sync import ModbusSerialClient
from utils.pattern import Singleton
from utils.logger import Logger
import threading
import time

class RtuInterface(metaclass=Singleton):
    def __init__(self, *args, **kwargs) -> None:
        """
        Initializes the connection parameters for the PLC station.

        Args:
            host: IP address of the PLC (default: "127.0.0.1")
            port: Modbus TCP port (default: 502)
            timeout: Timeout for Modbus operations (default: 1 second)
            unit: Modbus slave ID (default: 1)
        """

        self.__port = kwargs.get('port', "COM20")
        self.__baudrate = kwargs.get('baudrate', 9600)
        self.__bytesize = kwargs.get('bytesize', 8)
        self.__parity = kwargs.get('parity', "N")
        self.__stopbits = kwargs.get('stopbits', 1)
        self.__timeout = kwargs.get('timeout', 1.0)


        self.__lock = threading.Lock()

        self.__connected = False
        self.__client: ModbusSerialClient = None
        self.__error_count = 0
        self.__max_backoff = 60  # Giới hạn thời gian backoff tối đa là 60 giây
        self.__min_backoff = 0.5  # Thời gian chờ tối thiểu là 0.1 giây
        self.__backoff_time = self.__min_backoff
        self.__connect()
    

    def __connect(self):
        try:
            self.__client = ModbusSerialClient(
                method = 'rtu',
                port = self.__port,
                baudrate = self.__baudrate,
                timeout = self.__timeout,
                bytesize = self.__bytesize,
                stopbits = self.__stopbits,
                parity = self.__parity
            )
            if self.__client.connect():
                self.__connected = True
                self.__error_count = 0  # Reset số lỗi
                self.__backoff_time = self.__min_backoff  # Reset thời gian backoff

                Logger().info(f"Successfully connected to PLC at {self.__port}")
            else:
                Logger().error("Failed to connect to PLC")
                self.__handle_connection_error()
        except Exception as e:
            Logger().error("Failed to connect to PLC")
            self.__handle_connection_error(e)


    def __handle_connection_error(self, error= "Error modbus"):
        self.__connected = False
        self.__error_count += 1
        Logger().debug(f"Error: {error}, Error count: {self.__error_count}")

        # Tăng thời gian backoff theo cấp số nhân nhưng không vượt quá giới hạn
        self.__backoff_time = min(self.__backoff_time * 2, self.__max_backoff)
        Logger().debug(f"Backing off for {self.__backoff_time} seconds before retrying.")
        time.sleep(self.__backoff_time)


    def read_datas(self, address: int, num_register: int, slave_id: int) -> list:
        """
            0x01: Read Coils
            0x03: Read Holding Registers
            0x05: Write Single Coil
            0x06: Write Single Register
            0x10: Write Multiple Registers
            0x81: Illegal Function
            0x82: Illegal Data Address
            0x83: Illegal Data Value
            0x84: Slave Device Failure
        """
        
        if self.__connected:
            with self.__lock:
                try:
                    data = self.__client.read_holding_registers(address= address, count = num_register, unit= slave_id)
                    if hasattr(data, 'registers'):
                        return data.registers
                except Exception as e:
                    self.__connected = False
                    Logger().error(f"Error reading from PLC: {e}")
        else:
            self.__connect()
        return [None]
    

    def write_datas(self, address: int, values: list[int], slave_id: int) -> bool:
        """
            0x01: Read Coils
            0x03: Read Holding Registers
            0x05: Write Single Coil
            0x06: Write Single Register
            0x10: Write Multiple Registers
            0x81: Illegal Function
            0x82: Illegal Data Address
            0x83: Illegal Data Value
            0x84: Slave Device Failure
        """
        if self.__connected:
            with self.__lock:
                try:
                    res = self.__client.write_registers(address = address, values = values, unit = slave_id)
                    if res.function_code < 0x80:  # check if the result is not an error
                        return True
                except Exception as e:
                    self.__connected = False
                    Logger().error(f"Error sending from PLC: {e}")
        else:
            self.__connect()
        return False

    def close(self):
        self.__client.close()
        self.__connected = False
