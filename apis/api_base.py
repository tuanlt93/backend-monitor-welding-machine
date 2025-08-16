"""
Deploy all rest apis for the Flask application

Everytables is assumed to have ```id``` column in it
"""

# from database import *

from utils.logger import Logger

from flask_restful import Api, Resource, request, reqparse
from flask_babel import _
from flask_jwt_extended import  jwt_required, get_jwt, get_jwt_identity
from flask_jwt_extended.exceptions import RevokedTokenError
from typing import Callable
import traceback
from sqlalchemy.exc import IntegrityError, InvalidRequestError, DataError
from typing import Type

class ApiBase(Resource):
    urls = ()

    def requestParser(self, args: list, required_args: list):
        """
        Parser data from request

        Return -> Namespace (dict)
        """
        if not request.data:
            return {}
        
        parser = reqparse.RequestParser()
        for arg in args:
            if arg in required_args:
                parser.add_argument(arg, help = _('This field cannot be blank'), required = True)
            else:
                parser.add_argument(arg, required = False)
        data = parser.parse_args()
        return data
    
    @staticmethod
    def limitDict(data: dict, *args) -> dict:
        """
        Return -> dict only contain args
        """
        new_data = {}
        for arg in args:
            if arg in data:
                new_data[arg] = data[arg]
        return new_data
    
    @staticmethod
    def checkRequirement(data: dict, *args) -> list:
        """
        Check if data contains all required args

        Return -> list of missing args
        """
        missing_args = []
        for arg in args:
            if arg not in data:
                missing_args.append(arg)
        return missing_args

    def __checkJson(self, data: dict, required_args: list):
        """
        Validate Json data by required arguments,
        add messages to 'response_message'

        Returns: response_message
        """
        if type(data) != dict:
            data = {}

        response_message = []
        for arg in self.checkRequirement(data, *required_args):
            response_message.append(arg)
        return response_message


    def jsonParser(self, required_args: list = (), limit_args: list = ()):
        """
        Parse JSON data from request body and parameters.

        Returns -> (json) data, (dict) headers
        """
        # token = request.headers.get('Authorization')
        # headers = {'Authorization': token} if token else {}

        data = {**request.args.to_dict(), **(request.get_json(force=True) if request.data else {})}

        missing_args = self.checkRequirement(data, *required_args)
        assert not missing_args, (2020, [f"Không được để trống {arg}" for arg in missing_args], 409)

        return (self.limitDict(data, *limit_args) if limit_args else data)

    
    @staticmethod
    def createResponseMessage(data: object, message: str = "Succeeded", response_code: int = 200, error_code: int = 0):
        """
        Return response for rest request
        ```
        {
            "code": int(error_code, 0-no error)
            "msg": str(message)
            "response": object(data)
        }, response_code
        ```
        """
        response = ({
            'code': error_code,
            'msg': message,
            'response': data
        }, response_code)
        return response
    
    @staticmethod
    def createNotImplement():
        """
        Return "Not implemented" response for rest request
        ```
        {
            "code": 2018
            "msg": "Not implemented"
            "response": {}
        }, 501
        ```
        """
        return ApiBase.createResponseMessage(None, _("Not implemented"), 501, 2018)

    @staticmethod
    def createNoAuthority():
        """
        Return "No authority" response for rest request
        ```
        {
            "code": 2021
            "msg": "No authority"
            "response": {}
        }, 401
        ```
        """
        return ApiBase.createResponseMessage(None, _("No authority"), 401, 2021)

    @staticmethod
    def createConflict(msg: str):
        """
        Return "Data conflict" response for rest request
        ```
        {
            "code": 2022
            "msg": (str) description
            "response": {}
        }, 409
        ```
        """
        return ApiBase.createResponseMessage(None, msg, 409, 2022)

    @staticmethod
    def createInvalid(msg: str):
        """
        Return "Request invalid" response for rest request
        ```
        {
            "code": 2023
            "msg": (str) description
            "response": {}
        }, 409
        ```
        """
        return ApiBase.createResponseMessage(None, msg, 409, 2023)

    @staticmethod
    def createServerFailure(msg: str):
        """
        Return "Server failure" response for rest request
        ```
        {
            "code": 2024
            "msg": (str) description
            "response": {}
        }, 500
        ```
        """
        return ApiBase.createResponseMessage(None, msg, 500, 2024)

    # @classmethod
    # def exception_error(cls, func):
    #     """
    #         DECORATOR FOR TRY AND EXCEPTION ERROR
    #     """
    #     def inner(cls):
    #         msg = _("An error occurred")
    #         code = 2019
    #         res_code = 503
    #         try:
    #             return func(cls)
    #         except AssertionError as e:
    #             code, msg, res_code = eval(str(e))
    #         except IntegrityError as e:
    #             code, msg = e.orig.args
    #         except DataError as e:
    #             code, msg = e.orig.args
    #         except InvalidRequestError as e:
    #             msg = str(e)
    #         except RevokedTokenError as e:
    #             msg = str(e)
    #         except Exception as e:
    #             msg += f": {e}"
            
    #         # Logger().error(msg)
    #         # Ghi lại toàn bộ thông tin lỗi bao gồm traceback
    #         full_error_msg = f"{msg}\nTraceback:\n{traceback.format_exc()}"
    #         Logger().error(full_error_msg)  # Ghi lại thông điệp lỗi đầy đủ
            
    #         return ApiBase.createResponseMessage({}, msg, res_code, code)
            
    #     return inner
    

    @classmethod
    def exception_error(cls, func):
        """
            DECORATOR FOR TRY AND EXCEPTION ERROR
        """
        def inner(cls):
            msg = _("An error occurred")
            code = 2019
            res_code = 503
            try:
                return func(cls)
            except AssertionError as e:
                code, msg, res_code = eval(str(e))
            except IntegrityError as e:
                code, msg = e.orig.args
            except DataError as e:
                code, msg = e.orig.args
            except InvalidRequestError as e:
                msg = str(e)
            except RevokedTokenError as e:
                msg = str(e)
            except Exception as e:
                # Ghi lại thông báo lỗi và traceback
                msg = f"{msg}: {str(e)}"
                full_error_msg = f"{msg}\n{traceback.format_exc()}"
                Logger().error(full_error_msg)  # Ghi lại thông điệp lỗi đầy đủ
                return ApiBase.createResponseMessage({}, msg, res_code, code)

        return inner



