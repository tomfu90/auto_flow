# mock_server/app.py
# coding = utf-8
"""
多用户支持的 Mock 服务：
- 支持多个用户独立登录
- 每个用户获得唯一 token
- token 与用户绑定，精确鉴权
- 用户数据完全隔离
"""

from flask import Flask, request, jsonify, g
import time
import sqlite3
import uuid
from datetime import datetime,timedelta
import os,sys
from werkzeug.utils import secure_filename
from pathlib import Path
import re
#获取项目根目录
root_dir = Path(__file__).parent.parent
#如果根目录不存在 sys.path，就插在最前面
if str(root_dir) not in sys.path:
    sys.path.insert(0,str(root_dir))

#导入项目模块
from libs.database import get_db_connection,init_db



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = root_dir /'mock_server'/'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)




def verify_token(auth_header):
    #校验auth_header是否存在，是否指定字符串开头
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    #将获取到的token和数据库查询比对
    with get_db_connection() as conn:
        row = conn.execute("SELECT username,expires_at FROM tokens WHERE token=?",(token,)).fetchone()
        #1 数据库查询不到返回空
        if not row:
            return None
        expires_at = datetime.strptime(row['expires_at'], '%Y-%m-%d %H:%M:%S.%f')
        #2 token过期 返回无效
        if datetime.now() > expires_at:
            conn.execute("DELETE FROM tokens WHERE token=?",(token,))
            return None
        return row['username']



# @app.before_request
# def load_user():
#     auth = request.headers.get('authorization')
#     g.current_user = verify_token(auth)




@app.route('/api/login', methods=['POST'])
def login():
    '''登陆'''
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "用户名或密码不能为空"}), 400

    with get_db_connection() as conn:
        row = conn.execute("select password from users where username=?",(username.lower(),)).fetchone()
        if not row or  row['password']!=password:
            return jsonify({"error": "用户名或密码错误"}), 401

    token = str(uuid.uuid4())
    now = datetime.now()
    expires = now + timedelta(hours=1)
    now_at = now.strftime('%Y-%m-%d %H:%M:%S.%f')
    expires_at =expires.strftime('%Y-%m-%d %H:%M:%S.%f')

    with get_db_connection() as conn:
        # 删除旧token ,插入新token，防止多个token存在
        conn.execute('''delete from tokens where username=?''', ( username.lower(),))
        conn.execute('''insert into tokens values (?,?,?,?)''', (token,username.lower(),now_at,expires_at))

    return jsonify({"access_token": token,"info":"登陆成功"})





@app.route('/api/account/balance', methods=['GET'])
def get_balance():
    '''查看账户余额'''
    username = verify_token(request.headers.get('Authorization'))
    if not username:
        return jsonify({"error": "Invalid or missing token"}), 401

    with get_db_connection() as conn:
        row = conn.execute("select balance from accounts where username=?",(username,)).fetchone()
        if not row:
            return jsonify({"username":username,"error": "账户不存在"}),404
        balance = row['balance']

    return jsonify({"username": username, "balance": balance})


@app.route('/api/account/transactions', methods=['GET'])
def get_transactions():
    '''查看交易流水'''
    username = verify_token(request.headers.get('Authorization'))
    if not username:
        return jsonify({"error": "Invalid or missing token"}), 401

    with get_db_connection() as conn:
        rows = conn.execute("select id,username,type,amount,time from transactions where username=? order by time desc",(username,)).fetchall()
        transactions = [ dict(row) for row in rows]

    return jsonify({"username": username,"transactions":transactions})




