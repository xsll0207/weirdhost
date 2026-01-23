import os
import time
from playwright.sync_api import sync_playwright

def apply_stealth(page):
    """手动注入 JS 隐藏机器人特征"""
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    cookie_value = os.environ.get('REMEMBER_WEB_COOKIE')
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            proxy={"server": "socks5://127.0.0.1:40000"},
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
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
            print(f"正在访问: {server_url}")
            page.goto(server_url, wait_until="networkidle", timeout=60000)
            time.sleep(15) 

            # --- 核心改进：直接定位 iframe 而非按钮 ---
            print("正在搜寻 Cloudflare 验证框...")
            # 找到包含 cloudflare 的 iframe
            cf_iframe = page.wait_for_selector('iframe[src*="cloudflare"]', timeout=30000)
            
            if cf_iframe:
                box = cf_iframe.bounding_box()
                if box:
                    print(f"检测到验证框位置: x={box['x']}, y={box['y']}")
                    # 精准打击：复选框在 iframe 左侧约 30 像素处
                    target_x = box['x'] + 30
                    target_y = box['y'] + (box['height'] / 2)
                    
                    # 方案 A: 模拟鼠标网格打击 (针对最左侧方块)
                    for offset in [-5, 0, 5]:
                        page.mouse.click(target_x + offset, target_y + offset)
                        time.sleep(0.2)
                    
                    # 方案 B: 键盘操作补法 (Tab 到复选框上按空格，这是无视坐标的)
                    page.keyboard.press("Tab")
                    time.sleep(0.5)
                    page.keyboard.press("Space")
                    
                    print("已执行点击与键盘复合操作，等待验证...")
                    time.sleep(20) 
                    page.screenshot(path="after_bombing.png")

            # 执行最终续期按钮点击
            btn = page.locator('button:has-text("시간 추가")')
            if btn.is_visible():
                btn.click()
                time.sleep(10)
            
            # 校验结果
            content = page.content()
            if "성공" in content or "Success" in content:
                print("✅ 任务最终成功！")
                page.screenshot(path="final_success.png")
                return True
            else:
                print("⚠️ 提示：点击已完成，但未检测到成功提示。")
                page.screenshot(path="failed_final.png")
                return False

        except Exception as e:
            print(f"脚本异常: {e}")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    if not add_server_time():
        exit(1)
