from __future__ import absolute_import

from celery import Celery

import utils


celery = Celery('background.celery',
                backend=utils.get_celery_backend(),
                broker=utils.get_celery_broker(),
                include=['background.tasks'])

# Optional configuration, see the application user guide.
celery.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

if __name__ == '__main__':
    celery.start()