@app.route('/api/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    '''查看订单记录'''
    username = verify_token(request.headers.get('Authorization'))
    if not username:
        return jsonify({"error": "Invalid or missing token"}), 401

    with get_db_connection() as conn:
        row = conn.execute("select * from orders where order_id=? and username=? ",(order_id,username)).fetchone()

    if not row:
        return jsonify({"error": "Order not found"}), 404

    return jsonify(dict(row))


@app.route('/api/orders', methods=['POST'])
def create_order():
    '''创建订单'''
    username = verify_token(request.headers.get('Authorization'))
    if not username:
        return jsonify({"error": "Invalid or missing token"}), 401

    data = request.get_json()
    amount = data.get('amount')
    order_type = data.get('order_type')
    currency = data.get('currency', 'CNY') # 不传默认cny
    product_id = data.get('product_id')

    # 金额不能为空
    if amount is None or amount == "" :
        return jsonify({"error": "Invalid amount"}), 400
    #金额必须为数字格式
    if not isinstance(amount, (int,float)):
        return jsonify({"error": "Invalid amount"}), 400
    #金额不能超过3位小数
    if '.' in str(amount) and len(str(amount).split('.')[1])>2:
        return jsonify({"error": "金额最多只能有2位小数"}), 422
    #金额不能小于0
    if amount <= 0:
        return jsonify({"error": "金额不能小于0"}), 422
    #金额不能超过10000
    if amount > 100000:
        return jsonify({"error": "金额不能超过100000"}),422
    # product_id 不能为空
    if not product_id:
        return jsonify({"error": "Invalid product_id"}), 400
    # product_id 长度要在2-8位之间
    if len(str(product_id)) < 2  or len(str(product_id))>8:
        return jsonify({"error": "product_id长度要在2-8之间"}), 422
    # currency输入要符合要求，只能是CNY USD 之中的
    if  currency.upper() not in ['CNY', 'USD']:
        return jsonify({"error": "currency格式输入错误"}), 400
    # type不能为空
    if not order_type:
        return jsonify({"error": "Invalid order_type"}), 400
    # type 输入只能在DEPOSIT, WITHDRAW, PAYMENT之中
    if order_type.upper() not in ['DEPOSIT', 'WITHDRAW', 'PAYMENT']:
        return jsonify({"error": "order_type格式输入错误"}), 400

    #查询数据库用户余额
    with get_db_connection() as conn:
        row = conn.execute("select balance from accounts where username=? ",(username,)).fetchone()
        if not row:
            return jsonify({"error":"账户不存在"}),404
    #创建支出-订单余额 不能大于当前用户余额
    amount = round( float(amount), 2)
    if amount > row['balance'] and order_type in ['PAYMENT', 'WITHDRAW']:
        return jsonify({"error":"当前订单金额超过账户余额"}), 422

    order_id = f"ORD{uuid.uuid4().hex[:8].upper()}"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = 'CREATED' #默认订单状态是创建
    #插入数据库
    with get_db_connection() as conn:
        conn.execute(""" insert into orders(order_id,username,amount,currency,order_type,
        product_id,status,created_at) values (?,?,?,?,?,?,?,?)"""
        ,(order_id,username,amount,currency.upper(),order_type.upper(),product_id,status,created_at))

    return( {
        "order_id": order_id,
        "username": username,
        "amount": amount,
        "order_type": order_type.upper(),
        "currency": currency.upper(),
        "product_id": product_id,
        "status": status,
        "created_at": created_at
    }), 201

@app.route('/api/GetUploads', methods=['GET'])
def list_uploads():
    username = verify_token(request.headers.get('Authorization'))
    if not username:
        return jsonify({"error": "Invalid or missing token"}), 401
    limit = request.args.get('limit',default=10,type=int)
    limit = min(max(limit,1),100)
    with get_db_connection() as conn:
        rows = conn.execute('''select id,filename,original_name,
        file_size,username,upload_time from uploads where username=?
         order by upload_time desc limit ?''' ,(username,limit)).fetchall()

    return jsonify([dict(row) for row in rows ]), 200


@app.route('/api/upload', methods=['POST'])
def upload_file():
    username = verify_token(request.headers.get('Authorization'))
    if not username:
        return jsonify({"error": "Invalid or missing token"}), 401
    # 缺少文件上传属性
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files['file']
    # 点击了上传按钮，但没选择文件->上传文件为为空
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    # 文件上传格式校验
    ext = os.path.splitext(file.filename)[1].lstrip('.').lower()
    ALLOWED_MIMETYPES ={'jpg','jpeg','png'}
    if ext not in ALLOWED_MIMETYPES:
        return jsonify({"error": f"上传图片格式错误，支持的格式：'jpg','jpeg','png'"}), 400
    # 文件上传大小校验
    # 100k = 100 * 1024 字节
    original_name = file.filename
    file_name = f"{uuid.uuid4().hex}_{secure_filename(original_name)}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
    file.save(filepath)
    file_size = os.path.getsize(filepath)
    MAX_FILE_SIZE = 100* 1024
    if file_size > MAX_FILE_SIZE:
        os.remove(filepath)
        return jsonify({"error": f"上传文件大小超过最大限制:100k"}), 403


    upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db_connection() as conn:
        conn.execute(""" insert into uploads(filename,original_name,file_size,
        username,upload_time) values (?,?,?,?,?)""",
                     (file_name,original_name,file_size,username,upload_time))
    return jsonify({"message": "文件上传成功", "filename": file_name})

@app.route('/api/register', methods=['post'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    #必填项为空，注册失败
    if not username or not password or not confirm_password:
        return jsonify({"error":"账号或密码不能为空"}),400
    if password != confirm_password:
        return jsonify({"error": "密码和确认密码不一致"}), 403
    #用户名长度在2-10 之间
    if len(username)<2 or len(username)>10:
        return jsonify({"error": "账号长度不在2-10之间"}), 403
    #用户名格式检验：数字+字母
    if not re.match(r"^[a-zA-Z0-9]+$",username):
        return jsonify({"error": "账号只能由数字+字母组成"}), 403
    # 密码长度在6-16 之间
    if len(password)<6 or len(password)>16:
        return jsonify({"error": "密码长度不在6-16之间"}), 403
    #密码格式检验：数字+字母+下划线
    if not re.match(r"^[a-zA-Z0-9_]+$",password):
        return jsonify({"error": "密码只能由数字+字母+下划线组成"}), 403
    #重复创建账号
    with get_db_connection() as conn:
        row = conn.execute("select username from users where username=?",(username,)).fetchone()
        if row:
            return jsonify({"error": "账号已注册，请勿重复注册"}), 403
    #插入数据库
    with get_db_connection() as conn:
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        conn.execute(" insert into users(username,password,created_at) values (?,?,?)",(username.lower(),password,created_at))

    return jsonify({"username": username,"message":"注册成功"})


#flask状态检查
@app.route('/health')
def health():
    return {"status": "ok"}


if __name__ == '__main__':
    # 在 app.run() 前添加
    with get_db_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON")  # 确保外键约束
        cursor = conn.execute("PRAGMA database_list")
        print("API 使用的数据库路径:", cursor.fetchone()[2])
    init_db()  # 确保数据库表已创建
    app.run(host='0.0.0.0', port=5000, debug=False,use_reloader=False)