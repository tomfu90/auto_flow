# coding = utf-8
# author =fufu
import smtplib
import os
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header

def send_test_report(
        total: int,
        passed: int,
        failed: int,
        errors: int,
        skipped: int,
        xfail: int,
        xpass:int,
        duration_sec: int,
        allure_link: str= None
):
    sender = os.getenv('EMAIL_SENDER')
    password = os.getenv('EMAIL_PASSWORD')
    receivers = os.getenv('EMAIL_RECEIVERS',"").split(',')
    cleaned_receivers = [r.strip() for r in receivers if r.strip()] # 去除收件人空格

    #配置信息缺少：发件人/邮件人/授权码
    if not sender or not password or not cleaned_receivers[0]:
        print("⚠️ 邮箱配置缺失，跳过邮件发送")
        return

    fail_count = failed + errors
    has_failure = fail_count >0
    pass_rate = f"{(passed / total * 100):.1f}%" if total>0 else "0%"

    # 动态设置颜色和状态文本
    status_color = "#f44336" if has_failure else "#4CAF50"
    status_text = "❌ 测试未通过" if has_failure else "✅ 测试全部通过"
    bg_color = "#ffebee" if has_failure else "#e8f5e9"
    subject_prefix = "🚨 测试失败" if has_failure else "✅ 测试通过"

    html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 20px auto; 
                    border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; 
                    background-color: {bg_color};">
            <h2 style="color: {status_color};">{status_text}</h2>
            <p><strong>总用例数：</strong> {total}</p>
            <p><strong>执行耗时：</strong> {duration_sec:.2f} 秒</p>

            <table style="width: 100%; margin: 15px 0; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px; background-color: #d4edda; text-align: left;"><strong>✅ 通过</strong></td>
                    <td style="padding: 8px; background-color: #d4edda; text-align: right; font-weight: bold;">{passed}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; background-color: #f8d7da; text-align: left;"><strong>❌ 失败</strong></td>
                    <td style="padding: 8px; background-color: #f8d7da; text-align: right; font-weight: bold;">{failed}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; background-color: #f8d7da; text-align: left;"><strong>⚠️ 错误</strong></td>
                    <td style="padding: 8px; background-color: #f8d7da; text-align: right; font-weight: bold;">{errors}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; background-color: #fff3cd; text-align: left;"><strong>⏭️ 跳过</strong></td>
                    <td style="padding: 8px; background-color: #fff3cd; text-align: right; font-weight: bold;">{skipped}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; background-color: #d1ecf1; text-align: left;"><strong>🔶 预期失败_xfail</strong></td>
                    <td style="padding: 8px; background-color: #d1ecf1; text-align: right; font-weight: bold;">{xfail}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; background-color: #ffeeba; text-align: left;"><strong>🎉 意外通过_xpass</strong></td>
                    <td style="padding: 8px; background-color: #ffeeba; text-align: right; font-weight: bold;">{xpass}</td>
                </tr>
            </table>

            {f'<p style="color: #856404; background-color: #fff3cd; padding: 10px; border-radius: 4px; margin-top: 15px;"><strong>⚠️ 注意：</strong>发现 {xpass} 个 xpass 用例！请检查是否需移除 @pytest.mark.xfail 标记。</p>' if xpass > 0 else ''}

            {f'<p style="margin-top: 15px;"><a href="{allure_link}" target="_blank" style="display: inline-block; background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">📊 查看 Allure 报告</a></p>' if allure_link else ''}
        </div>
        """

    msg = MIMEText(html_body, 'html', 'utf-8')
    msg['From'] = Header(sender)
    msg['To'] = Header(", ".join(cleaned_receivers))
    msg['Subject'] = Header(f"[{subject_prefix}]{total}个用例执行完毕", 'utf-8')

    try:
        server = smtplib.SMTP_SSL('smtp.qq.com', 465)
        server.login(sender, password)
        server.sendmail(sender, cleaned_receivers, msg.as_string())
        server.quit()
        print("📧 测试报告邮件已发送！")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

if __name__ == '__main__':
    send_test_report(
        total=6,
    passed=3,
    failed=1,
    errors=0,
    skipped=1,
    xfail=1,
    xpass=0,
    duration_sec=2,
    allure_link = "http://.localhost.com"
    )