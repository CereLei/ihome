from celery import Celery
from ihome.utils.SendMessage import CCP

# 定义celery对象
celery_app = Celery("ihome",broker="redis://127.0.0.1:6379/1")

@celery_app.task
def send_sms(tid, mobile, datas):
    """发送短信的异步任务"""
    ccp = CCP()
    ccp.send_message(tid, mobile, datas)

# celery开启的命令
# celery -A ihome.tasks.task_sms worker -l info
