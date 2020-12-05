# 用户资料
from . import api
from flask import g, current_app, jsonify, request,session
from ihome.utils.common import login_required
from ihome.utils.response_code import RET
from ihome.utils.image_storage import storage
from ihome.models import User
from ihome import db,constants
import json

# 装饰器放入视图下方
@api.route("/users/avatar", methods=["POST"])
@login_required
def set_user_avatar():
    """设置用户的头像
        参数： 图片(多媒体表单格式)  用户id (g.user_id)
    """
    # 装饰器的代码中已经将user_id保存到g对象中，所以视图中可以直接读取
    user_id = g.user_id

    # 获取图片
    image_file = request.files.get("avatar")

    if image_file is None:
        return jsonify(code=RET.PARAMERR,errmsg = "未上传")

    # 调用七牛上传图片，返回文件名
    try:
        file_name = storage(image_file)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code = RET.DATAERR,errmsg="上传图片错误")

    # 保存文件名到数据中
    try:
        User.query.filter_by(id=user_id).update({"avatar_url": file_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(code=RET.DATAERR,errmsg="保存图片错误")

    acatar_url = constants.QINIU_URL_DOMAIN + file_name
    return jsonify(code=RET.OK,errmsg="保存成功",data={"avatar_url":acatar_url})


@api.route("/user-info")
@login_required
def get_user_info():
    """获取用户信息"""
    user_id = g.user_id
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.OK,errmsg="用户信息获取失败")
    return jsonify(code=RET.OK,errmsg="",data={'name':user.name,'mobile':user.mobile,'avatar_url':constants.QINIU_URL_DOMAIN + user.avatar_url})

@api.route("/users/name",methods=["PUT"])
@login_required
def change_user_name():
    """修改用户名字"""
    user_id = g.user_id

    # 获取数据
    req_data = request.json()
    name = req_data.get("name")
    if not name:
        return jsonify(code=RET.DATAERR,errmsg="名字不能为空")

    # 保存用户昵称name，并同时判断name是否重复（利用数据库的唯一索引)
    try:
        User.query.filter_by(id=user_id).update({"name":name})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(code=RET.DATAERR,errmsg="设置用户错误")

    # 修改session数据中的name字段
    session["name"] = name
    return jsonify(code=RET.OK,errmsg="名字设置成功",data={"name":name})

@api.route("/users/auth")
@login_required
def get_user_auth():
    """获取用户的实名认证信息"""
    user_id = g.user_id
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DATAERR,errmsg="获取实名认证错误")

    if user is None:
        return jsonify(code=RET.NODATA,errmsg= "无效操作")

    return jsonify(code=RET.OK,errmsg="获取实名认证成功",data=user.auth_to_dict())


@api.route("/users/auth",methods=["POST"])
@login_required
def set_user_auth():
    user_id = g.user_id
    req_data = request.get_json()

    real_name = req_data.get('real_name')
    id_card = req_data.get('id_card')

    if not all([real_name,id_card]):
        return jsonify(code=RET.DATAERR,errmsg="数据不能为空")
    try:
        User.query.filter_by(id=user_id).update({"real_name":real_name,"id_card":id_card})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(code=RET.DBERR,errmsg="设置实名认证错误")

    return jsonify(code=RET.OK,errmsg="设置成功")

