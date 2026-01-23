import os
import time
from playwright.sync_api import sync_playwright

def apply_stealth(page):
    """手动注入特征隐藏，不依赖外部库"""
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    cookie_value = os.environ.get('REMEMBER_WEB_COOKIE')
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            proxy={"server": "socks5://127.0.0.1:40000"}, # 匹配 WARP 代理
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        apply_stealth(page)
        
        if cookie_value:
            context.add_cookies([{
                'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d',
                'value': cookie_value,
                'domain': 'hub.weirdhost.xyz', 'path': '/',
                'httpOnly': True, 'secure': True, 'sameSite': 'Lax'
            }])

        try:
            print(f"访问页面: {server_url}")
            page.goto(server_url, wait_until="domcontentloaded", timeout=60000)
            
            print("等待 15 秒让验证框稳定...")
            time.sleep(15) 
            
            btn = page.locator('button:has-text("시간 추가")')
            btn.wait_for(state='visible')
            box = btn.bounding_box()
            
            if box:
                # 网格轰炸 6.0：根据 failed_check.png 修正，中心在左侧
                print("执行网格轰炸 (地毯式点击复选框方块)...")
                # X轴针对复选框方框，Y轴针对复选框高度
                x_targets = [box['x'] + 22, box['x'] + 32, box['x'] + 42]
                y_targets = [box['y'] - 55, box['y'] - 60, box['y'] - 65, box['y'] - 70]
                
                # 模拟鼠标移动后再点击
                page.mouse.move(box['x'] + 32, box['y'] - 62)
                time.sleep(0.5)

                for ty in y_targets:
                    for tx in x_targets:
                        page.mouse.click(tx, ty)
                        time.sleep(0.1) 
                
                print("点击完成，预留 20 秒让验证状态回传...")
                time.sleep(20) 
                page.screenshot(path="after_bombing.png")

            print("尝试最终点击续期按钮...")
            btn.click()
            time.sleep(10)
            
            # 真实性校验
            content = page.content()
            if "성공" in content or "Success" in content:
                print("✅ 任务真正成功！服务器时长已更新。")
                page.screenshot(path="final_success.png")
                return True
            else:
                print("⚠️ 警告：点击已执行，但未检测到成功关键字。")
                page.screenshot(path="failed_check.png")
                return False

        except Exception as e:
            print(f"脚本执行异常: {e}")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    if not add_server_time():
        exit(1)
