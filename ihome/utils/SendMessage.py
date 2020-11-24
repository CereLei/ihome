from ronglian_sms_sdk import SmsSDK

accId = '8a216da875e463e00175f3075d0c0528'
accToken = '4a0b305f76a5490ebe81b59cc99055bc'
appId = '8a216da875e463e00175f3075e26052f'

# 以函数的方式，会每次SmsSDK调用，所以以类的方式只在初始化进行
# def send_message():
#     sdk = SmsSDK(accId, accToken, appId)
#     tid = '容联云通讯创建的模板'
#     mobile = '手机号1,手机号2'
#     datas = ('变量1', '变量2')
#     resp = sdk.sendMessage(tid, mobile, datas)
#     print(resp)
#
# send_message()

class CCP(object):
    """自己封装的发送短信辅助类"""
    # 用于保存对象的类属性
    instance = None
    def __new__(cls, *args, **kwargs):
        # 单例模式-判断CCP类有没有意见创建好的对象，有则返回，没有创建
        if cls.instance is None:
            obj = super(CCP,cls).__new__(cls)
            obj.sdk = SmsSDK(accId, accToken, appId)
            cls.instance = obj
        return cls.instance

    def send_message(self,tid, mobile, datas):
        resp = self.sdk.sendMessage(tid, mobile, datas)
        status_code = eval(resp).get('statusCode')
        if status_code == '000000':
            # 表示短信发送成功
            return 0
        else:
            # 表示短信发送失败
            return -1
        # print(eval(resp).get('statusCode'))


if __name__ == '__main__':
    ccp = CCP()
    ccp.send_message('1','17778903911',('SAD1','3'))