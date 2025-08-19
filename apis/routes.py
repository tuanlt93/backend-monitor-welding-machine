"""
TODO: Import active url resources here
"""
from apis.api_base import api
from apis.apis import CreateConfig, DeleteConfig, GetAllConfig, \
    EditConfig, GetAllValueLatest, GetInfoMinitor, GetMachineData


api.addClassResource(CreateConfig)
api.addClassResource(DeleteConfig)
api.addClassResource(EditConfig)
api.addClassResource(GetAllConfig)
api.addClassResource(GetAllValueLatest)
api.addClassResource(GetInfoMinitor)
api.addClassResource(GetMachineData)
