from . import api # 相对路径导入
from ihome import db,models # 防止循环导包，导入需要推迟

from flask import current_app
@api.route('/index')
def index():
    # current_app.logger.error('1111')
    # current_app.logger.warn('1111')
    # current_app.logger.info('1111')
    # current_app.logger.debug('1111')
    return '222'