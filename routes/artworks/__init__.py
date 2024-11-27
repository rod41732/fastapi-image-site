from . import apis, gallery_apis, upload_apis
from .router import router

gallery_apis.mount_apis(router)
upload_apis.mount_apis(router)
apis.mount_apis(router)
