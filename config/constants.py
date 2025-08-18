from utils.pattern import Singleton

class InfluxConfig(metaclass = Singleton):
    VOLT_POINT          = 'volt_value'
    AMPE_POINT          = 'ampe_value'
    MACHINE_NAME_TAG    = 'machine_name'
    VOLT_FEILD          = 'voltage'
    AMPE_FEILD          = 'ampere'

class WeldingConfig(metaclass = Singleton):
    AMPE_MIN = 10
    VOLT_MIN = 5
    RESOLUTION_AMPE_MIN = 65
    RESOLUTION_VOLT_MIN = 65