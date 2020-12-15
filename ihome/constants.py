# 常量数据保存

# 图片验证码redis的有效期(秒)
IMAGE_CODE_REDIS_EXPIRES = 1800

# 短信redis的有效期
SMS_CODE_REDIS_EXPIRES = 300

# 发送短信验证码间隔--短信redis发送60秒之后，才可以发送
SEND_SMS_CODE_INTERVAL = 60

# 登录最大的次数-防止暴力测试
LOGIN_ERROR_MAX_TIMES =5

# 七牛域名
QINIU_URL_DOMAIN = "http://qkl8z4v66.hd-bkt.clouddn.com/"

# 城市区域的缓存时间
AREA_INFO_REDIS_CACHE_EXPIRES = 7200

# 分页每页几条
HOUSE_LIST_PAGE_CAPACITY = 2

# 每页显示数据缓存
HOUES_LIST_PAGE_REDIS_CACHE_EXPIRES = 3600