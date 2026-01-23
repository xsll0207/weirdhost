import os
import time
from playwright.sync_api import sync_playwright

def apply_manual_stealth(page):
    """手动注入 JS 以隐藏 Playwright 特征"""
    stealth_js = """
    Object.defineProperty(navigator, 'webdriver', {get: () => False});
    window.chrome = { runtime: {} };
    Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    """
    page.add_init_script(stealth_js)
    # 尝试使用 stealth 库（如果可用）
    try:
        from playwright_stealth import stealth_sync
        stealth_sync(page)
        print("Stealth 库注入成功")
    except:
        print("Stealth 库不可用，已切换为手动 JS 注入")

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    cookie_value = os.environ.get('REMEMBER_WEB_COOKIE')
    
    with sync_playwright() as p:
        # 启动参数优化：进一步伪装成普通浏览器
        browser = p.chromium.launch(
            headless=True,
            proxy={"server": "socks5://127.0.0.1:40000"},
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-infobars',
                '--window-size=1920,1080'
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        apply_manual_stealth(page)
        
        if cookie_value:
            context.add_cookies([{
                'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d',
                'value': cookie_value,
                'domain': 'hub.weirdhost.xyz', 'path': '/',
                'httpOnly': True, 'secure': True, 'sameSite': 'Lax'
            }])

        try:
            print(f"访问页面: {server_url}")
            page.goto(server_url, wait_until="networkidle", timeout=60000)
            
            # 等待 15 秒让 Cloudflare 挑战完全加载
            print("等待验证框加载...")
            time.sleep(15) 
            
            btn = page.locator('button:has-text("시간 추가")')
            btn.wait_for(state='visible')
            box = btn.bounding_box()
            
            if box:
                # 网格轰炸 4.0：加入鼠标移动轨迹模拟
                print("执行模拟人手网格打击...")
                # 针对复选框所在的左侧区域
                x_base = box['x'] + 30
                y_base = box['y'] - 62
                
                # 先把鼠标移动到区域附近，模拟人类寻找动作
                page.mouse.move(x_base, y_base)
                time.sleep(0.5)
                
                # 在 20 像素范围内进行 4x4 密集打击
                for dy in [-8, -3, 3, 8]:
                    for dx in [-10, -5, 5, 10]:
                        page.mouse.click(x_base + dx, y_base + dy)
                        time.sleep(0.1)
                
                print("点击完成，等待 20 秒让 Cloudflare 完成内部验证...")
                time.sleep(20) 
                page.screenshot(path="after_bombing.png")

            # 最终续期点击
            print("点击续期按钮...")
            btn.click()
            time.sleep(10)
            
            # 结果校验
            content = page.content()
            if "성공" in content or "Success" in content:
                print("✅ 任务真正成功！")
                page.screenshot(path="final_success.png")
                return True
            else:
                print("⚠️ 警告：续期失败。可能 CF 盾未打钩。")
                page.screenshot(path="failed_check.png")
                return False

        except Exception as e:
            print(f"运行异常: {e}")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    if not add_server_time():
        exit(1)
