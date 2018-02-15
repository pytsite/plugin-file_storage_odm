"""PytSite ODM File Storage Controllers
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from os import path as _path, makedirs as _makedirs
from math import floor as _floor
from PIL import Image as _Image
from pytsite import reg as _reg, router as _router, routing as _routing
from plugins import file as _file
from . import _model, _api


class Image(_routing.Controller):
    """Download image file
    """

    def exec(self):

        requested_width = int(self.arg('width'))
        requested_height = int(self.arg('height'))
        p1 = self.arg('p1')
        p2 = self.arg('p2')
        filename = self.arg('filename')
        uid = 'file_image:' + _path.splitext(filename)[0]

        try:
            img_file = _file.get(uid)  # type: _model.ImageFile
        except _file.error.FileNotFound as e:
            raise self.not_found(str(e))

        # Align side lengths and redirect
        aligned_width = _api.align_image_side(requested_width, _api.get_image_resize_limit_width())
        aligned_height = _api.align_image_side(requested_height, _api.get_image_resize_limit_height())
        if aligned_width != requested_width or aligned_height != requested_height:
            redirect = _router.rule_url('file_storage_odm@image', {
                'width': aligned_width,
                'height': aligned_height,
                'p1': p1,
                'p2': p2,
                'filename': filename,
            })
            return self.redirect(redirect, 301)

        # Original size
        orig_width = img_file.width
        orig_height = img_file.height
        orig_ratio = orig_width / orig_height

        need_resize = True

        # Calculate new size
        if not requested_width and not requested_height:
            # No resize needed, return original image
            resize_width = orig_width
            resize_height = orig_height
            need_resize = False
        elif requested_width and not requested_height:
            # Resize by width, preserve aspect ration
            resize_width = requested_width
            resize_height = _floor(requested_width / orig_ratio)
        elif requested_height and not requested_width:
            # Resize by height, preserve aspect ration
            resize_width = _floor(requested_height * orig_ratio)
            resize_height = requested_height
        else:
            # Exact resizing
            resize_width = requested_width
            resize_height = requested_height

        # Checking source file
        source_local_path = img_file.get_field('local_path')
        if not _path.exists(source_local_path):
            return self.redirect('http://placehold.it/{}x{}'.format(requested_width, requested_height))

        # Calculating target file location
        target_local_path = _path.join(_reg.get('paths.static'), 'image', 'resize', str(requested_width),
                                       str(requested_height), p1, p2, filename)

        # Create target directory
        target_dir = _path.dirname(target_local_path)
        if not _path.exists(target_dir):
            _makedirs(target_dir, 0o755, True)

        if not _path.exists(target_local_path):
            # Open source image
            img = _Image.open(source_local_path)  # type: _Image

            # Resize
            if need_resize:
                # Crop
                crop_ratio = resize_width / resize_height
                crop_width = orig_width
                crop_height = _floor(crop_width / crop_ratio)
                crop_top = _floor(orig_height / 2) - _floor(crop_height / 2)
                crop_left = 0
                if crop_height > orig_height:
                    crop_height = orig_height
                    crop_width = _floor(crop_height * crop_ratio)
                    crop_top = 0
                    crop_left = _floor(orig_width / 2) - _floor(crop_width / 2)
                crop_right = crop_left + crop_width
                crop_bottom = crop_top + crop_height

                cropped = img.crop((crop_left, crop_top, crop_right, crop_bottom))
                img.close()

                # Resize
                img = cropped.resize((resize_width, resize_height), _Image.BILINEAR)

            img.save(target_local_path)
            img.close()

        return self.redirect(img_file.get_url(width=requested_width, height=requested_height))
