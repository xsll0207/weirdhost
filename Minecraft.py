import os
import time
from playwright.sync_api import sync_playwright

# --- 动态导入修复方案 ---
try:
    import playwright_stealth
    # 定义一个统一的调用函数
    def apply_stealth(page):
        if hasattr(playwright_stealth, 'stealth_sync'):
            playwright_stealth.stealth_sync(page)
        elif hasattr(playwright_stealth, 'stealth'):
            # 如果 stealth 是个模块，尝试调用里面的函数
            if callable(playwright_stealth.stealth):
                playwright_stealth.stealth(page)
            else:
                playwright_stealth.stealth.stealth(page)
        print("Stealth 隐身特征已注入")
except Exception as e:
    print(f"Stealth 注入跳过 (非致命错误): {e}")
    def apply_stealth(page): pass

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
        # 调用修复后的隐身函数
        apply_stealth(page)
        
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
            
            print("等待 15 秒让验证框稳定...")
            time.sleep(15) 
            
            # 定位续期按钮作为锚点
            button = page.locator('button:has-text("시간 추가")')
            button.wait_for(state='visible')
            box = button.bounding_box()
            
            if box:
                # 网格轰炸 3.3：进一步向左修正坐标
                print("执行网格轰炸 3.3 (精准覆盖左侧方框)...")
                # 按钮左边缘是 box['x']。复选框在左侧，通常位于 x+20 到 x+50 之间
                x_targets = [box['x'] + 22, box['x'] + 32, box['x'] + 42, box['x'] + 52]
                # 纵向高度覆盖 45px 到 70px
                y_targets = [box['y'] - 52, box['y'] - 58, box['y'] - 64, box['y'] - 70]
                
                for ty in y_targets:
                    for tx in x_targets:
                        page.mouse.click(tx, ty)
                        time.sleep(0.1) 
                
                print("点击完成，等待 15 秒观察是否打钩...")
                time.sleep(15) 
                page.screenshot(path="after_bombing.png")

            # 最终确认逻辑
            print("尝试最终续期点击...")
            button.click()
            time.sleep(10)
            
            content = page.content()
            if "성공" in content or "Success" in content:
                print("✅ 确认成功：服务器时长已增加！")
                page.screenshot(path="final_success.png")
                return True
            else:
                print("⚠️ 警告：续期未检测到成功文字，请检查 after_bombing.png")
                page.screenshot(path="failed_check.png")
                return False

        except Exception as e:
            print(f"脚本异常: {e}")
            page.screenshot(path="error.png")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    if not add_server_time():
        exit(1)
