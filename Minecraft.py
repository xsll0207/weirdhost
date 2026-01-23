import os
import time
import random
from playwright.sync_api import sync_playwright

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    remember_web_cookie = os.environ.get('REMEMBER_WEB_COOKIE')
    pterodactyl_email = os.environ.get('PTERODACTYL_EMAIL')
    pterodactyl_password = os.environ.get('PTERODACTYL_PASSWORD')

    if not (remember_web_cookie or (pterodactyl_email and pterodactyl_password)):
        print("错误: 缺少登录凭据。")
        return False

    with sync_playwright() as p:
        # 1. 启动浏览器 (配置反检测)
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--window-size=1920,1080',
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale='ko-KR',
            timezone_id='Asia/Seoul'
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

        page = context.new_page()
        page.set_default_timeout(60000)

        try:
            # 2. 登录
            if remember_web_cookie:
                context.add_cookies([{
                    'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d', # 确保此处是你最新的 Cookie Name
                    'value': remember_web_cookie,
                    'domain': 'hub.weirdhost.xyz',
                    'path': '/',
                    'expires': int(time.time()) + 31536000,
                    'httpOnly': True, 'secure': True, 'sameSite': 'Lax'
                }])
                
            print(f"访问: {server_url}")
            page.goto(server_url, wait_until="networkidle")

            if "login" in page.url or "auth" in page.url:
                print("Cookie失效，尝试密码登录...")
                if not (pterodactyl_email and pterodactyl_password): return False
                page.fill('input[name="username"]', pterodactyl_email)
                page.fill('input[name="password"]', pterodactyl_password)
                time.sleep(1)
                page.click('button[type="submit"]')
                page.wait_for_url("**/server/**", timeout=30000)
                print("登录成功。")

            # --- 3. 核心升级：等待布局稳定 ---
            print("等待页面元素和广告加载...")
            add_button = page.locator('button:has-text("시간 추가")')
            add_button.wait_for(state='visible', timeout=30000)
            add_button.scroll_into_view_if_needed()
            
            # 【布局稳定锁】循环检测按钮Y坐标，直到它不再变动
            # 这能完美解决广告把按钮往下挤的问题
            print("正在监测布局位移 (防止误触)...")
            stable_count = 0
            last_y = 0
            for _ in range(20): # 最多检测10秒
                box = add_button.bounding_box()
                if box:
                    current_y = box['y']
                    if abs(current_y - last_y) < 2 and last_y != 0:
                        stable_count += 1
                    else:
                        stable_count = 0 # 发生位移，重置计数
                    
                    last_y = current_y
                    
                    if stable_count >= 3: # 连续3次(1.5秒)位置没变，视为稳定
                        print("页面布局已稳定。")
                        break
                time.sleep(0.5)

            # --- 4. 核心升级：DOM 级精确查找 Cloudflare ---
            # 不再猜坐标，而是直接找“有效期”卡片里的 iframe
            print("寻找 Cloudflare 验证框...")
            
            # 查找包含 "유통기한" 文本的容器，并在其内部查找 iframe
            # 这里的逻辑是：找到续期面板 -> 找到里面的 iframe
            cf_iframe = page.locator('.card:has-text("유통기한") iframe, iframe[src*="turnstile"], iframe[src*="cloudflare"]').first
            
            if cf_iframe.count() > 0:
                cf_box = cf_iframe.bounding_box()
                if cf_box:
                    print(f"锁定验证框坐标: {cf_box}")
                    # 【精准打击】点击 iframe 左侧 30px，垂直居中位置
                    # 这样一定能点中 checkbox，不管它被挤到哪里
                    click_x = cf_box['x'] + 30 
                    click_y = cf_box['y'] + (cf_box['height'] / 2)
                    
                    print(f"点击坐标: ({click_x}, {click_y})")
                    page.mouse.move(click_x, click_y)
                    time.sleep(0.5)
                    page.mouse.down()
                    time.sleep(0.1)
                    page.mouse.up()
                    
                    print("已点击验证框，等待 10 秒...")
                    time.sleep(10)
                    page.screenshot(path="after_iframe_click.png")
                else:
                    print("错误: 找到 iframe 但无法获取坐标 (可能被隐藏)")
            else:
                print("警告: 未找到 Cloudflare iframe，尝试盲点按钮上方...")
                # 备用：如果找不到 iframe，回退到 relative coordinate，但稍微抬高一点
                btn_box = add_button.bounding_box()
                if btn_box:
                    page.mouse.click(btn_box['x'] + 28, btn_box['y'] - 50) # 抬高到 50px

            # --- 5. 点击续期按钮 ---
            if not add_button.is_enabled():
                print("验证未立即通过，稍等 5 秒再试...")
                time.sleep(5)

            if add_button.is_enabled():
                print("按钮已启用！执行续期...")
                add_button.click()
                time.sleep(5)
                page.screenshot(path="final_success_v4.png")
                
                content = page.content()
                if "success" in content.lower() or "extended" in content.lower():
                    print("成功：检测到成功提示！")
                    return True
                else:
                    print("流程结束，请查看截图。")
                    return True
            else:
                print("失败：按钮依然禁用，验证未通过。")
                page.screenshot(path="failed_disabled.png")
                return False

        except Exception as e:
            print(f"脚本异常: {e}")
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
