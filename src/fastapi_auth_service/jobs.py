import argparse
import asyncio
import logging.config

from fastapi_auth_service.conf import settings
from fastapi_auth_service.db import async_session_maker
from fastapi_auth_service.db.helpers import bootstrap_user

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': settings.logging_format,
        },
    },
    'handlers': {
        'default': {
            'level': settings.logging_level,
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': settings.logging_level,
            'propagate': True,
        }
    }
})

logger = logging.getLogger(__name__)


def get_parsed_args():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--job', type=str)

    args, args_other = parser.parse_known_args()

    return args


async def _bootstrap_user():
    async with async_session_maker() as session:
        await bootstrap_user(session, settings)


async def main():
    args = get_parsed_args()
    job_mapping = {
        'bootstrap_user': _bootstrap_user,
    }

    try:
        await job_mapping[args.job]()
    except KeyError:
        logger.error(f'Unknown job: "{args.job}"')


if __name__ == '__main__':
    asyncio.run(main())
