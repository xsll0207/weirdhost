import os
import time
from playwright.sync_api import sync_playwright

def apply_stealth(page):
    """手动注入隐身脚本，绕过自动化检测"""
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    cookie_value = os.environ.get('REMEMBER_WEB_COOKIE')
    
    with sync_playwright() as p:
        # 1. 启动浏览器并强制设置物理窗口大小
        browser = p.chromium.launch(
            headless=True,
            proxy={"server": "socks5://127.0.0.1:40000"},
            args=[
                '--disable-blink-features=AutomationControlled', 
                '--no-sandbox',
                '--window-size=1920,1080' # 强制浏览器窗口分辨率
            ]
        )
        
        # 2. 设置页面视口分辨率
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}, # 确保与窗口大小一致
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
            print(f"正在访问控制台: {server_url}")
            # 增加超时时间，确保 WARP 代理环境下的稳定加载
            page.goto(server_url, wait_until="networkidle", timeout=90000)
            
            # 关键一步：滚动到页面底部，确保 CF 框被触发渲染
            page.mouse.wheel(0, 500)
            print("等待 20 秒让验证码和布局完全稳定...")
            time.sleep(20) 
            page.screenshot(path="pre_detect_high_res.png") # 高清预检截图

            print("开始全框架深度探测...")
            target_frame_element = None
            
            # 遍历所有 Frame，寻找包含 Cloudflare 或 Widget 关键词的框架
            for frame in page.frames:
                if "cloudflare" in frame.url or "challenges" in frame.url:
                    try:
                        target_frame_element = frame.frame_element()
                        print(f"成功锁定验证框架: {frame.url[:60]}...")
                        break
                    except:
                        continue

            if not target_frame_element:
                print("❌ 深度探测失败，尝试最后的保底选择器...")
                target_frame_element = page.query_selector('iframe[title*="Widget"]')

            if target_frame_element:
                box = target_frame_element.bounding_box()
                if box:
                    # 精准坐标校准：针对左侧小方格区域
                    # 在 1920x1080 分辨率下，方格中心约在框架左侧 40px，高度中心
                    target_x = box['x'] + 40
                    target_y = box['y'] + (box['height'] / 2)
                    
                    print(f"执行网格轰炸打击: ({target_x}, {target_y})")
                    # 执行 4x4 密集连点，覆盖复选框所在的所有可能像素
                    for dx in [-10, -5, 0, 5, 10]:
                        for dy in [-5, 0, 5]:
                            page.mouse.click(target_x + dx, target_y + dy)
                            time.sleep(0.1)
                    
                    # 模拟键盘辅助操作
                    page.keyboard.press("Tab")
                    time.sleep(0.5)
                    page.keyboard.press("Space")
                    
                    print("已执行点击，等待 20 秒验证同步...")
                    time.sleep(20)
                    page.screenshot(path="after_bombing_high_res.png")

            # 3. 最终尝试点击续期按钮
            btn = page.locator('button:has-text("시간 추가")')
            if btn.is_visible():
                print("尝试点击续期按钮...")
                btn.click()
                time.sleep(10)
            
            # 4. 结果校验：搜索韩语成功关键字
            content = page.content()
            if "성공" in content or "Success" in content:
                print("✅ 任务最终成功！服务器时长已增加。")
                page.screenshot(path="final_success.png")
                return True
            else:
                print("⚠️ 警告：点击已完成，但未检测到成功提示。")
                page.screenshot(path="failed_at_last.png")
                return False

        except Exception as e:
            print(f"脚本运行中发生错误: {e}")
            page.screenshot(path="error_trace.png")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    if not add_server_time():
        exit(1)
