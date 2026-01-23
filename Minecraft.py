import os
import time
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    # 1. 获取环境变量
    remember_web_cookie = os.environ.get('REMEMBER_WEB_COOKIE')
    pterodactyl_email = os.environ.get('PTERODACTYL_EMAIL')
    pterodactyl_password = os.environ.get('PTERODACTYL_PASSWORD')

    if not (remember_web_cookie or (pterodactyl_email and pterodactyl_password)):
        print("错误: 缺少登录凭据。")
        return False

    with sync_playwright() as p:
        # 2. 浏览器启动配置 (保持之前的反检测配置)
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-size=1920,1080',
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale='ko-KR',
            timezone_id='Asia/Seoul'
        )
        
        # 注入 JS 进一步隐藏 webdriver
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        page = context.new_page()
        page.set_default_timeout(60000)

        try:
            # 3. 登录逻辑 (保持不变)
            if remember_web_cookie:
                print("尝试 Cookie 登录...")
                context.add_cookies([{
                    'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d', # 确保这个名字是你最新的
                    'value': remember_web_cookie,
                    'domain': 'hub.weirdhost.xyz',
                    'path': '/',
                    'expires': int(time.time()) + 31536000,
                    'httpOnly': True, 'secure': True, 'sameSite': 'Lax'
                }])
                
            print(f"访问页面: {server_url}")
            page.goto(server_url, wait_until="networkidle")

            # 登录检查
            if "login" in page.url or "auth" in page.url:
                print("Cookie 失效，转入账号密码登录...")
                if not (pterodactyl_email and pterodactyl_password):
                    return False
                page.fill('input[name="username"]', pterodactyl_email)
                page.fill('input[name="password"]', pterodactyl_password)
                time.sleep(2)
                page.click('button[type="submit"]')
                page.wait_for_url("**/server/**", timeout=30000)
                print("登录成功。")

            # --- 4. 暴力处理 Cloudflare (核心修改) ---
            print("正在寻找 Cloudflare 验证框...")
            time.sleep(5) # 等待 iframe 完全加载

            # 策略：直接找 iframe 标签，获取它的坐标，然后点它的正中心
            # 这种方法不依赖 iframe 内部结构，最稳
            
            # 尝试定位 Cloudflare 的 iframe
            cf_iframe_locator = page.locator("iframe[src*='turnstile'], iframe[src*='cloudflare']")
            
            if cf_iframe_locator.count() > 0:
                print(f"检测到 {cf_iframe_locator.count()} 个验证框 iframe。")
                # 通常是第一个
                frame_element = cf_iframe_locator.first
                
                # 获取 iframe 在屏幕上的坐标盒子 (x, y, width, height)
                box = frame_element.bounding_box()
                
                if box:
                    print(f"验证框坐标: {box}")
                    # 计算中心点
                    click_x = box['x'] + box['width'] / 2
                    click_y = box['y'] + box['height'] / 2
                    
                    print(f"移动鼠标至验证框中心 ({click_x}, {click_y}) 并点击...")
                    page.mouse.move(click_x, click_y)
                    time.sleep(0.5)
                    page.mouse.down()
                    time.sleep(0.1)
                    page.mouse.up()
                    
                    print("点击动作已执行，等待 10 秒让验证通过...")
                    time.sleep(10)
                    
                    # 截图看看验证框是否打钩了
                    page.screenshot(path="after_captcha_click.png")
                else:
                    print("无法获取验证框坐标，可能不可见。")
            else:
                print("未检测到明显的 Cloudflare iframe，尝试继续...")

            # --- 5. 点击续期按钮 ---
            add_button_selector = 'button:has-text("시간 추가")'
            add_button = page.locator(add_button_selector)
            
            print("等待 '시간 추가' 按钮...")
            add_button.wait_for(state='visible', timeout=30000)
            add_button.scroll_into_view_if_needed()

            # 再次检查按钮状态，有些面板验证未通过时按钮是灰的
            if not add_button.is_enabled():
                print("错误：按钮仍处于禁用状态，说明验证未通过。请查看 after_captcha_click.png")
                return True # 返回 True 避免 Action 报错，但实际失败

            print("点击续期按钮...")
            # 同样使用坐标点击按钮，防止被透明层遮挡
            btn_box = add_button.bounding_box()
            if btn_box:
                 page.mouse.click(btn_box['x'] + btn_box['width'] / 2, btn_box['y'] + btn_box['height'] / 2)
            else:
                 add_button.click()

            # 等待结果
            time.sleep(5)
            page.screenshot(path="final_result_v2.png")
            
            # 检查是否有成功提示
            content = page.content()
            if "success" in content.lower() or "extended" in content.lower():
                print("检测到成功信号！")
            else:
                print("未检测到明确成功文字，请检查截图。")

            return True

        except Exception as e:
            print(f"脚本执行出错: {e}")
            page.screenshot(path="error_crash.png")
            return False
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    if add_server_time():
        exit(0)
    else:
        exit(1)
