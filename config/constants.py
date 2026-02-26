from utils.pattern import Singleton

class InfluxConfig(metaclass = Singleton):
    VOLT_POINT          = 'volt_value'
    AMPE_POINT          = 'ampe_value'
    MACHINE_NAME_TAG    = 'machine_name'
    VOLT_FEILD          = 'voltage'
    AMPE_FEILD          = 'ampere'
    LATEST_READ_TIME    = 10
    SAMPLE_READ_TIME    = 60
    RUN_TIME_POINT      = 'RunTime_value'
    RUN_TIME_FEILD      = 'RunTime'
    MACHINE_STT_POINT   = 'machine_status_value'
    MACHINE_STT_FEILD   = 'machine_status'
    MACHINE_ENERGY_CS_POINT   = 'machine_energy_cs_value'
    MACHINE_ENERGY_CS_FEILD   = 'machine_energy_cs'
    WIRE_SPEED_POINT    = 'wire_speed_value'
    WIRE_SPEED_FEILD    = 'wire_speed'
    WIRE_CS_POINT    = 'wire_cs_value'
    WIRE_CS_FEILD    = 'wire_cs'
    GAS_AMOUNT_POINT    = 'gas_amount_value'
    GAS_AMOUNT_FEILD    = 'gas_amount_speed'



class WeldingConfig(metaclass = Singleton):
    AMPE_MIN = 10
    VOLT_MIN = 5
    RESOLUTION_AMPE_MIN = 65
    RESOLUTION_VOLT_MIN = 65

class StatusMachine(metaclass = Singleton):
    DISCONNECT  = 'disconnect'
    IDEL        = 'idel'
    RUNNING     = 'running'