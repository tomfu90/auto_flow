# coding = utf-8
import traceback
import requests
import allure
import json
import sys
from pathlib import Path
#获取项目根目录
root_dir = Path(__file__).parent.parent
#如果根目录不存在 sys.path，就插在最前面
if str(root_dir) not in sys.path:
    sys.path.insert(0,str(root_dir))
from libs.logger import log_test_action



class Apiclient:

    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/") # 移除末尾斜杠（避免拼接时出现双斜杠）
        self.session = requests.Session() #创建持久会话

    def _request(self, method, path, **kwargs):
        url = self.base_url + path  # 拼接完整请求
        headers = dict(self.session.headers) # 获取会话请求头
        body = kwargs.get("json") or {} #请求体请求详情，不是json格式，就默认空字典
        files = kwargs.get("files") or {}
        #构造请求摘要，用于allure和log日志记录
        req_summary = f"{method} {url}"
        req_info =(
            f"URL: {url}\n"
            f"Method: {method}\n"
            f"Headers: {json.dumps(headers,indent=2,ensure_ascii=False)}\n"
            f"Body:{json.dumps(body,indent=2,ensure_ascii=False) if body else 'None'}" # 将python字典格式转为json格式传递

        )
        try:
            with allure.step(f'发送请求:{req_summary}'):
                allure.attach(req_info, "请求详情", attachment_type=allure.attachment_type.TEXT)

            # 发起请求
            response = self.session.request(method, url, timeout=15, **kwargs)
            # 成功处理响应
            try:
                resp_data = response.json()
                resp_text = json.dumps(resp_data, indent=2, ensure_ascii=False)
            except Exception:
                resp_data = None
                resp_text = response.text
            with allure.step(f"响应：{response.status_code}"):
                allure.attach(resp_text, "响应详情", allure.attachment_type.JSON if resp_data else allure.attachment_type.TEXT)
            #记录成功业务日志
            log_test_action(action="api_request_success", details=f"Status={response.status_code} | URL={url} | Request={body}| Response={resp_data if resp_data else "non-json"}")

            return response
        except requests.exceptions.RequestException as e:
            # 捕获requests请求异常
            error_msg = f"e.__class__.__name__: {str(e)}"
            full_traceback = traceback.format_exc()
            #allure记录异常
            with allure.step(f"请求失败：{req_summary}"):
                allure.attach(req_info,"请求详情", attachment_type=allure.attachment_type.TEXT)
                allure.attach(error_msg,"错误信息", attachment_type=allure.attachment_type.TEXT)
                allure.attach(full_traceback, "堆栈信息", attachment_type=allure.attachment_type.TEXT)
            #业务日志记录异常
            log_test_action(action='api_request_failed', details=f"URL={url} | Method={method}| Request={body}|Error={error_msg}")
            raise
        except Exception as e:
            # 兜底异常
            log_test_action(action='api_request_error',details=f"URL={url} | Request={body}|Error={str(e)} | Trace={traceback.format_exc()}")
            raise


    def get(self, path, **kwargs):
        return self._request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self._request("POST", path, **kwargs)

if __name__ == "__main__":
    api_client = Apiclient('http://127.0.0.1:5000')
    data1 ={
        'username': 'tester',
        'password': 'SecurePass123!'

    }
    print(f"data1:{data1}")
    resp1 = api_client.post('/api/login', json=data1)
    print(resp1.json())
    data2 = {
        'username': 'tester12',
        'password': 'SecurePass1231!111'

    }
    print(f"data2:{data2}")
    resp2 = api_client.post('/api/login', json=data2)
    print(resp2.json())







