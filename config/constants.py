from utils.pattern import Singleton

class InfluxConfig(metaclass = Singleton):
    VOLT_POINT          = 'volt_value'
    AMPE_POINT          = 'ampe_value'
    MACHINE_NAME_TAG    = 'machine_name'
    VOLT_FEILD          = 'voltage'
    AMPE_FEILD          = 'ampere'
    LATEST_READ_TIME    = 10
    SAMPLE_READ_TIME    = 60

class WeldingConfig(metaclass = Singleton):
    AMPE_MIN = 10
    VOLT_MIN = 5
    RESOLUTION_AMPE_MIN = 65
    RESOLUTION_VOLT_MIN = 65

class StatusMachine(metaclass = Singleton):
    DISCONNECT  = 'disconnect'
    IDEL        = 'idel'
    RUNNING     = 'running'