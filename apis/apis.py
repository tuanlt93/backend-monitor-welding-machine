from apis.api_base import ApiBase
from apis.response_format import ResponseFomat
from database import sqlite_handle, influx_handle
from PLC import Plc_handle
from config.constants import InfluxConfig, WeldingConfig, StatusMachine


class CreateConfig(ApiBase):
    """
        Thông tin sau khi thùng carton đi qua DWS
    """
    urls = ("/config/create",)

    def __init__(self) -> None:
        self.__sqlite_handle = sqlite_handle
        self.__Plc_handle = Plc_handle
        return super().__init__()

    @ApiBase.exception_error
    def post(self):
        """
            API_CREATE_CONFIG = [ 
                "id" , "name" , "volt_regs" , "ampe_regs" , "resolution" , "ampe_max" , "ampe_min" , "volt_max" , "volt_min"
            ]
        """
        args = ResponseFomat.API_CREATE_CONFIG
        data = self.jsonParser(args, args)
        result, msg = self.__sqlite_handle.add(id= data['id'],
                                            name= data['name'],
                                            volt_regs= data['volt_regs'],
                                            ampe_regs= data['ampe_regs'],
                                            resolution= data['resolution'],
                                            ampe_max= data['ampe_max'],
                                            ampe_min= data['ampe_min'],
                                            volt_max= data['volt_max'],
                                            volt_min= data['volt_min']
                                            )
        if result:
            self.__Plc_handle.get_plan()
            return ApiBase.createResponseMessage({}, msg)
        return ApiBase.createConflict(msg)
        

class DeleteConfig(ApiBase):
    """
        Thông tin sau khi thùng carton đi qua DWS
    """
    urls = ("/config/delete",)

    def __init__(self) -> None:
        self.__sqlite_handle = sqlite_handle
        self.__Plc_handle = Plc_handle
        return super().__init__()

    @ApiBase.exception_error
    def post(self):
        """
            API_DELETE_CONFIG = [ 
                "id"
            ]
        """
        args = ResponseFomat.API_DELETE_CONFIG
        data = self.jsonParser(args, args)
        result = self.__sqlite_handle.delete_by_id(id= data['id'])
        if result > 0:
            self.__Plc_handle.get_plan()
            return ApiBase.createResponseMessage({}, f"Xóa thành công {result} cài đặt")
        return ApiBase.createNotImplement()
    

class EditConfig(ApiBase):
    """
        Thông tin sau khi thùng carton đi qua DWS
    """
    urls = ("/config/edit",)

    def __init__(self) -> None:
        self.__sqlite_handle = sqlite_handle
        self.__Plc_handle = Plc_handle
        return super().__init__()

    @ApiBase.exception_error
    def post(self):
        """
            API_EDIT_CONFIG = [ 
                "id" , "name" , "volt_regs" , "ampe_regs" , "resolution" , "ampe_max" , "ampe_min" , "volt_max" , "volt_min"
            ]
        """
        args = ResponseFomat.API_EDIT_CONFIG
        data = self.jsonParser(args, args)
        result, msg = self.__sqlite_handle.edit_by_name(id= data['id'],
                                                    name= data['name'],
                                                    volt_regs= data['volt_regs'],
                                                    ampe_regs= data['ampe_regs'],
                                                    resolution= data['resolution'],
                                                    ampe_max= data['ampe_max'],
                                                    ampe_min= data['ampe_min'],
                                                    volt_max= data['volt_max'],
                                                    volt_min= data['volt_min']
                                                )
        if result:
            self.__Plc_handle.get_plan()
            return ApiBase.createResponseMessage({}, msg)
        return ApiBase.createConflict(msg)


class GetAllConfig(ApiBase):
    """
        "machine" :{
            "id" , "name" , "volt_regs" , "ampe_regs" , "resolution" , "ampe_max" , "ampe_min" , "volt_max" , "volt_min"
        }
    """
    urls = ("/config/getall",)

    def __init__(self) -> None:
        self.__sqlite_handle = sqlite_handle
        return super().__init__()

    @ApiBase.exception_error
    def get(self):
        resp = self.jsonParser([], [])
        results = self.__sqlite_handle.get_all()
        for result in results:
            resp[f'{result['name']}'] = result
        return ApiBase.createResponseMessage(resp)
    

class GetAllValueLatest(ApiBase):
    """
        {
            'Máy Hàn A': {'voltage': 814.53125, 'ampere': 2750.0}, 
            'Máy Hàn F': {'voltage': 4323.28125, 'ampere': 7466.25}
        }
    """
    urls = ("/monitor/latest",)

    def __init__(self) -> None:
        self.__influx_handle = influx_handle
        return super().__init__()

    @ApiBase.exception_error
    def get(self):
        resp = self.jsonParser([], [])
        volt_datas: dict = self.__influx_handle.read_latest(InfluxConfig.VOLT_POINT)
        ampe_datas: dict = self.__influx_handle.read_latest(InfluxConfig.AMPE_POINT)
        
        resp = {}

        for key, vdata in volt_datas.items():
            adata = ampe_datas.get(key)
        
            v = vdata.get("voltage")
            a = adata.get("ampere")
            id = vdata.get("id")

            if v is None or a is None:
                resp[key] = {
                        'voltage': 0.0,
                        'ampere' : 0.0,
                        'id'     : id,
                        'status' : StatusMachine.DISCONNECT
                    }
                continue

            if v < WeldingConfig.VOLT_MIN and a < WeldingConfig.AMPE_MIN:
                resp[key] = {
                        'voltage': 0.0,
                        'ampere' : 0.0,
                        'id'     : id,
                        'status' : StatusMachine.IDEL
                    }
            else:
                resp[key] = {
                    'voltage': v,
                    'ampere' : a,
                    'id'     : id,
                    'status' : StatusMachine.RUNNING
                }


        return ApiBase.createResponseMessage(resp)
    

class GetInfoMinitor(ApiBase):
    """
        {
        "id" , "name" , "volt_regs" , "ampe_regs" , "resolution" , "ampe_max" , "ampe_min" , "volt_max" , "volt_min"
        }
    """
    urls = ("/monitor/getinfo",)

    def __init__(self) -> None:
        self.__sqlite_handle = sqlite_handle
        return super().__init__()

    @ApiBase.exception_error
    def post(self):
        args = ResponseFomat.API_POST_INFO
        msg = self.jsonParser(args, args)
        result = self.__sqlite_handle.get_by_id(msg)
        
        if result:
            return ApiBase.createResponseMessage(result)
        
        return ApiBase.createConflict("Don't find id")
    

class GetMachineData(ApiBase):
    """
        {
        "name"
        }
    """
    urls = ("/monitor/machine/data",)

    def __init__(self) -> None:
        self.__influx_handle = influx_handle
        return super().__init__()

    @ApiBase.exception_error
    def post(self):
        args = ResponseFomat.API_POST_MACHINE_DATA
        msg = self.jsonParser(args, args)

        result = self.__influx_handle.read_data_today(msg['name'])
        if result:
            return ApiBase.createResponseMessage(result)
        return ApiBase.createConflict("Don't find name")
        
    
