from common.conf_system import getAccessPoolType
from api.workflow.access.data.cached_io_data_access import CachedIODataAccess
from api.workflow.access.data.remote_cached_io_data_access import RemoteCachedIODataAccess

class DataIOAccessController:
    def __init__(self, logger):
        self._logger = logger
        self._access_type = str(getAccessPoolType()).lower()

    def get_data_access_instance(self):
        if self._access_type == 'local':
            return CachedIODataAccess(self._logger)
        elif self._access_type == 'remote':
            return RemoteCachedIODataAccess(self._logger)
        else:
            self._logger.error(f"Access type is None")
            return None

