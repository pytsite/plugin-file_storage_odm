"""PytSite ODM File Storage Driver
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

import os as _os
import re as _re
import shutil as _shutil
import bson.errors as _bson_errors
from mimetypes import guess_extension as _guess_extension
from pytsite import reg as _reg, util as _util
from plugins import odm as _odm, file as _file
from . import _model

_IMG_MIME_RE = _re.compile('image/(bmp|gif|jpeg|jp2|jpx|jpm|tiff|x-icon|png)$')


def _build_store_path(name: str, mime: str, propose: str = None) -> str:
    """Build unique path to store file on the filesystem.
    """
    storage_dir = _os.path.join(_reg.get('paths.storage'), 'file', mime.split('/')[0])
    ext = _os.path.splitext(name)[1]
    rnd_str = _util.random_str

    # Possible (but not final) path
    possible_target_path = _os.path.join(storage_dir, rnd_str(2), rnd_str(2), rnd_str()) + ext

    # Check if the proposed path suits the requirements
    if propose:
        m = _re.match('(\w{2})/(\w{2})/(\w{16})(\.\w+)$', propose)
        if m:
            ext = m.group(4)
            possible_target_path = _os.path.join(storage_dir, m.group(1), m.group(2), m.group(3)) + ext

    # Search for path which doesn't exist on the filesystem
    while True:
        if not _os.path.exists(possible_target_path):
            store_path = possible_target_path
            break
        else:
            possible_target_path = _os.path.join(storage_dir, rnd_str(2), rnd_str(2), rnd_str()) + ext

    return store_path


class Driver(_file.driver.Abstract):
    def create(self, file_path: str, mime: str, name: str = None, description: str = None, propose_path: str = None,
               **kwargs) -> _file.model.AbstractFile:

        # Generate unique file path in storage
        # Determine extension from MIME
        if not _os.path.splitext(name):
            name += _guess_extension(mime)

        abs_target_path = _build_store_path(name, mime, propose_path)

        # Make sure that directory on the filesystem exists
        target_dir = _os.path.dirname(abs_target_path)
        if not _os.path.exists(target_dir):
            _os.makedirs(target_dir, 0o755, True)

        # Copy file to the storage
        _shutil.copy(file_path, abs_target_path)

        # Create ODM entity
        if _IMG_MIME_RE.search(mime):
            odm_entity = _odm.dispense('file_image')  # type: _model.ImageFileODMEntity
        else:
            odm_entity = _odm.dispense('file')  # type: _model.AnyFileODMEntity

        storage_dir = _reg.get('paths.storage')
        odm_entity.f_set('path', abs_target_path.replace(storage_dir + '/', ''))
        odm_entity.f_set('name', name)
        odm_entity.f_set('description', description)
        odm_entity.f_set('mime', mime)
        odm_entity.f_set('length', _os.path.getsize(file_path))
        odm_entity.save()

        if isinstance(odm_entity, _model.ImageFileODMEntity):
            return _model.ImageFile(odm_entity)
        elif isinstance(odm_entity, _model.AnyFileODMEntity):
            return _model.AnyFile(odm_entity)

    def get(self, uid: str) -> _file.model.AbstractFile:
        """Get file by UID
        """
        if not isinstance(uid, str):
            raise _file.error.InvalidFileUidFormat('Invalid file UID format: {}.'.format(uid))

        # This driver uses UIDs in form 'model:entity_uid'
        uid_split = uid.split(':')
        if len(uid_split) != 2 or not _odm.is_model_registered(uid_split[0]):
            raise _file.error.InvalidFileUidFormat('Invalid file UID format: {}.'.format(uid))

        # Search fo ODM entity in appropriate collection
        try:
            odm_entity = _odm.find(uid_split[0]).eq('_id', uid_split[1]).first()
        except _bson_errors.InvalidId:
            raise _file.error.FileNotFound('ODM entity is not found for file {}'.format(uid))

        if not odm_entity:
            raise _file.error.FileNotFound('ODM entity is not found for file {}'.format(uid))

        # Select corresponding file model
        if isinstance(odm_entity, _model.ImageFileODMEntity):
            return _model.ImageFile(odm_entity)
        elif isinstance(odm_entity, _model.AnyFileODMEntity):
            return _model.AnyFile(odm_entity)
        else:
            raise TypeError('Unknown file type')
