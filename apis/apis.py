from apis.api_base import ApiBase
from apis.response_format import ResponseFomat
from database import sqlite_handle


class AddConfig(ApiBase):
    """
        Thông tin sau khi thùng carton đi qua DWS
    """
    urls = ("/config/add",)

    def __init__(self) -> None:
        self.__sqlite_handle = sqlite_handle
        return super().__init__()

    @ApiBase.exception_error
    def post(self):
        """
            API_ADD_CONFIG = [ 
                "id" , "name" , "volt_regs" , "ampe_regs" , "resolution" , "ampe_max" , "ampe_min" , "volt_max" , "volt_min"
            ]
        """
        args = ResponseFomat.API_ADD_CONFIG
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
            return ApiBase.createResponseMessage({}, msg)
        return ApiBase.createConflict(msg)
        

class DeleteConfig(ApiBase):
    """
        Thông tin sau khi thùng carton đi qua DWS
    """
    urls = ("/config/delete",)

    def __init__(self) -> None:
        self.__sqlite_handle = sqlite_handle
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
            return ApiBase.createResponseMessage({}, f"Xóa thành công {result} cài đặt")
        return ApiBase.createNotImplement()
    

class EditConfig(ApiBase):
    """
        Thông tin sau khi thùng carton đi qua DWS
    """
    urls = ("/config/edit",)

    def __init__(self) -> None:
        self.__sqlite_handle = sqlite_handle
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
            return ApiBase.createResponseMessage({}, msg)
        return ApiBase.createConflict(msg)


class GetAllConfig(ApiBase):
    """
        [ 
            "id" , "name" , "volt_regs" , "ampe_regs" , "resolution" , "ampe_max" , "ampe_min" , "volt_max" , "volt_min"
        ]
    """
    urls = ("/config/getall",)

    def __init__(self) -> None:
        self.__sqlite_handle = sqlite_handle
        return super().__init__()

    @ApiBase.exception_error
    def get(self):
        """
        """
        datas = self.jsonParser([], [])
        results = self.__sqlite_handle.get_all()
        for result in results:
            datas[f'{result['name']}'] = result
        return ApiBase.createResponseMessage(datas)
    
