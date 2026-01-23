import os
import time
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    # --- 1. 获取环境变量 ---
    remember_web_cookie = os.environ.get('REMEMBER_WEB_COOKIE')
    pterodactyl_email = os.environ.get('PTERODACTYL_EMAIL')
    pterodactyl_password = os.environ.get('PTERODACTYL_PASSWORD')

    if not (remember_web_cookie or (pterodactyl_email and pterodactyl_password)):
        print("错误: 缺少登录凭据。")
        return False

    with sync_playwright() as p:
        # --- 2. 浏览器启动配置 (核心修改：反检测) ---
        # 使用 args 隐藏 WebDriver 特征，这是绕过 Cloudflare 的关键
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled', # 禁用自动化控制特性
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-size=1920,1080',
            ]
        )
        
        # 创建上下文时设置更真实的 User-Agent 和视口
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale='ko-KR', # 设置为韩语环境，与服务器匹配
            timezone_id='Asia/Seoul'
        )
        
        # 注入 JS 脚本进一步隐藏 webdriver 属性
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = context.new_page()
        page.set_default_timeout(60000)

        try:
            # --- 3. 登录逻辑 (保持不变，已验证有效) ---
            if remember_web_cookie:
                print("尝试 Cookie 登录...")
                context.add_cookies([{
                    'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d', # 替换为你实际的 Cookie Name
                    'value': remember_web_cookie,
                    'domain': 'hub.weirdhost.xyz',
                    'path': '/',
                    'expires': int(time.time()) + 31536000,
                    'httpOnly': True, 'secure': True, 'sameSite': 'Lax'
                }])
                
            # 无论是否设置 Cookie，都直接访问目标页面，如果 Cookie 失效会自动跳登录页
            print(f"访问页面: {server_url}")
            page.goto(server_url, wait_until="networkidle") # 等待网络空闲，确保 CF 加载完

            # 如果掉到了登录页，执行登录
            if "login" in page.url or "auth" in page.url:
                print("Cookie 失效或未设置，执行账号密码登录...")
                if not (pterodactyl_email and pterodactyl_password):
                    print("无账号密码，无法继续。")
                    return False
                
                page.fill('input[name="username"]', pterodactyl_email)
                page.fill('input[name="password"]', pterodactyl_password)
                # 随机延迟，模拟真人
                time.sleep(random.uniform(1, 3)) 
                page.click('button[type="submit"]')
                page.wait_for_url("**/server/**", timeout=30000)
                print("登录成功，进入服务器页面。")

            # --- 4. 核心修改：处理 Cloudflare 验证 ---
            # 检查页面上是否存在 iframe (Cloudflare 通常在 iframe 里)
            print("检查是否存在 Cloudflare 验证框...")
            
            # 等待几秒让 CF 脚本加载
            time.sleep(5) 
            
            # 尝试查找 Cloudflare Turnstile iframe
            # 这里的逻辑是寻找包含 cloudflare 或 turnstile 的 iframe
            cf_frames = page.frames
            cf_found = False
            for frame in cf_frames:
                if "cloudflare" in frame.url or "turnstile" in frame.url:
                    print(f"发现 Cloudflare iframe: {frame.url}")
                    try:
                        # 尝试点击 iframe 内部的 body 或 checkbox
                        # Cloudflare 验证通常只需要点击一下 iframe 区域
                        box = frame.locator("body")
                        if box.count() > 0:
                            print("尝试点击 Cloudflare 验证框...")
                            box.hover()
                            time.sleep(0.5)
                            box.click()
                            cf_found = True
                            time.sleep(5) # 点击后等待验证通过
                    except Exception as e:
                        print(f"尝试点击验证框失败: {e}")
            
            if not cf_found:
                # 如果没找到 iframe，尝试直接在页面找 checkbox 元素 (备用方案)
                try:
                    cf_checkbox = page.locator("iframe[src*='challenges']").content_frame.locator("body")
                    if cf_checkbox.count() > 0:
                        print("通过选择器找到 Cloudflare，点击...")
                        cf_checkbox.click()
                        time.sleep(5)
                except:
                    print("未检测到显式的 Cloudflare 阻挡，或者已经自动通过。继续尝试点击按钮。")

            # --- 5. 点击续期按钮 ---
            add_button_selector = 'button:has-text("시간 추가")'
            print("寻找续期按钮...")
            
            add_button = page.locator(add_button_selector)
            add_button.wait_for(state='visible', timeout=30000)

            # 再次检查是否禁用
            if not add_button.is_enabled():
                print("按钮处于禁用状态(Disabled)。可能验证未通过，或未到续期时间。")
                page.screenshot(path="button_disabled_final.png")
                # 依然尝试点一下 Cloudflare，万一它刚刚才加载出来
                return True

            add_button.scroll_into_view_if_needed()
            
            # 模拟鼠标移动到按钮上
            add_button.hover()
            time.sleep(random.uniform(0.5, 1.5))
            
            print("点击 '시간 추가' 按钮...")
            add_button.click()
            
            # 等待反应
            time.sleep(5)
            
            # 最终截图
            page.screenshot(path="final_result.png")
            print("操作完成，请检查截图确认结果。")
            
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
