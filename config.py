import redis
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

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    pass


config_map ={
    "develop": DevelopmentConfig,
    "product":ProductionConfig
}