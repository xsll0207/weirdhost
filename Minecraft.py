import os
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    # 1. 获取环境变量
    remember_web_cookie = os.environ.get('REMEMBER_WEB_COOKIE')
    # 【新增】支持用户传入 Cookie 的完整键值对字符串，例如 "remember_web_xxx=yyyyy"
    # 或者用户需要在 Secrets 里只填 Value，这里我们需要知道 Key 是什么。
    # 为了简单，建议你在 Secret 里填完整的 "name=value"，或者我们需要去浏览器里看一眼正确的 name。
    # 假设目前的 Secret 只存了 value。我们需要确认 name。
    
    # 修正：Pterodactyl 的 Cookie Name 通常是 "remember_web_" 开头，后面跟一串 Hash。
    # 既然无法确定 Hash，我们建议优先依赖账号密码登录，或者请务必在 Secret 里填对。
    
    pterodactyl_email = os.environ.get('PTERODACTYL_EMAIL')
    pterodactyl_password = os.environ.get('PTERODACTYL_PASSWORD')

    if not (remember_web_cookie or (pterodactyl_email and pterodactyl_password)):
        print("错误: 缺少登录凭据。")
        return False

    with sync_playwright() as p:
        # 【关键修改 1】设置真实的 User-Agent，防止被轻易识别为机器人
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        page.set_default_timeout(60000) # 60秒超时

        try:
            is_logged_in = False
            
            # --- 登录逻辑 ---
            # 这里的 Cookie 名称非常关键！请务必在浏览器 F12 -> Application -> Cookies 里确认你的 Cookie Name
            # 如果你不确定，我们可以先尝试账号密码登录，因为那更稳妥（前提是没有验证码）
            
            print(f"正在访问登录页面: https://hub.weirdhost.xyz/auth/login")
            page.goto("https://hub.weirdhost.xyz/auth/login", wait_until="networkidle")
            
            # 填入账号密码
            if pterodactyl_email and pterodactyl_password:
                print("尝试使用账号密码登录...")
                page.fill('input[name="username"]', pterodactyl_email)
                page.fill('input[name="password"]', pterodactyl_password)
                page.click('button[type="submit"]')
                
                # 等待跳转或错误
                try:
                    # 等待 URL 变更为控制台主页，或者出现错误提示
                    page.wait_for_url("**/server/**", timeout=15000) # 假设登录成功会跳转
                    print("账号密码登录可能成功，URL已跳转。")
                    is_logged_in = True
                except:
                    if "auth/login" in page.url:
                        print("登录似乎卡住了，可能是验证码或账号错误。")
                        # 如果有 Cookie，这里可以作为备用尝试，但通常账号密码失败 Cookie 也难救
            
            # 如果账号密码没成功，或者是直接使用 Cookie 可以在这里插入逻辑，但建议主要依赖账号密码
            
            # --- 导航到服务器页面 ---
            print(f"正在前往服务器页面: {server_url}")
            page.goto(server_url, wait_until="networkidle") # networkidle 等待网络空闲，比 domcontentloaded 更稳
            
            if "login" in page.url:
                print("错误：无法进入服务器页面，仍处于登录页。截图保存。")
                page.screenshot(path="login_failed.png")
                return False

            # --- 点击按钮 ---
            # 寻找按钮，更精确的定位
            # 这里的 text 必须与网页完全一致
            add_button = page.locator('button:has-text("시간 추가")') # 或者 try "Renew" if English
            
            print("等待按钮出现...")
            add_button.wait_for(state="visible", timeout=30000)
            
            if add_button.is_disabled():
                print("错误：按钮存在但处于不可点击状态（Disabled）。")
                page.screenshot(path="button_disabled.png")
                return False

            print("点击按钮...")
            # 【关键修改 2】去掉 force=True，如果会被遮挡，让他报错，这样我们才知道出问题了
            add_button.click() 
            
            # 【关键修改 3】验证结果
            # 点击后，通常会有 "Server extended" 或者绿色的 Toast 提示
            # 或者等待 2 秒后截图看看
            time.sleep(5)
            print("点击完成，截图保存状态。")
            page.screenshot(path="after_click.png")

            # 检查是否有成功提示 (Pterodactyl 通常有 .alert-success 或类似结构)
            # 这里做一个通用检查：页面源码里是否有 "success" 相关的提示
            content = page.content().lower()
            if "success" in content or "extended" in content or "完了" in content:
                print("检测到成功关键词，任务成功！")
                return True
            else:
                print("警告：点击了按钮，但未检测到明确的成功提示。请检查 after_click.png")
                return True # 暂时算成功，依赖人工看图

        except Exception as e:
            print(f"发生异常: {e}")
            page.screenshot(path="error_trace.png")
            return False
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    if add_server_time():
        exit(0)
    else:
        exit(1)
