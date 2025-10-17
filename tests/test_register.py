# coding = utf-8
# author = fufu

import sys
import pytest
from pathlib import Path
import allure
import random
import string
#设置项目根目录，防止意外找不到导内部模块路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
from libs.utils import load_yaml
from libs.api_client import  Apiclient
from libs.logger import log_assertion
from libs.utils import  load_test_cases

#获取用例数据
#testcases = load_yaml("data/login/test_register.yaml")
testcases = load_test_cases("data/login/test_register.yaml")

success_cases = testcases['success_register']
fail_cases = testcases['fail_register']

#获取url配置表
config = load_yaml("config/config.yaml")
#获取注册url
env = config["env"]
register_url = config['environments'][env]["register_url"]
#获取base_url
base_url = config['environments'][env]["base_url"]

@pytest.mark.smoke
@pytest.mark.parametrize("case", success_cases)
def test_register_success(case,db_conn):
    print(f"开始发起测试：{case['name']}")
    #allure动态标题
    allure.dynamic.title(case['name'])
    #注册会话
    client = Apiclient(base_url)
    #发起注册请求
    response = client.post(register_url, json=case['input'])
    with allure.step('校验响应状态码'):
        #校验状态码
        actual_value = response.status_code
        expected_value = case['expected']['status_code']
        log_assertion(actual_value, actual_value==expected_value, actual_value, expected_value)
        assert actual_value == expected_value,f"实际：{actual_value} 期望：{expected_value}"
    with allure.step('校验响应返回信息'):
        actual_value = response.json()['message']
        expected_value = case['expected']['message']
        log_assertion(actual_value, actual_value == expected_value, actual_value, expected_value)
        assert actual_value == expected_value, f"实际：{actual_value} 期望：{expected_value}"
    with allure.step('数据库校验：写入数据库'):
        row = db_conn.execute("SELECT username FROM users WHERE username=?", (case['input']['username'],)).fetchone()
        actual_value = response.json()['username']
        expected_value =row['username']
        log_assertion(actual_value, actual_value == expected_value, actual_value, expected_value)
        assert actual_value == expected_value, f"接口返回：{actual_value} 数据库：{expected_value}"

@pytest.mark.parametrize("case", fail_cases)
def test_register_fail(case):
    print(f"开始发起测试：{case['name']}")
    #allure动态标题
    allure.dynamic.title(case['name'])
    #注册会话
    client = Apiclient(base_url)
    #发起注册请求
    response = client.post(register_url, json=case['input'])
    with allure.step('校验响应状态码'):
        #校验状态码
        actual_value = response.status_code
        expected_value = case['expected']['status_code']
        log_assertion(actual_value, actual_value==expected_value, actual_value, expected_value)
        assert actual_value == expected_value,f"实际：{actual_value} 期望：{expected_value}"
    with allure.step('校验响应返回信息'):
        actual_value = response.json()['error']
        expected_value = case['expected']['error']
        log_assertion(actual_value, actual_value == expected_value, actual_value, expected_value)
        assert actual_value == expected_value, f"实际：{actual_value} 期望：{expected_value}"

