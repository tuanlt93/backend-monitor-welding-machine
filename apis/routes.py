"""
TODO: Import active url resources here
"""
from apis.api_base import api
from apis.apis import AddConfig, DeleteConfig, GetAllConfig, EditConfig, GetAllValueLatest


api.addClassResource(AddConfig)
api.addClassResource(DeleteConfig)
api.addClassResource(EditConfig)
api.addClassResource(GetAllConfig)
api.addClassResource(GetAllValueLatest)
