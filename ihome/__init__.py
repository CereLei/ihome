from config import config_map
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flask_session import Session
from flask_wtf import CSRFProtect

import redis
import logging
from logging.handlers import RotatingFileHandler
from ihome.utils.common import ReConverter


# db,redis放在外面，是为了方便其他文件导入使用
# 创建数据库
db = SQLAlchemy()

# 创建redis连接对象
redis_store = None

# 设置日志
# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG) # 调试debug级,会有info wram error
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录的格式      日志等级    输入日志信息的文件名 行数    日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日记录器
logging.getLogger().addHandler(file_log_handler)


def create_app(config_name):
    app = Flask(__name__)
    config_cls = config_map.get(config_name)
    print(config_cls)

    # 导入配置项
    app.config.from_object(config_cls)

    # 使用app初始化db，这样就可以在app创建之后初始化db
    db.init_app(app)

    # 初始化redis工具
    global redis_store
    redis_store = redis.StrictRedis(host=config_cls.REDIS_HOST,port=config_cls.REDIS_PORT,decode_responses=True)

    # 利用flask-session，将session保存到redis中
    Session(app)

    # 为flask补充csrf防控
    # CSRFProtect(app)

    # 为 flask 添加自定义的转化器
    app.url_map.converters['re'] = ReConverter

    # 注册蓝图
    from ihome import api  # 绝对路径导入
    app.register_blueprint(api.api, url_prefix="/api")

    # 提供静态资源的蓝图
    from ihome import web_html
    app.register_blueprint(web_html.html)

    # print(app.url_map)
    return app