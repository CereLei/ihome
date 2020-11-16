# 最基本的文件
from ihome import create_app




app = create_app('develop')

@app.route('/index')
def index():
    print('1')
    return 'imde page'

if __name__ == '__main__':
    app.run()