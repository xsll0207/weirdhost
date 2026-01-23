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
            print(f"正在访问控制台: {server_url}")
            page.goto(server_url, wait_until="domcontentloaded", timeout=60000)
            
            # 检查是否被重定向到登录页 (说明 Cookie 失效)
            if "login" in page.url or "auth" in page.url:
                print("⚠️ 错误: 发现登录重定向，请更新你的 REMEMBER_WEB_COOKIE！")
                page.screenshot(path="login_redirect.png")
                return False

            # 等待布局稳定
            time.sleep(15) 
            page.screenshot(path="pre_detect.png")

            print("正在搜寻验证码容器...")
            # 尝试多种选择器：title 是最标准的，iframe 是通用的
            selectors = [
                'iframe[title*="challenge"]',
                'iframe[src*="cloudflare"]',
                'div#cf-turnstile iframe',
                'iframe' # 最后的保底方案
            ]
            
            target_iframe = None
            for selector in selectors:
                try:
                    target_iframe = page.wait_for_selector(selector, timeout=5000)
                    if target_iframe:
                        print(f"成功通过选择器 [{selector}] 找到验证框")
                        break
                except:
                    continue

            if not target_iframe:
                print("❌ 无法定位验证框，可能是网络加载失败。")
                return False

            box = target_iframe.bounding_box()
            if box:
                print(f"验证框坐标: x={box['x']}, y={box['y']}, w={box['width']}, h={box['height']}")
                # 针对左侧方块的精准打击
                # 复选框通常在 iframe 的左侧 1/6 处
                target_x = box['x'] + 30
                target_y = box['y'] + (box['height'] / 2)
                
                print("执行网格打击 + Tab 补法...")
                # 1. 模拟鼠标微扰点击
                for i in range(5):
                    page.mouse.click(target_x + (i*2), target_y + (i*2))
                    time.sleep(0.1)
                
                # 2. 模拟键盘交互 (CF 盾对 Tab+Space 响应度很高)
                page.keyboard.press("Tab")
                time.sleep(0.5)
                page.keyboard.press("Space")
                
                print("等待验证状态反馈 (20秒)...")
                time.sleep(20)
                page.screenshot(path="after_bombing.png")

            # 最终尝试点击追加按钮
            btn = page.locator('button:has-text("시간 추가")')
            if btn.is_visible():
                btn.click()
                print("已点击追加按钮，等待后端响应...")
                time.sleep(10)
            
            content = page.content()
            if "성공" in content or "Success" in content:
                print("✅ 任务真正成功！")
                page.screenshot(path="final_success.png")
                return True
            else:
                print("⚠️ 警告：任务未显示成功，请检查 screenshots。")
                page.screenshot(path="failed_at_last.png")
                return False

        except Exception as e:
            print(f"运行异常: {e}")
            page.screenshot(path="error.png")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    if not add_server_time():
        exit(1)
