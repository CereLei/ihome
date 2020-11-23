from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store
from ihome.constants import IMAGE_CODE_REDIS_EXPIRES
from flask import current_app,jsonify,make_response
from ihome.utils.response_code import RET
import base64

# 127.0.0.1/api/v1.0/image_code/image_code_id
@api.route('/image_code/<image_code_id>')
def get_image_code(image_code_id):
    """
    获取图片验证码
    :params: image_code_id验证码编号
    ：return ：正常:验证码图片  异常：返回json
    """
    # 获取参数
    # 验证参数

    # 业务逻辑处理（1.生成验证码图片，2.将验证码真实值编号保存到redis，）
    # 1.生成验证码图片
    name, text, image_data = captcha.generate_captcha()
    #2.将验证码真实值编号保存到redis

    # 单条维护记录使用redis的string类型
    # redis_store.set("image_code_%s" % image_code_id,text )
    # # 设置有效期
    # redis_store.expire("image_code_%s" % image_code_id,IMAGE_CODE_REDIS_EXPIRES)
    # setex(name, time, value)设置可以对应的值为string类型的value，并指定此键值对应的有效期
    try:
        redis_store.setex("image_code_%s" % image_code_id, IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 记录日志
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,  errmsg="保存图片验证码失败")

    # 返回值

    base64_data = base64.b64decode(image_data)
    print("输出：")
    print(base64_data)
    resp = make_response(image_data)
    resp.headers["Content-Type"] = "image/jpg"
    return resp