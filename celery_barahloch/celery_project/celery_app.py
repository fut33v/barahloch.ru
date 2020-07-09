from __future__ import absolute_import, unicode_literals
from celery import Celery
from .tasks_logic import BarahlochTasksLogic

# app = Celery('celery_project', broker='redis://localhost', include=['celery_project.tasks'])
app = Celery('celery_barahloch.celery_project', include=['celery_barahloch.celery_project.tasks'])

BarahlochTasksLogic.init('barahlochannel.json')

if __name__ == '__main__':
    app.start()
