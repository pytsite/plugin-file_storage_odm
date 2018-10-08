"""PytSite File Storage ODM Plugin Events Handlers
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from os import path as _path
from pytsite import util as _util, reg as _reg, logger as _logger


def pytsite_cleanup():
    root = _path.join(_reg.get('paths.static'), 'image', 'resize')
    ttl = _reg.get('file_storage_odm.static_ttl', 2592000)  # 1 month

    success, failed = _util.cleanup_files(root, ttl)

    for f_path in success:
        _logger.debug('Obsolete static file removed: {}'.format(f_path))

    for f_path, e in failed:
        _logger.error('Error while removing obsolete static file {}: {}'.format(f_path, e))
