# -*- coding: utf-8 -*-
# flake8: noqa
from qiniu import Auth, put_file, etag,put_data
import qiniu.config
#需要填写你的 Access Key 和 Secret Key
access_key = 'kpHuEnsqyCUz5DDNOd6XdActBWBNSpt_Rw2iYCeJ'
secret_key = 'UQPtHQgm_O8-xYjftYW-RPSZ9r_c_GyLysJ7hnF2'

def storage(file_data):
    """上传图片"""

    #构建鉴权对象
    q = Auth(access_key, secret_key)
    #要上传的空间
    bucket_name = 'cere-ihome'
    #上传后保存的文件名
    # key = 'my-python-logo.png'

    #生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, None, 3600)

    #要上传文件的本地路径
    localfile = './sync/bbb.jpg'
    ret, info = put_data(token, None, file_data)
    if info.status_code ==200:
        # 表示上传成功
        return ret.get("key")
    else:
        # 上传失败
        raise  Exception("上传云服务器失败")

    # print(info)
    # print("*"*10)
    # print(info.status_code)
    # print("*"*10)
    # print(ret)
    # assert ret['hash'] == etag(localfile)

if __name__ == '__main__':
    with open("./6.jpg","rb") as f:
        a = f.read()
        storage(a)