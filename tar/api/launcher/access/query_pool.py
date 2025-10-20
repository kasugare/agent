# -*- coding: utf-8 -*-
#!/usr/bin/env python


def select_init_service_module_query():
    query_string = f"""
        SELECT url_prefix as prefix 
            , module_nm as module_name
            , class_nm as class_name
        FROM svc_pkg_info
        WHERE 1=1
            AND inst_yn = 'Y'
            AND use_yn = 'Y'
    """
    return query_string