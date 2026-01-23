import os
import time
from playwright.sync_api import sync_playwright
# 修正导入名称
from playwright_stealth import stealth

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    cookie_value = os.environ.get('REMEMBER_WEB_COOKIE')
    
    with sync_playwright() as p:
        # 1. 启动浏览器
        browser = p.chromium.launch(
            headless=True,
            proxy={"server": "socks5://127.0.0.1:40000"},
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = context.new_page()
        # 修正调用：使用 stealth(page) 隐藏自动化特征
        stealth(page)
        
        if cookie_value:
            context.add_cookies([{
                'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d',
                'value': cookie_value,
                'domain': 'hub.weirdhost.xyz', 'path': '/',
                'httpOnly': True, 'secure': True, 'sameSite': 'Lax'
            }])

        try:
            print(f"正在访问控制台: {server_url}")
            page.goto(server_url, wait_until="domcontentloaded", timeout=60000)
            
            # 等待渲染
            print("等待 15 秒让验证框稳定...")
            time.sleep(15) 
            
            # 定位续期按钮作为锚点
            button = page.locator('button:has-text("시간 추가")')
            button.wait_for(state='visible')
            box = button.bounding_box()
            
            if box:
                print("执行网格轰炸 3.1 (精准打击复选框方框)...")
                # 根据 failed_check.png 分析：复选框小方块位于按钮左边缘的正上方
                # 按钮左边缘坐标是 box['x']。方块中心大约在 +25px 左右。
                # 纵向高度在按钮上方 50px 到 70px 之间。
                x_targets = [box['x'] + 20, box['x'] + 30, box['x'] + 40]
                y_targets = [box['y'] - 50, box['y'] - 55, box['y'] - 60, box['y'] - 65]
                
                for ty in y_targets:
                    for tx in x_targets:
                        page.mouse.click(tx, ty)
                        time.sleep(0.1) 
                
                print("点击完成，等待验证生效...")
                time.sleep(15) # 预留更长时间处理 CF 验证
                page.screenshot(path="after_bombing.png")

            # 最终确认逻辑
            print("尝试点击续期按钮...")
            button.click()
            time.sleep(8)
            
            # 检查页面内容确认是否成功
            content = page.content()
            if "성공" in content or "Success" in content or "성공적으로" in content:
                print("✅ 确认成功：服务器时长已增加！")
                page.screenshot(path="final_success.png")
                return True
            else:
                print("⚠️ 警告：虽然点击了按钮，但未检测到续期成功。")
                page.screenshot(path="failed_check.png")
                return False

        except Exception as e:
            print(f"脚本执行异常: {e}")
            page.screenshot(path="error.png")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    if not add_server_time():
        exit(1)
