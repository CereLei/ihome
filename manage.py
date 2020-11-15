# 最基本的文件
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import redis
from flask_session import Session
from flask_wtf import CSRFProtect
app = Flask(__name__)

class Config(object):
    """配置文件"""
    DEBUG = True # DEBUGGER
    SECRET_KEY = "dfadfDFS123#1"

    # 数据库
    SQLALCHEMY_DATABASE_URI = "mysql://root:123456@127.0.0.1:3306/ihome"
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # redis
    REDIS_HOST='127.0.0.1'
    REDIS_PORT = 6379

    # flask-session
    SESSION_TYPE = 'redis' # session存哪里
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
    SESSION_USE_SIGNER = True # 对cookie的sessionID进行隐藏
    # SESSION_PERMANENT = # session的数据是否永久有效
    PERMANENT_SESSION_LIFETIME = 86400 # session的有效期，单位秒

# 导入配置项
app.config.from_object(Config)

# 创建数据库
db = SQLAlchemy(app)

# 创建redis连接对象
redis_store = redis.StrictRedis(host=Config.REDIS_HOST,port=Config.REDIS_PORT)

# 利用flask-session，将session保存到redis中
Session(app)

# 为flask补充csrf防控
CSRFProtect(app)

@app.route('/index')
def index():
    print('1')
    return 'imde page'

if __name__ == '__main__':
    app.run()