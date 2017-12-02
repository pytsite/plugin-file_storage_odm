"""PytSite ODM File Storage.
"""
from . import _model as model, _field as field
from ._driver import Driver

__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'


def _init():
    from pytsite import router
    from plugins import odm
    from . import _model, _controllers

    # Register ODM models
    odm.register_model('file', _model.AnyFileODMEntity)
    odm.register_model('file_image', _model.ImageFileODMEntity)

    router.handle(_controllers.Image, '/image/resize/<int:width>/<int:height>/<p1>/<p2>/<filename>',
                  'file_storage_odm@image', defaults={'width': 0, 'height': 0})


_init()
