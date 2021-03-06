from . import api
from ihome.utils.common import login_required
from flask import g, current_app, jsonify, request
from ihome.utils.response_code import RET
from ihome.models import Area, House, Facility, HouseImage,Order,User
from ihome import db, constants, redis_store
from ihome.utils.image_storage import storage
from datetime import datetime
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

@api.route("/houses/info", methods=["POST"])
@login_required
def save_house_info():
    """保存房屋的基本信息
        前端发送过来的json数据
        {
            "title":"",
            "price":"",
            "area_id":"1",
            "address":"",
            "room_count":"",
            "acreage":"",
            "unit":"",
            "capacity":"",
            "beds":"",
            "deposit":"",
            "min_days":"",
            "max_days":"",
            "facility":["7","8"]
        }
    """

    # 获取数据
    user_id = g.user_id
    house_data = request.get_json()
    print(house_data)

    title = house_data.get("title")  # 房屋名称标题
    price = house_data.get("price")  # 房屋单价
    area_id = house_data.get("area_id")  # 房屋所属城区的编号
    address = house_data.get("address")  # 房屋地址
    room_count = house_data.get("room_count")  # 房屋包含的房间数目
    acreage = house_data.get("acreage")  # 房屋面积
    unit = house_data.get("unit")  # 房屋布局（几室几厅)
    capacity = house_data.get("capacity")  # 房屋容纳人数
    beds = house_data.get("beds")  # 房屋卧床数目
    deposit = house_data.get("deposit")  # 押金
    min_days = house_data.get("min_days")  # 最小入住天数
    max_days = house_data.get("max_days")  # 最大入住天数

    # 校验数据
    if not all([title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(code=RET.PARAMERR,errmsg="参数不完整")

    # 判读金额是否正确
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.PARAMERR, errmsg="参数错误")

    # 判断城区id是否存在
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, errmsg="数据库异常")

    if area is None:
         return jsonify(code=RET.NODATA,errmsg="城区信息有误")

    # 保存房屋信息
    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )

    # 处理房屋的设施信息
    facility_ids = house_data.get("facility")

    # 如果用户勾选了设施信息，再保存数据库
    if facility_ids:
        # ["7","8"]
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(code=RET.DBERR,errmsg="数据库异常")

        if facilities:
            # 表示有合法的设施数据
            # 保存设施数据
            house.facilities = facilities


    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(code=RET.DBERR,errmsg="保存数据失败")

    # 保存数据成功
    return jsonify(code=RET.OK,errmsg="操作成功",data={"house_id":house.id})


@api.route("/houses/image",methods=["POST"])
@login_required
def save_house_image():
    """保存图片
    参数 图片 房屋的id
    """
    house_id = request.form.get("house_id")
    image_file = request.files.get("house_image")

    if not all([image_file,house_id]):
        return jsonify(code=RET.PARAMERR,errmsg="参数不完整")

    # 判断house_id是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR,errmsg="数据库异常")

    if house is None:
        return jsonify(code=RET.NODATA,errmsg="房屋不存在")

    image_data = image_file.read()
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.THIRDERR,errmsg="保存图片失败")

    # 保存图片信息到数据可中
    house_image = HouseImage(house_id=house_id,url=file_name)
    db.session.add(house_image)

    # 处理房屋的主图片
    if not house.index_image_url:
        house.index_image_url = file_name
        db.session.add(house)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(code=RET.DBERR,errmsg="保存图片数据异常")

    image_url = constants.QINIU_URL_DOMAIN + file_name

    return jsonify(code=RET.OK,errmsg="操作成功",data={"image_url":image_url})

