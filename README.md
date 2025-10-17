# auto_flow - 自动化 API 测试框架

> 作者：fufu（long哥 2025下半年在线求职测试工作呀🐶） 

> 一个基于 Python + Flask + Pytest 的全栈自动化测试框架，支持接口 + 数据库断言、动态参数、多用户、Allure 报告、日志追踪与 **Git 集成测试**。

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) 
![Pytest](https://img.shields.io/badge/Pytest-7.0%2B-green) 
![Allure](https://img.shields.io/badge/Allure-2.13%2B-purple) 
![CI](https://github.com/tomfu90/auto_flow/actions/workflows/ci.yml/badge.svg)

---

## 🚀 项目简介

`auto_flow` 是一个轻量级、可扩展的自动化测试框架，专为业务系统设计。它集成了：

- ✅ Flask 模拟后端服务
- ✅ SQLite 存储用户数据与 Token
- ✅ YAML 配置驱动测试用例
- ✅ 动态参数化执行
- ✅ 接口 + 数据库双断言
- ✅ Allure 详细报告
- ✅ 多用户分组登录支持
- ✅ 本地精准日志记录
- 🔄 **Git 集成测试（GitHub Actions）**

适用于 **API 功能测试、回归测试、接口联调、持续集成** 场景。

---

## 🔧 核心功能

| 功能 | 说明 |
|------|------|
| 🌐 Flask 模拟接口 | 提供健康检查、注册、登录、余额查询、订单管理、文件上传下载等完整接口 |
| 🗃️ SQLite 数据库 | 存储用户信息、Token、交易流水，支持 DB 断言 |
| 📄 YAML 测试用例 | 所有用例以 `.yaml` 文件编写，结构清晰，易于维护 |
| 🔄 参数化执行 | 使用 `@pytest.mark.parametrize` 批量导入 YAML 数据，动态执行 |
| 🔍 接口 + DB 断言 | 支持接口返回断言 + 数据库一致性验证 |
| 👥 多用户分组登录 | `conftest.py` 支持按用户分组，模拟多个已登录状态 |
| 📊 Allure 报告 | 分步骤展示请求、响应、断言过程，可视化强 |
| 📝 精准日志 | 记录每个接口请求、响应、断言结果，便于排查问题 |
| 🎯 动态变量渲染 | `utils` 模块支持在 YAML 中使用 `${rand}`、`${time}` 等随机变量 |
| 🔄 **Git 集成测试** | **每次 `git push` 自动触发 CI，运行全量测试并生成 Allure 报告** |

---

## 🔄 Git 集成测试（GitHub Actions）

本项目已集成 **GitHub Actions**，实现 **提交即测试** 的 DevOps 流程：

### ✅ 自动触发条件
- 当你向 `main` 分支 `git push` 时
- 或提交 Pull Request 时

### 🛠️ CI 流程包含
1. 安装 Python 依赖
2. 启动 Flask 模拟服务（后台）
3. 执行 Pytest 测试用例
4. 生成 Allure 测试报告
5. （可选）上传报告到 Artifacts

### 📂 配置文件
```yaml
.github/workflows/ci.yml
