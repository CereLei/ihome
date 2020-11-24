from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store,db,constants
from ihome.constants import IMAGE_CODE_REDIS_EXPIRES
from flask import current_app,jsonify,make_response,request
from ihome.utils.response_code import RET
from ihome.utils.SendMessage import CCP
from ihome.models import User
import random

# 127.0.0.1/api/v1.0/image_code/image_code_id
@api.route('/image_codes/<image_code_id>')
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
    resp = make_response(image_data)
    resp.headers["Content-Type"] = "image/jpg"
    return resp

# GET /api/sms_codes/<mobile>?image_code=xxxxx&image_code_id=xxxxx
@api.route("/sms_codes/<re(r'1[34578]\d{9}'):mobile>")
def get_sms_code(mobile):
    """获取短信验证码"""
    # 获取参数
    image_code = request.args.get("image_code")
    image_code_id = request.args.get("image_code_id")

    if not all([image_code,image_code_id]):
        # 表示参数不完整
        return jsonify(errno=RET.PARAMERR,errmsg='参数不完整')

    # 业务逻辑处理
    # 从redis中取出真实的图片验证码--(凡是redis操作都需要写try)
    try:
        real_image_code = redis_store.get("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR,errmsg='redis 数据错误')

    # 判断图片验证码是否过期
    if real_image_code is None:
        return jsonify(errno=RET.NODATA,errmsg='验证码过期')

    # 删除redis中的图片验证码，防止用户使用同一个图片验证码验证多次
    try:
        redis_store.delete("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)

    # 与用户填写的值进行对比
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR,errmsg='验证码输入错误')

    # 判断对于这个手机号的操作，在60秒内有没有之前的记录，如果有，则认为用户操作频繁，不接受处理
    try:
        send_flag = redis_store.get("send_sms_code_%s" % mobile )
    except Exception as e:
        current_app.logger.error(e)
    else:
        if send_flag is not None:
            # 表示在60秒内之前有过发送的记录
            return jsonify(errno=RET.REQERR, errmsg="请求过于频繁，请60秒后重试")


    # 判断手机号是否存在-从数据库查-(存在则返回数据，不存在则返回None)
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if user is not None:
            # 表示数据库存在
            return jsonify(errno=RET.DATAERR,errmsg='手机号已经存在')
    # 如果手机号不存在，则生成验证码-6为数字，不足补0
    sms_code = "%06d" % random.randint(0,999999)

    # 保存真实的短信验证码
    try:
        redis_store.setex("sms_code_%s" % mobile,constants.SMS_CODE_REDIS_EXPIRES,sms_code)
        # 保存发送给这个手机号的记录，防止用户在60s内再次出发发送短信的操作
        redis_store.setex("send_sms_code_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存短信验证码异常")

    # 发送短信
    try:
        ccp = CCP()
        result = ccp.send_message(1,mobile,(sms_code,int(constants.SMS_CODE_REDIS_EXPIRES/60)))
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg="发送异常")

    # 返回值
    if result == 0:
        # 发送成功
        return jsonify(errno=RET.OK, errmsg="发送成功")
    else:
        return jsonify(errno=RET.THIRDERR, errmsg="发送失败")

