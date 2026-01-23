import os
import time
from playwright.sync_api import sync_playwright

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    cookie_value = os.environ.get('REMEMBER_WEB_COOKIE')
    
    with sync_playwright() as p:
        # 使用 WARP SOCKS5 代理启动浏览器
        browser = p.chromium.launch(
            headless=True,
            proxy={"server": "socks5://127.0.0.1:40000"},
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        
        # 注入 Cookie 绕过登录
        if cookie_value:
            context.add_cookies([{
                'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d',
                'value': cookie_value,
                'domain': 'hub.weirdhost.xyz', 'path': '/',
                'httpOnly': True, 'secure': True, 'sameSite': 'Lax'
            }])
        
        page = context.new_page()
        page.set_default_timeout(60000)

        try:
            print(f"正在访问控制台: {server_url}")
            page.goto(server_url, wait_until="domcontentloaded")
            
            # 等待 Cloudflare 验证和横幅加载完毕
            print("等待 15 秒让验证框和布局稳定...")
            time.sleep(15) 
            
            # 定位“追加时间”按钮作为坐标锚点
            button = page.locator('button:has-text("시간 추가")')
            button.wait_for(state='visible')
            box = button.bounding_box()
            
            if box:
                print("执行网格轰炸 (12点覆盖计划)...")
                # 以按钮左上角为基准点
                # 根据截图，验证框在按钮上方 45-75px，偏左 15-85px 区域
                for y_offset in [45, 55, 65, 75]:
                    for x_offset in [20, 50, 80]:
                        page.mouse.click(box['x'] + x_offset, box['y'] - y_offset)
                        time.sleep(0.3) # 模拟人类点击间隔
                
                print("轰炸结束，等待验证状态同步...")
                time.sleep(10)
                page.screenshot(path="after_bombing.png")
            
            # 最终尝试点击按钮并验证结果
            if button.is_enabled():
                print("验证疑似通过，点击续期按钮...")
                button.click()
                time.sleep(8)
                
                # 深度验证：检查页面是否出现了“成功”相关韩语文字
                content = page.content()
                if "성공" in content or "Success" in content:
                    print("✅ 确认：续期任务真正成功！")
                    page.screenshot(path="final_success.png")
                    return True
                else:
                    print("⚠️ 警告：按钮已点，但页面未显示成功提示。")
            else:
                print("❌ 错误：网格轰炸未能勾选 CF 盾。")
            
            page.screenshot(path="failed_check.png")
            return False

        except Exception as e:
            print(f"发生异常: {e}")
            page.screenshot(path="error_log.png")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    if not add_server_time():
        exit(1)
