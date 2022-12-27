import uvicorn

from fastapi_auth_service.api.http import app
from fastapi_auth_service.conf import settings

uvicorn.run(app, host=settings.service_addr, port=settings.service_port)
