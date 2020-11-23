from flask import  Blueprint

# 创建蓝图对象
api = Blueprint("api",__name__)

# 导入蓝图视图
from . import demo,verify_code