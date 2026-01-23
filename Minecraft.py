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
        # 2. 浏览器启动配置 (隐身模式)
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
        
        # 注入 JS 隐藏 webdriver 特征
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
                    'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d', # 确保此处是你最新的 Cookie Name
                    'value': remember_web_cookie,
                    'domain': 'hub.weirdhost.xyz',
                    'path': '/',
                    'expires': int(time.time()) + 31536000,
                    'httpOnly': True, 'secure': True, 'sameSite': 'Lax'
                }])
                
            print(f"访问页面: {server_url}")
            page.goto(server_url, wait_until="networkidle")

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

            # --- 4. 核心修改：使用键盘 TAB 键定位 Cloudflare ---
            # 这种方法不受页面广告加载导致的布局位移影响
            
            # 定位目标按钮
            add_button_selector = 'button:has-text("시간 추가")'
            print("等待 '시간 추가' 按钮加载...")
            add_button = page.locator(add_button_selector)
            add_button.wait_for(state='visible', timeout=30000)
            
            # 滚动到底部，确保元素都在视口内
            add_button.scroll_into_view_if_needed()
            time.sleep(2) # 等待页面滚动稳定

            print("策略：聚焦按钮 -> Shift+Tab 反向跳到验证框 -> 空格键激活")
            
            # 1. 聚焦到 "시간 추가" 按钮 (但不点击)
            add_button.focus()
            time.sleep(0.5)
            
            # 2. 按 Shift + Tab (焦点倒退，理论上会跳到上方的 Cloudflare 框)
            # 我们多按几次确保跳进去，通常 1 次或 2 次
            page.keyboard.press("Shift+Tab")
            time.sleep(0.5)
            
            # 3. 按空格键 (Space) 激活当前焦点 (即勾选验证框)
            print("尝试激活验证框...")
            page.keyboard.press("Space")
            
            # 备用方案：万一它是跳两次，我们可以再尝试一次循环
            # 但通常 Cloudflare 就在提交按钮的正上方，一次 Shift+Tab 就够了
            
            print("已发送激活指令，等待 10 秒让 Cloudflare 反应...")
            time.sleep(10)
            page.screenshot(path="after_tab_check.png") # 截图查看是否打钩

            # --- 5. 点击续期按钮 ---
            # 检查按钮状态
            if not add_button.is_enabled():
                print("按钮仍禁用，尝试再次 Tab 激活...")
                # 如果失败，可能是焦点没对准，尝试暴力 Tab 遍历
                # 重置焦点到按钮
                add_button.focus()
                # 连续反向 Tab 寻找
                for _ in range(3):
                    page.keyboard.press("Shift+Tab")
                    time.sleep(0.2)
                    page.keyboard.press("Space")
                    time.sleep(1)
                time.sleep(5)
            
            if add_button.is_enabled():
                print("按钮已启用，准备点击续期...")
                add_button.click()
                
                # 等待成功反馈
                time.sleep(5)
                page.screenshot(path="final_success.png")
                
                # 验证页面文字
                content = page.content()
                if "success" in content.lower() or "extended" in content.lower():
                    print("检测到成功信号！")
                    return True
                else:
                    print("点击完成，请检查 final_success.png 确认结果。")
                    return True
            else:
                print("错误：验证框未能通过，按钮依然禁用。")
                return False

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
