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
            print(f"正在访问: {server_url}")
            page.goto(server_url, wait_until="domcontentloaded", timeout=60000)
            
            # 等待 20 秒，确保 WARP 代理下的缓慢流量也能加载出验证码
            print("正在深度加载页面...")
            time.sleep(20) 
            page.screenshot(path="pre_detect.png")

            print("开始全框架扫描探测...")
            target_frame_element = None
            
            # 策略：直接遍历所有 Frame 寻找包含 Cloudflare 特征的 URL
            for frame in page.frames:
                if "cloudflare" in frame.url or "challenges" in frame.url:
                    try:
                        # 找到对应的 DOM 元素以获取坐标
                        target_frame_element = frame.frame_element()
                        print(f"成功探测到验证框架: {frame.url[:50]}...")
                        break
                    except:
                        continue

            if not target_frame_element:
                print("❌ 自动探测失败，尝试最后的尺寸兜底...")
                for f in page.query_selector_all('iframe'):
                    b = f.bounding_box()
                    if b and 200 < b['width'] < 400:
                        target_frame_element = f
                        break

            if not target_frame_element:
                print("❌ 彻底无法定位验证框。")
                return False

            box = target_frame_element.bounding_box()
            if box:
                # 像素级校准
                # 复选框方格中心约在框架左边缘 +30 到 +45 像素
                # 纵向中心约在高度的 1/2
                target_x = box['x'] + 35
                target_y = box['y'] + (box['height'] / 2)
                
                print(f"执行精准打击: ({target_x}, {target_y})")
                # 模拟鼠标在地毯式覆盖该小方块
                for x_offset in [-5, 0, 5]:
                    for y_offset in [-5, 0, 5]:
                        page.mouse.click(target_x + x_offset, target_y + y_offset)
                        time.sleep(0.1)
                
                # 模拟键盘操作：Tab 到复选框上并按空格
                page.keyboard.press("Tab")
                time.sleep(0.5)
                page.keyboard.press("Space")
                
                print("点击完成，等待验证同步 (20s)...")
                time.sleep(20)
                page.screenshot(path="after_bombing.png")

            # 最终点击追加按钮
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
                print("⚠️ 警告：未检测到成功提示。")
                page.screenshot(path="failed_at_last.png")
                return False

        except Exception as e:
            print(f"运行异常: {e}")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    if not add_server_time():
        exit(1)
