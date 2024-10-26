from .router import router
from . import gallery_apis, upload_apis, apis


gallery_apis.mount_apis(router)
upload_apis.mount_apis(router)
apis.mount_apis(router)
