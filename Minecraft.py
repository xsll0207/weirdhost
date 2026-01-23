import os
import time
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    cookie_value = os.environ.get('REMEMBER_WEB_COOKIE')
    
    with sync_playwright() as p:
        # 1. 启动浏览器并开启隐身模式
        browser = p.chromium.launch(
            headless=True,
            proxy={"server": "socks5://127.0.0.1:40000"},
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        # 开启 Stealth 绕过检测
        page = context.new_page()
        stealth_sync(page)
        
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
            
            # 等待渲染，特别是 CF 盾
            print("等待 15 秒让验证框稳定...")
            time.sleep(15) 
            
            # 定位续期按钮作为锚点
            button = page.locator('button:has-text("시간 추가")')
            button.wait_for(state='visible')
            box = button.bounding_box()
            
            if box:
                print("执行网格轰炸 3.0 (针对左侧复选框)...")
                # 重新校准坐标：针对按钮左侧上方区域地毯式搜索
                # 复选框中心大约在按钮左边缘起 20-40px，上方 55-65px 处
                x_targets = [box['x'] + 20, box['x'] + 30, box['x'] + 40, box['x'] + 55]
                y_targets = [box['y'] - 55, box['y'] - 60, box['y'] - 65]
                
                for ty in y_targets:
                    for tx in x_targets:
                        page.mouse.click(tx, ty)
                        time.sleep(0.1) # 快速小碎步点击
                
                print("点击完成，预留较长等待时间让验证生效...")
                time.sleep(12)
                page.screenshot(path="after_bombing.png")

            # 真正的校验逻辑：检查按钮点击后是否有成功反馈
            print("尝试点击续期按钮...")
            button.click()
            time.sleep(8)
            
            # 检查页面文字是否变化 (WeirdHost 成功后通常会弹出 SweetAlert 或刷新内容)
            content = page.content()
            # 检查韩语“成功”关键字或时间变化
            if "성공" in content or "Success" in content or "성공적으로" in content:
                print("✅ 确认成功：服务器时长已增加！")
                page.screenshot(path="final_success.png")
                return True
            else:
                # 如果没检测到成功文字，说明之前的点击没点中复选框
                print("⚠️ 警告：点击了按钮但未检测到续期成功。")
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