# GET /api/v1.0/houses?sd=2017-12-01&ed=2017-12-31&aid=10&sk=new&p=1
@api.route("/houses")
@login_required
def get_house_list():
    """获取房屋的列表信息(搜索页面)"""
    start_date = request.args.get("sd","") # 用户想要的起始时间
    end_date = request.args.get("ed","") # 用户想要的结束时间
    area_id = request.args.get("aid","") # 区域编号
    sort_key = request.args.get("sk","new") # 排序关键字
    page = request.args.get("p") # 页数

    # 处理时间
    try:
        if start_date:
            start_date = datetime.strftime(start_date,"%Y-%m-%d")
        if end_date:
            end_date = datetime.strftime(end_date,"%Y-%m-%d")
        if start_date and end_date:
            assert start_date<=end_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.PARAMERR,errmsg="日期参数有误")

    # 判断区域
    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(code=RET.PARAMERR,errmsg="区域参数有误")
    # 处理页数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

   # 获取缓存数据
    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
    try:
        resp_json = redis_store.hget(redis_key,page)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json:
            print("使用了缓存")
            return resp_json,200,{"Content-Type": "application/json"}

    # 过滤条件的参数列表容器--因为不知道参数有什么所有，有就存里面
    filter_params = []

    # 填充过滤参数
    # 时间条件
    conflict_orders = None
    try:
        if start_date and end_date:
            # 查询冲突的订单
            conflict_orders = Order.query.filter(Order.begin_date<=end_date,Order.end_date>=start_date).all()
        elif start_date:
            conflict_orders = Order.query.filter(Order.begin_date <= end_date).all()
        elif end_date:
            conflict_orders = Order.query.filter(Order.begin_date<end_date)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR,errmsg="数据异常")

    if conflict_orders:
        # 从订单中获取冲突的房屋id
        conflict_house_ids = [order.house_id for order in conflict_orders]

        # 如果冲突的房屋id不为空，向查询参数中添加条件
        if conflict_house_ids:
            filter_params.append(House.id.notin_(conflict_house_ids))

    # 区域条件
    if area_id:
        filter_params.append(House.area_id == area_id)
    house_query = None
    # 查询操作
    if sort_key == "booking": # 入住最多
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sort_key == "price-inc":
        house_query = House.query.filter(*filter_params).order_by(House.price.asc())
    elif sort_key =="price-des":
        house_query = House.query.filter(*filter_params).order_by(House.price.desc())
    else:
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())

    # 分页直接在查询后的数据加paginate对象
    try:
        #                               当前页数必须是Int类型         每页数据量                              自动的错误输出
        page_obj = house_query.paginate(page=int(page), per_page=constants.HOUSE_LIST_PAGE_CAPACITY, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR,errmsg="数据库错误")
    # 获取页面数据
    house_li = page_obj.items
    houses = []
    for house in house_li:
        houses.append(house.to_basic_dict())

    # 获取总页数
    total_page = page_obj.pages

    resp_dict = dict(code=RET.OK,errmsg="",data = {"total_page": total_page, "houses": houses, "current_page": page})

    resp_json = json.dumps(resp_dict)

    if page <= total_page:
        # 设置缓存数据
        redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
        print("处理数据")
        try:
            # redis_store.hset(redis_key, page, resp_json)
            # redis_store.expire(redis_key, constants.HOUES_LIST_PAGE_REDIS_CACHE_EXPIRES)
            # 如何hset成功，expire失效了，这就不好，所有引入管道pipeline

            # 创建redis管道对象，可以一次执行多个语句
            pipeline = redis_store.pipeline()

            # 开启多个语句的记录
            pipeline.multi()

            # 添加指令
            pipeline.hset(redis_key, page, resp_json)
            pipeline.expire(redis_key, constants.HOUES_LIST_PAGE_REDIS_CACHE_EXPIRES)

            # 执行语句
            pipeline.execute()
        except Exception as e:
            current_app.logger.error(e)


    return resp_json, 200, {"Content-Type": "application/json"}

@api.route("/user/house",methods=["GET"])
@login_required
def get_user_houses():
    """获取房东发布的房源信息条目"""
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
        houses = user.houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取数据失败")

