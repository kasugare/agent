#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import traceback
from pathlib import Path

import certifi
import urllib3
from ailand.dao.aidao import Service
from fastapi.routing import APIRoute, APIRouter

from api.launcher.controller.launcher_controller import LauncherController


class ServiceLauncher(Service):
    def __init__(self, app, logger, db_conn):
        super().__init__(logger, db_conn)
        self.pkg_dir = str(Path(__file__).resolve().parent.parent)
        self._app = app
        self._logger = logger
        self._db_conn = db_conn
        self._launcher_ctl = LauncherController(logger, self._db_conn)

    def _gen_api_route_path(self, prefix, path):
        path_list = prefix.split("/") + path.split("/")
        api_route_path = "/%s" % ("/".join([path for path in path_list if path]))
        return api_route_path

    def _is_dup_api_router(self, api_route_path):
        for route in self._app.routes:
            if isinstance(route, APIRoute):
                if route.path == api_route_path:
                    return True
                else:
                    continue
        return False

    # def load_init_service(self):
    #     try:
    #         service_module_map_list = self._launcher_ctl.get_init_service_meta()
    #         self._logger.info(f"service_module_map_list={service_module_map_list}")
    #         for service_module_map in service_module_map_list:
    #             self.add_api_service(**service_module_map)
    #     except Exception as e:
    #         traceback.print_exc()

    def load_service_package(self, svc_pkg_id: str = None):
        destination_path = None
        try:
            service_module_map_list = self._launcher_ctl.get_service_meta(svc_pkg_id)
            self._logger.info(f"service_module_map_list={service_module_map_list}")

            for service_module_map in service_module_map_list:
                svc_url = service_module_map['svc_url']
                svc_typ_cd = service_module_map['svc_typ_cd']
                if svc_typ_cd == "ZIP":
                    destination_path = self._download_service_package(svc_url, self.pkg_dir)
                try:
                    self.add_api_service(destination_path, **service_module_map)
                except ModuleNotFoundError as mnfe:
                    self._logger.error(mnfe)
                    pass
        except Exception as e:
            traceback.print_exc()
            raise e

    def add_api_service(self, destination_path, svc_pkg_id, url_prefix, module_nm, class_nm, svc_url, svc_typ_cd):
        if svc_typ_cd == 'ZIP':
            self._logger.info("Add ZIP type service package")
            self._logger.info(f"svc_pkg_id={svc_pkg_id}, module_name = {module_nm}, class_name={class_nm}, destination_path={destination_path}")
            sys.path.insert(0, destination_path)
            module = __import__(module_nm, fromlist=[module_nm])
            app_object = getattr(module, class_nm)(self._logger, None)
            api_router: APIRouter = app_object.get_router()
        elif svc_typ_cd == 'SRC':
            self._logger.info("Add Source type service package")
            self._logger.info(f"svc_pkg_id={svc_pkg_id}, module_name = {module_nm}, class_name={class_nm}")
            module = __import__(module_nm, fromlist=[''])
            app_object = getattr(module, class_nm)()
            self._logger.info(dir(app_object))
            api_router: APIRouter = app_object.get_router()
        elif svc_typ_cd == 'DEF':
            self._logger.info("Add Default service package")
            self._logger.info(f"svc_pkg_id={svc_pkg_id}, module_name = {module_nm}, class_name={class_nm}")
            module = __import__(module_nm, fromlist=[''])
            app_object = getattr(module, class_nm)()
            api_router: APIRouter = app_object.get_router()
        else:
            self._logger.error("Undefined service type")
            traceback.print_exc()
            raise Exception("Undefined service type")

        self._logger.info(f"api_router.routes={api_router.routes}")

        for route in api_router.routes:
            api_route_path = self._gen_api_route_path(url_prefix, route.path)
            perm_pkg_nm = next(iter(api_router.tags))
            method = next(iter(route.methods))
            perm_id = self._launcher_ctl.get_perm_id_from_perm_func_map(api_route_path, method)
            if perm_id is None:
                perm_id = self.gen_id('ailand', 'perm_info', 'perm_id')
                self._logger.debug(f"new perm id {perm_id} has been created")
            else:
                perm_id = perm_id['perm_id']
                self._logger.debug(f"perm id {perm_id} exists")

            perm_nm = route.name
            perm_desc = api_route_path

            if route.openapi_extra is not None:
                if route.openapi_extra.get('perm_nm') is not None:
                    perm_nm = route.openapi_extra.get('perm_nm')
                if route.openapi_extra.get('perm_desc') is not None:
                    perm_desc = route.openapi_extra.get('perm_desc')

            self._launcher_ctl.add_perm_info(perm_id, perm_nm, perm_desc, perm_pkg_nm)
            self._launcher_ctl.add_svc_func_info(svc_pkg_id, api_route_path, route.path, method, route.name, perm_id)
            self._launcher_ctl.add_perm_func_map(api_route_path, route.path, method, route.name, perm_id)

            if self._is_dup_api_router(api_route_path):
                self.delete_app_router(url_prefix, route.path)

        self._app.include_router(api_router, prefix=url_prefix)

    def delete_app_router(self, prefix, path, url=None):
        del_index = []
        if url is None:
            api_route_path = self._gen_api_route_path(prefix, path)
        else:
            api_route_path = url
        for index, route in enumerate(self._app.router.routes):
            if isinstance(route, APIRoute):
                if route.path == api_route_path:
                    del_index.append(index)
        del_index.reverse()
        for index in del_index:
            self._app.router.routes.pop(index)

    def delete_service_package(self, svc_pkg_id: str):
        try:
            service_routers = self._launcher_ctl.get_service_routers(svc_pkg_id)
            self._logger.info(f"service_routers={service_routers}")
            self._launcher_ctl.delete_service_routers(svc_pkg_id)
            for router in service_routers:
                self.delete_app_router(None, None, router['svc_url'])

        except Exception as e:
            traceback.print_exc()
            raise e

    def _download_service_package(self, url, destination_folder):
        verify_ssl = False

        # # 대상 경로 생성
        # # 상대 경로를 절대 경로로 변환
        # absolute_destination_folder = os.path.join(project_root, destination_folder)
        #
        # print(f"absolute_destination_folder={absolute_destination_folder}")
        # # 대상 폴더가 존재하지 않으면 생성
        # os.makedirs(absolute_destination_folder, exist_ok=True)

        # 파일 이름 추출
        file_name = os.path.basename(url)

        # 대상 경로 생성
        destination_path = os.path.join(destination_folder, file_name)

        self._logger.info(f"destination_path={destination_path}")

        # urllib3 HTTP 클라이언트 생성
        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        http = urllib3.PoolManager(
            cert_reqs='CERT_REQUIRED' if verify_ssl else 'CERT_NONE',
            ca_certs=certifi.where() if verify_ssl else None
        )

        try:
            # 파일 다운로드
            with http.request('GET', url, preload_content=False) as response, open(destination_path, 'wb') as out_file:
                if response.status == 200:
                    # 청크 단위로 파일 쓰기
                    for chunk in response.stream(1024):
                        out_file.write(chunk)
                    self._logger.info(f"파일 '{file_name}'이(가) 성공적으로 다운로드되어 {destination_path}에 저장되었습니다.")
                else:
                    self._logger.error(f"파일 다운로드 실패. 상태 코드: {response.status}")
        except urllib3.exceptions.HTTPError as e:
            self._logger.error(f"HTTP 오류 발생: {e}")
            raise e
        except IOError as e:
            self._logger.error(f"I/O 오류 발생: {e}")
            raise e
        return destination_path
