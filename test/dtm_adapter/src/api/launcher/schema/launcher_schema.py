from pydantic import BaseModel


class ResModelOfAPIRoutes(BaseModel):
    path: str
    name: str
    methods: list[str]
    function: str


class ReqModelOfAddServicePackage(BaseModel):
    svc_pkg_id: str


class ReqModelOfDeleteServicePackage(BaseModel):
    svc_pkg_id: str
