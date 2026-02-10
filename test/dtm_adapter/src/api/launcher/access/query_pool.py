# -*- coding: utf-8 -*-
# !/usr/bin/env python


def select_service_module_query(svc_pkg_id: str):
    query_string = f"""
        SELECT svc_pkg_id
            , url_prefix 
            , module_nm
            , class_nm
            , svc_url
            , svc_typ_cd
        FROM marketstore.svc_pkg_info
        WHERE 1=1
            AND use_yn = 'Y'
    """
    if svc_pkg_id is None:
        query_string += f"\nAND inst_yn = 'Y'"
    else:
        query_string += f"\nAND svc_pkg_id = '{svc_pkg_id}'"

    return query_string


def insert_svc_func_info_query(svc_pkg_id, api_route_path: str, route_path, method: str, func_modul_nm, perm_id):
    query_string = f"""
            INSERT INTO marketstore.svc_func_info 
                    ( svc_pkg_id
                    , svc_url
                    , method
                    , func_nm
                    , route_path
                    , perm_id
                    , inst_yn
                    , use_yn
                    , create_dt
                    , create_usr_id
                    , update_dt
                    , update_usr_id) 
            VALUES 
                    ( '{svc_pkg_id}'
                    , '{api_route_path}'
                    , '{method}'
                    , '{func_modul_nm}'
                    , '{route_path}'
                    , '{perm_id}'
                    , 'Y'
                    , 'Y'
                    , CURRENT_TIMESTAMP()
                    , 'SYSTEM'
                    , CURRENT_TIMESTAMP()
                    , 'SYSTEM')
            ON DUPLICATE KEY UPDATE
                      perm_id = '{perm_id}'
                    , inst_yn = 'Y'  
                    , use_yn = 'Y'
                    , update_dt = CURRENT_TIMESTAMP()
                    , update_usr_id = 'SYSTEM'

        """
    return query_string


def delete_service_routers_query(svc_pkg_id: str):
    query_string = f"""
        UPDATE marketstore.svc_func_info
        SET inst_yn = 'N'
          , use_yn = 'N'
          , update_dt = CURRENT_TIMESTAMP()
          , update_usr_id = 'SYSTEM'
        WHERE svc_pkg_id = '{svc_pkg_id}'
    """

    return query_string


def get_service_routers_query(svc_pkg_id: str):
    query_string = f"""
        SELECT    svc_pkg_id
                , svc_url
                , method
        FROM      marketstore.svc_func_info
        WHERE     svc_pkg_id = '{svc_pkg_id}'
    """
    return query_string


def insert_perm_info_query(perm_id, perm_nm, perm_desc, perm_pkg_nm):
    query_string = f"""
            INSERT INTO marketstore.perm_info 
                    ( perm_id
                    , perm_nm
                    , perm_desc
                    , perm_pkg_nm
                    , use_yn
                    , create_dt
                    , create_usr_id
                    , update_dt
                    , update_usr_id)
            VALUES 
                    ( '{perm_id}'
                    , '{perm_nm}'
                    , '{perm_desc}'
                    , '{perm_pkg_nm}'
                    , 'Y'
                    , NOW()
                    , 'SYSTEM'
                    , NOW()
                    , 'SYSTEM')
            ON DUPLICATE KEY UPDATE
                      perm_nm = '{perm_nm}'
                    , perm_desc = '{perm_desc}'
                    , perm_pkg_nm = '{perm_pkg_nm}'
                    , use_yn = 'Y'
                    , update_dt = NOW()
                    , update_usr_id = 'SYSTEM'

        """
    return query_string


def add_perm_func_map_query(api_route_path, path, method, name, perm_id):
    query_string = f"""
            INSERT INTO marketstore.perm_func_map 
                    ( perm_id
                    , svc_url
                    , method
                    , create_dt
                    , create_usr_id
                    , update_dt
                    , update_usr_id)
            VALUES 
                    ( '{perm_id}'
                    , '{api_route_path}'
                    , '{method}'
                    , NOW()
                    , 'SYSTEM'
                    , NOW()
                    , 'SYSTEM')
            ON DUPLICATE KEY UPDATE
                      update_dt = NOW()
                    , update_usr_id = 'SYSTEM'

        """
    return query_string


def get_perm_id_from_perm_func_map(api_route_path, method):
    query_string = f"""
            SELECT perm_id
              FROM marketstore.perm_func_map
             WHERE 1=1 
               AND svc_url = '{api_route_path}'
               AND method = '{method}'
        """
    return query_string
