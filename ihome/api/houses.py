
from . import api
from ihome.models import Area,User
from flask import jsonify,current_app
from ihome.utils.response_code import RET
from ihome import redis_store,constants
import json
@api.route("/areas")
def get_area_info():
    """获取区域"""
    # 区域数据很多地方获取，如果每次直接查数据库(磁盘数据库)，效率会慢，常常使用缓存
    # 缓存2种方法，第一种放在全局变量里缓存，第二个数据多就存在内存数据库redis中

    #从rendis中获取数据，如果有就获取数据，如果没有就从mysql查数据，查到之后保存redis中，返回前端

    try:
        resp_json = redis_store.get("area_info")
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json is not None:
            # redis 有缓存数据
            current_app.logger.info("hit redis area_info")
            return resp_json, 200, {"Content-Type": "application/json"}

    # 查询数据库，读取城区信息
    try:
        area_all = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR,errmsg="数据库异常")
    area_dict_li = []
    # 将对象转换为字段
    for area in area_all:
        area_dict_li.append(area.to_dict())

    # 将数据转换为json字符串
    # dict()相当于{}一个对象
    resp_dict = dict(code=RET.OK,errmsg="操作成功",data=area_dict_li)
    resp_json = json.dumps(resp_dict)

    # 将数据保存到redis中
    try:
        # 设置有效期的原因，是为了让数据同步--保证数据库与缓存一致
        # 缓存数据的同步问题---
            # 方法一：在操作mysql数据的时候，删除缓存数据(缺点：有人会遗忘出错率高)；
            # 方法二：给redis缓存机制设置有效期，具体秒数根据数据重要性（缺点：不能实时同步）
        redis_store.setex("area_info",constants.AREA_INFO_REDIS_CACHE_EXPIRES,resp_json)
    except Exception as e:
        current_app.logger.error(e)
    return resp_json,200,{"Content-Type": "application/json"}