class ApiFeConfigure(ApiBase):
    """
    Base API for configuring FE UI

    Implement:
    * GET: getFilter, getPost, getPatch, getTable, getExcel
    * POST: setFilter, setPost, setPatch, setTable
    """
    def getFilter(self):
        """
        Get config of filter UI
        """
        return _("Not implemented")

    def getPost(self):
        """
        Get config of add new UI
        """
        return _("Not implemented")

    def getPatch(self):
        """
        Get config of update UI
        """
        return _("Not implemented")

    def getTable(self):
        """
        Get config of table UI
        """
        return _("Not implemented")

    def getExcel(self):
        """
        Get all tables in a excel file
        """
        return _("Not implemented")

    def setFilter(self):
        """
        Set filter UI config
        """
        return _("Not implemented")

    def setPost(self):
        """
        Set add new UI config
        """
        return _("Not implemented")

    def setPatch(self):
        """
        Set update UI config
        """
        return _("Not implemented")

    def setTable(self):
        """
        Set table UI config
        """
        return _("Not implemented")

    def get(self):
        """
        Redirect to other get functions
        """
        if '/filter' in request.path:
            data =  self.getFilter()
        elif '/post' in request.path:
            data =  self.getPost()
        elif '/patch' in request.path:
            data =  self.getPatch()
        elif '/table' in request.path: 
            data =  self.getTable()
        elif '/export' in request.path: 
            data =  self.getExcel()
        else:
            return ApiBase.createResponseMessage(_("Wrong path '{request.path}'"), 404)
        return data

    def post(self):
        """
        Redirect to other set functions
        """
        response_code = 200
        if '/filter' in request.path:
            response_message = self.setFilter()
        elif '/post' in request.path:
            response_message = self.setPost()
        elif '/patch' in request.path:
            response_message = self.setPatch()
        elif '/table' in request.path:
            response_message = self.setTable()
        else:
            response_message = _(f"Wrong path '{request.path}'")
            response_code = 404
        return ApiBase.createResponseMessage(response_message, response_code)




class CustomApi(Api):
    def addClassResource(self, api_class: Type["ApiBase"]):
        self.add_resource(api_class, *api_class.urls)

api = CustomApi()

from apis.routes import *
