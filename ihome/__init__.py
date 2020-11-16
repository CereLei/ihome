from config import config_map
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import redis
from flask_session import Session
from flask_wtf import CSRFProtect

# db,redis放在外面，是为了方便其他文件导入使用
# 创建数据库
db = SQLAlchemy()

# 创建redis连接对象
redis_store = None

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
    redis_store = redis.StrictRedis(host=config_cls.REDIS_HOST,port=config_cls.REDIS_PORT)

    # 利用flask-session，将session保存到redis中
    Session(app)

    # 为flask补充csrf防控
    CSRFProtect(app)

    return app