# -*- coding: utf-8 -*-
#!/usr/bin/env python


def select_user_info_query():
    query_string = f"""
        SELECT usr_id
            , usr_nm
            , acnt_typ_cd
            , phon_num
            , email
            , act_yn
            , tz_cd
            , lang_cd
        FROM user_info
    """
    return query_string