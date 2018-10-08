"""PytSite ODM File Storage.
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

# Public API
from . import _model as model, _field as field
from ._driver import Driver


def plugin_load():
    from pytsite import router, cleanup
    from plugins import odm
    from . import _model, _controllers, _eh

    # Register ODM models
    odm.register_model('file', _model.AnyFileODMEntity)
    odm.register_model('file_image', _model.ImageFileODMEntity)

    router.handle(_controllers.Image, '/image/resize/<int:width>/<int:height>/<p1>/<p2>/<filename>',
                  'file_storage_odm@image', defaults={'width': 0, 'height': 0})

    cleanup.on_cleanup(_eh.pytsite_cleanup)
