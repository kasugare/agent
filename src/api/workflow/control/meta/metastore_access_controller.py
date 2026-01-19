from common.conf_system import getAccessPoolType
from api.workflow.access.data.cached_metastore_access import CachedMetastoreAccess
from api.workflow.access.meta.remote_cached_metastore_access import RemoteCachedMetastoreAccess


class MetastoreAccessController:
    def __init__(self, logger, wf_id, ses_id, req_id):
        self._logger = logger
        self._access_type = str(getAccessPoolType()).lower()

        self._wf_id = wf_id
        self._ses_id = ses_id
        self._req_id = req_id


    def get_meta_access_instance(self):
        if self._access_type == 'local':
            return CachedMetastoreAccess(self._logger, self._wf_id, self._ses_id, self._req_id)
        elif self._access_type == 'remote':
            return RemoteCachedMetastoreAccess(self._logger, self._wf_id, self._ses_id, self._req_id)
        else:
            self._logger.error(f"Access type is None")
            return None

