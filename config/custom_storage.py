"""
custom_storage.py — ضعه في config/custom_storage.py
storage backend مخصص يرفع الملفات مباشرة لـ Cloudinary
يعمل مع أي إصدار من Django
"""
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from django.core.files.storage import Storage
from django.conf import settings


class CloudinaryMediaStorage(Storage):

    def __init__(self):
        cloudinary.config(
            cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
            api_key=os.getenv('CLOUDINARY_API_KEY'),
            api_secret=os.getenv('CLOUDINARY_API_SECRET'),
        )

    def _get_public_id(self, name):
        # أزل الامتداد من الاسم عشان Cloudinary يتحكم فيه
        root, _ = os.path.splitext(name)
        return f"wassel/{root}"

    def _save(self, name, content):
        public_id = self._get_public_id(name)
        result = cloudinary.uploader.upload(
            content,
            public_id=public_id,
            overwrite=True,
            resource_type="image",
        )
        # نحفظ الـ secure_url كاملاً في قاعدة البيانات
        return result['secure_url']

    def url(self, name):
        # إذا كان name هو URL كامل (من Cloudinary) أرجعه مباشرة
        if name and name.startswith('http'):
            return name
        # إذا كان مسار قديم، أرجع رابط فاشل يُظهر broken image
        return name

    def exists(self, name):
        return False  # نسمح بالرفع دائماً

    def delete(self, name):
        if name and name.startswith('http'):
            # استخرج public_id من الـ URL
            try:
                public_id = name.split('/upload/')[1]
                public_id = '/'.join(public_id.split('/')[1:])  # أزل version
                public_id = os.path.splitext(public_id)[0]
                cloudinary.uploader.destroy(public_id)
            except Exception:
                pass

    def size(self, name):
        return 0

    def path(self, name):
        raise NotImplementedError("CloudinaryMediaStorage لا يدعم path()")
