import os
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    """
    尝试登录 hub.weirdhost.xyz 并点击 "시간 추가" 按钮。
    优先使用 REMEMBER_WEB_COOKIE 进行会话登录，如果不存在则回退到邮箱密码登录。
    """
    # 从环境变量获取登录凭据
    remember_web_cookie = os.environ.get('REMEMBER_WEB_COOKIE')
    pterodactyl_email = os.environ.get('PTERODACTYL_EMAIL')
    pterodactyl_password = os.environ.get('PTERODACTYL_PASSWORD')

    # 检查是否提供了任何登录凭据
    if not (remember_web_cookie or (pterodactyl_email and pterodactyl_password)):
        print("错误: 缺少登录凭据。请设置 REMEMBER_WEB_COOKIE 或 PTERODACTYL_EMAIL 和 PTERODACTYL_PASSWORD 环境变量。")
        return False

    with sync_playwright() as p:
        # 在 GitHub Actions 中，使用 headless 无头模式运行
        # 添加 User-Agent 伪装，防止被部分防火墙直接判定为脚本
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        # 增加默认超时时间到90秒
        page.set_default_timeout(90000)

        try:
            # --- 方案一：优先尝试使用 Cookie 会话登录 ---
            if remember_web_cookie:
                print("检测到 REMEMBER_WEB_COOKIE，尝试使用 Cookie 登录...")
                session_cookie = {
                    'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d', # 保持你原有的 Cookie Name
                    'value': remember_web_cookie,
                    'domain': 'hub.weirdhost.xyz',
                    'path': '/',
                    'expires': int(time.time()) + 3600 * 24 * 365,
                    'httpOnly': True,
                    'secure': True,
                    'sameSite': 'Lax'
                }
                context.add_cookies([session_cookie])
                print(f"已设置 Cookie。正在访问目标服务器页面: {server_url}")
                
                try:
                    page.goto(server_url, wait_until="domcontentloaded", timeout=90000)
                except PlaywrightTimeoutError:
                    print(f"页面加载超时（90秒）。")
                    page.screenshot(path="goto_timeout_error.png")
                
                # 检查是否因 Cookie 无效被重定向到登录页
                if "login" in page.url or "auth" in page.url:
                    print("Cookie 登录失败或会话已过期，将回退到邮箱密码登录。")
                    context.clear_cookies()
                    remember_web_cookie = None # 标记 Cookie 登录失败
                else:
                    print("Cookie 登录成功，已进入服务器页面。")

            # --- 方案二：如果 Cookie 方案失败或未提供，则使用邮箱密码登录 ---
            if not remember_web_cookie:
                if not (pterodactyl_email and pterodactyl_password):
                    print("错误: Cookie 无效，且未提供 PTERODACTYL_EMAIL 或 PTERODACTYL_PASSWORD。无法登录。")
                    browser.close()
                    return False

                login_url = "https://hub.weirdhost.xyz/auth/login"
                print(f"正在访问登录页面: {login_url}")
                page.goto(login_url, wait_until="domcontentloaded", timeout=90000)

                email_selector = 'input[name="username"]' 
                password_selector = 'input[name="password"]'
                login_button_selector = 'button[type="submit"]'

                print("等待登录表单元素加载...")
                page.wait_for_selector(email_selector)
                page.fill(email_selector, pterodactyl_email)
                page.fill(password_selector, pterodactyl_password)

                print("正在点击登录按钮...")
                with page.expect_navigation(wait_until="domcontentloaded", timeout=60000):
                    page.click(login_button_selector)

                if "login" in page.url or "auth" in page.url:
                    print(f"邮箱密码登录失败，仍停留在登录页。")
                    page.screenshot(path="login_fail_error.png")
                    browser.close()
                    return False
                else:
                    print("邮箱密码登录成功。")

            # --- 确保当前位于正确的服务器页面 ---
            if page.url != server_url:
                print(f"当前不在目标服务器页面，正在导航至: {server_url}")
                page.goto(server_url, wait_until="domcontentloaded", timeout=90000)
                if "login" in page.url:
                    print("导航失败，会话可能已失效。")
                    browser.close()
                    return False

            # --- 核心操作：查找并点击 "시간 추가" 按钮 ---
            # 修改重点：去掉 force 和 position，增加有效性检查
            add_button_selector = 'button:has-text("시간 추가")'
            print(f"正在查找并等待 '{add_button_selector}' 按钮...")

            try:
                add_button = page.locator(add_button_selector)
                
                # 1. 等待按钮加载完毕并可见
                add_button.wait_for(state='visible', timeout=30000)
                
                # 2. 检查按钮是否被禁用（例如：时间未到不可续期）
                if not add_button.is_enabled():
                    print("警告: 按钮可见但处于 '不可点击' (Disabled) 状态。可能是还没到续期时间。")
                    page.screenshot(path="button_disabled.png")
                    # 这里返回 True 视为脚本运行正常，只是没到时间
                    browser.close()
                    return True 
                
                # 3. 滚动到视野内，确保不被遮挡
                add_button.scroll_into_view_if_needed()
                
                # 4. 执行标准点击 (去掉了 force=True，如果被遮挡会报错，而不是假装点成功)
                # 也可以使用 expect_response 来监听网络请求，这里先用最稳妥的点击等待方式
                print("正在点击按钮...")
                add_button.click()
                
                print("点击指令已发送。正在等待服务器响应 (10秒)...")
                time.sleep(10) # 给予服务器足够的时间处理请求

                # 5. 截图以验证结果 (请在 Github Action Artifacts 查看这张图)
                page.screenshot(path="after_click_success.png")
                print("任务完成，已截图保存状态。")
                
                browser.close()
                return True

            except PlaywrightTimeoutError:
                print(f"错误: 在30秒内未找到或 '시간 추가' 按钮不可见。")
                page.screenshot(path="button_not_found.png")
                browser.close()
                return False

        except Exception as e:
            print(f"执行过程中发生未知错误: {e}")
            page.screenshot(path="general_error.png")
            browser.close()
            return False

if __name__ == "__main__":
    print("开始执行添加服务器时间任务...")
    success = add_server_time()
    if success:
        print("任务执行成功。")
        exit(0)
    else:
        print("任务执行失败。")
        exit(1)
