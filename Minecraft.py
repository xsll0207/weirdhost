import os
import time
from playwright.sync_api import sync_playwright

def apply_stealth(page):
    """手动注入特征隐藏 JS"""
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    cookie_value = os.environ.get('REMEMBER_WEB_COOKIE')
    
    with sync_playwright() as p:
        # 1. 设置高清分辨率，确保元素不重叠
        browser = p.chromium.launch(
            headless=True,
            proxy={"server": "socks5://127.0.0.1:40000"},
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox', '--window-size=1920,1080']
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
            
            # --- 关键改进：强制滚动到底部以触发渲染 ---
            print("强制滚动到底部以加载验证码...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(5)
            # 再次寻找“服务器续期”标题并确保它在中心
            card = page.locator('text=서버 연장')
            if card.is_visible():
                card.scroll_into_view_if_needed()
            
            print("等待 20 秒让验证码稳定渲染...")
            time.sleep(20) 
            page.screenshot(path="pre_detect_scrolled.png") # 这张图应该能看到 CF 框了

            print("开始全框架扫描探测...")
            target_frame_element = None
            
            # 策略：寻找具有特定尺寸特征的框架
            for frame in page.frames:
                # Cloudflare Turnstile 通常 URL 包含 challenges 或宽度在 300 左右
                if "challenges" in frame.url or "cloudflare" in frame.url:
                    try:
                        target_frame_element = frame.frame_element()
                        print(f"锁定 CF 框架: {frame.url[:50]}...")
                        break
                    except:
                        continue

            if not target_frame_element:
                print("❌ 深度探测失败，尝试使用容器坐标定位...")
                # 如果找不到 iframe，就根据“时间追加”按钮反向推算位置
                btn = page.locator('button:has-text("시간 추가")')
                if btn.is_visible():
                    box = btn.bounding_box()
                    # 验证框就在按钮的正上方约 65 像素处
                    target_x = box['x'] + 40
                    target_y = box['y'] - 65
                else:
                    print("❌ 页面加载不完整，无法找到按钮锚点。")
                    return False
            else:
                box = target_frame_element.bounding_box()
                target_x = box['x'] + 40
                target_y = box['y'] + (box['height'] / 2)

            if target_x and target_y:
                print(f"执行地毯式点击: ({target_x}, {target_y})")
                # 在目标点周围 10 像素范围内进行 5x3 的密集网格点击
                for dx in [-15, -10, -5, 0, 5, 10]:
                    for dy in [-5, 0, 5]:
                        page.mouse.click(target_x + dx, target_y + dy)
                        time.sleep(0.1)
                
                # 键盘补丁：按 Tab 锁定焦点再按空格
                page.keyboard.press("Tab")
                time.sleep(0.5)
                page.keyboard.press("Space")
                
                print("点击完成，等待验证同步 (25秒)...")
                time.sleep(25) 
                page.screenshot(path="after_bombing.png")

            # 最终确认续期
            btn = page.locator('button:has-text("시간 추가")')
            if btn.is_visible():
                print("尝试点击续期按钮...")
                btn.click()
                time.sleep(10)
            
            content = page.content()
            if "성공" in content or "Success" in content:
                print("✅ 任务最终成功！服务器时长已增加。")
                page.screenshot(path="final_success.png")
                return True
            else:
                print("⚠️ 警告：点击已执行，但未检测到成功。请检查 after_bombing.png。")
                page.screenshot(path="failed_at_last.png")
                return False

        except Exception as e:
            print(f"发生异常: {e}")
            page.screenshot(path="error.png")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    if not add_server_time():
        exit(1)
