from . import api
from flask import request,jsonify,current_app,session
from ihome.utils.response_code import RET
from ihome import redis_store,db
from ihome.models import User
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash,check_password_hash
import re


@api.route("/users",methods=["POST"])
def register():
    """注册
    请求的参数： 手机号、短信验证码、密码、确认密码
    参数格式：json
    """

    # 获取请求的json数据，返回字段
    req_dict = request.get_json()
    print(req_dict)

    mobile = req_dict.get("mobile")
    sms_code = req_dict.get("sms_code")
    password = req_dict.get("password")
    password2 = req_dict.get("password2")

    # 校验参数
    if not all([mobile,sms_code,password,password2]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断手机号格式
    if not re.match(r"1[3456789]\d{9}",mobile):
        # 格式不对
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式错误")

    if password != password2:
        return jsonify(errno=RET.PARAMERR, errmsg="两次密码不一致")

    # 从redis中取出短信验证码
    try:
        real_sms_code = redis_store.get("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="读取真实短信验证码异常")

    # 判断短信验证码是否过期
    if real_sms_code is None:
        return jsonify(errno=RET.NODATA, errmsg="短信验证码失效")

    # 删除redis中的短信验证码，防止重复使用校验
    try:
        redis_store.delete("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)

    # 判断用户填写短信验证码的正确性
    # 操作数据库也是昂贵的成本，利用数据库的特性，在mobile设置独一无二的，直接抛出异常
    # if real_sms_code != sms_code:
    #     return jsonify(errno=RET.DATAERR, errmsg="短信验证码错误")
    #
    # # 判断用户的手机号是否注册过
    # try:
    #     user = User.query.filter_by(mobile=mobile).first()
    # except Exception as e:
    #     current_app.logger.error(e)
    # else:
    #     if user is not None:
    #         # 表示手机号已存在
    #         return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")

    # 盐值   salt--也就是随机字符串，然后通过sha1加密
    # 一般加密有sha1和md5，但是md5已经被攻破，少用，现在用sha256
    #  注册
    #  用户1   password="123456" + "abc"   sha1   abc$hxosifodfdoshfosdhfso
    #  用户2   password="123456" + "def"   sha1   def$dfhsoicoshdoshfosidfs
    # 用户登录  password ="123456"  "abc"  sha256      sha1   hxosufodsofdihsofho


    # 保存用户的注册数据到数据库中
    user = User(name=mobile,mobile=mobile)
    # user.generate_password_hash(password)

    # 在models中通过装饰器让属性相当于直接调类方法
    user.password = password  # 设置属性
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        # 数据库操作错误后的回滚
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAEXIST,errmsg="手机号已存在")
    except Exception as e:
        # 数据库操作错误后的回滚
        db.session.rollback()
        # 表示手机号出现了重复值，即手机号已注册过
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据库异常")

    # 保存登录状态到session中
    session["name"] = mobile
    session["mobile"] = mobile
    session["user_id"] = user.id

    # 返回结果
    return jsonify(errno=RET.OK, errmsg="注册成功")


@api.route("/login",methods=["post"])
def get_login():
    # 获取参数信息
    req_dict = request.get_json()
    mobile = req_dict.get("mobile")
    password = req_dict.get("password")

    # 校验参数
    if not all([mobile,password]):
        return jsonify(errno=RET.DATAERR,errmsg="数据不能为空")

    # 查询数据库
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)

    if user is None:
        return jsonify(err=RET.NODATA,errmsg="手机号不存在")

    # print(user.password)
    print(user.password_hash)
    check_pwd = check_password_hash(user.password_hash,password)
    print(check_pwd)
    if not check_password_hash(user.password_hash,password):
        return jsonify(errno=RET.DATAERR,errmsg="密码错误")

    return jsonify(errno='200',errmsg='登录成功')
