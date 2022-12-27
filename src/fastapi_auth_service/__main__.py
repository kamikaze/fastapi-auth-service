import uvicorn

from fastapi_auth_service.api.http import app
from fastapi_auth_service.conf import settings
from fastapi_auth_service.extmod import c_fib

print(f'{c_fib(10)=}')
uvicorn.run(app, host=settings.service_addr, port=settings.service_port)
