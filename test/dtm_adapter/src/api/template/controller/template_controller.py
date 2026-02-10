#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

from ailand.dao.aidao import Controller

from api.template.access.template_access import TemplateAccess

from utility.gen_id import gen_id
from utility.context import current_user


class TemplateController(Controller):
    def __init__(self, logger, db_conn):
        super().__init__(logger, db_conn)
        self._template_access = TemplateAccess(logger, db_conn)

    def get_template(self, tpl_id):
        template = self._template_access.get_template(tpl_id)
        return template

    def get_templates(self,):
        templates = self._template_access.get_templates()
        return templates

    def delete_template(self, tpl_id, usr_id):
        delete_template = self._template_access.delete_template(tpl_id=tpl_id, usr_id=usr_id)
        return delete_template

    def get_deploy_type_code(self,):
        codes = self._template_access.get_deploy_type_code()
        return codes

    def get_template_type_code(self,):
        codes = self._template_access.get_template_type_code()
        return codes

    def create_template(self, dply_typ_cd, tpl_typ_cd, params, mnfst, usr_id):
        tpl_uuid = gen_id()
        self._template_access.create_template(tpl_id=tpl_uuid,create_usr_id=usr_id,
                                              update_usr_id=usr_id, dply_typ_cd=dply_typ_cd,
                                              tpl_typ_cd=tpl_typ_cd, mnfst=json.dumps(mnfst, ensure_ascii=False).replace("'", "''"), params=json.dumps(params, ensure_ascii=False).replace("'", "''"))
        return tpl_uuid
