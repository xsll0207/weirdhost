import os
import time
from playwright.sync_api import sync_playwright

def apply_stealth(page):
    """注入特征隐藏 JS"""
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
            print(f"访问页面: {server_url}")
            page.goto(server_url, wait_until="domcontentloaded", timeout=60000)
            
            # 增加等待时间，应对 WARP 代理的波动
            print("等待页面深度加载 (20秒)...")
            time.sleep(20) 
            page.screenshot(path="pre_detect.png")

            print("正在扫描所有 Iframe...")
            target_iframe = None
            
            # 策略：遍历页面上所有的 iframe，寻找符合验证框尺寸特征的那个
            all_iframes = page.query_selector_all('iframe')
            for f in all_iframes:
                try:
                    box = f.bounding_box()
                    # Cloudflare Turnstile 验证框通常宽度在 280-310px，高度在 60-70px
                    if box and 250 < box['width'] < 350 and 50 < box['height'] < 100:
                        target_iframe = f
                        print(f"通过尺寸特征匹配到验证框: w={box['width']}, h={box['height']}")
                        break
                except:
                    continue

            if not target_iframe:
                print("❌ 自动探测失败，尝试使用通用选择器...")
                try:
                    target_iframe = page.wait_for_selector('iframe[title*="Widget"], iframe[src*="challenges"]', timeout=10000)
                except:
                    print("❌ 彻底无法定位验证框。")
                    return False

            box = target_iframe.bounding_box()
            if box:
                # 坐标再校准:
                # 之前点在 30px 处太靠边，点在按钮中心又太靠右。
                # 复选框小方块中心在 iframe 左边缘起 40-45 像素位置。
                target_x = box['x'] + 42 
                target_y = box['y'] + (box['height'] / 2)
                
                print(f"执行精准打击: ({target_x}, {target_y})")
                # 模拟鼠标微小抖动连点，确保触发表单
                for move in [-2, 0, 2]:
                    page.mouse.click(target_x + move, target_y + move)
                    time.sleep(0.1)
                
                # 补一个键盘操作
                page.keyboard.press("Tab")
                time.sleep(0.5)
                page.keyboard.press("Space")
                
                print("等待验证同步...")
                time.sleep(20)
                page.screenshot(path="after_bombing.png")

            # 最终点击追加按钮
            btn = page.locator('button:has-text("시간 추가")')
            if btn.is_visible():
                btn.click()
                time.sleep(10)
            
            content = page.content()
            if "성공" in content or "Success" in content:
                print("✅ 任务真正成功！")
                page.screenshot(path="final_success.png")
                return True
            else:
                print("⚠️ 警告：未检测到成功提示。")
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
