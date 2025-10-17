# coding = utf-8
# author = fufu
"""
统一工具函数
目的：避免代码重复
"""
from pathlib import Path
import yaml
import re
import sys

root_dir = Path(__file__).parent.parent
#如果根目录不存在 sys.path，就插在最前面
if str(root_dir) not in sys.path:
    sys.path.insert(0,str(root_dir))

from libs.random_utils import generate_random_username

def load_yaml(filepath: str):
    '''
    加载yaml文件
    :param filepath: 相对于项目根路径的目录
    :return: yaml解析后的字典
    '''
    base_path = Path(__file__).parent.parent #项目根目录
    full_path = base_path / filepath #完整文件路径
    #首先判断文件路径是否存在，不存在抛异常
    if not full_path.exists():
        raise FileNotFoundError(f"文件路径不存在：{full_path}")
    #文件路径存在，读取yaml文件内容
    with open(full_path, 'r', encoding='utf-8') as f:
        return  yaml.safe_load(f)

def render_placeholders(obj, context):
    """
    递归替换所有 {{key}} 为 context[key]
    支持 dict / list / str 嵌套结构
    """
    if isinstance(obj, dict):
        return {k: render_placeholders(v, context) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [render_placeholders(item, context) for item in obj]
    elif isinstance(obj, str):
        def replace_match(match):
            key = match.group(1)
            if key in context:
                return str(context[key])
            else:
                raise KeyError(f"占位符 '{{{key}}}' 未在 context 中定义！")
        return re.sub(r"\{\{(\w+)\}\}", replace_match, obj)
    else:
        return obj


def load_test_cases(yaml_path):
    """
    加载 YAML 文件，并自动替换占位符（如 {{random_username}}）
    返回渲染后的 Python 对象
    """
    raw_data = load_yaml(yaml_path)
    # 准备动态上下文（可扩展）
    context = {
        "random_username": generate_random_username(),
       # "random_email": generate_random_username() + "@test.com",
       # "timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
    }

    # 渲染整个 YAML 结构（直接递归处理根对象，更简洁）
    return render_placeholders(raw_data, context)

if __name__ == '__main__':
    print(load_test_cases("data/login/test_register.yaml"))