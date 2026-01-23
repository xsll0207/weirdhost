import os
import time
from playwright.sync_api import sync_playwright

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    # --- 1. 获取登录和代理凭据 ---
    remember_web_cookie = os.environ.get('REMEMBER_WEB_COOKIE')
    pterodactyl_email = os.environ.get('PTERODACTYL_EMAIL')
    pterodactyl_password = os.environ.get('PTERODACTYL_PASSWORD')

    # 获取代理配置
    proxy_host = os.environ.get('PROXY_HOST')
    proxy_port = os.environ.get('PROXY_PORT')
    proxy_user = os.environ.get('PROXY_USERNAME')
    proxy_pass = os.environ.get('PROXY_PASSWORD')

    if not (remember_web_cookie or (pterodactyl_email and pterodactyl_password)):
        print("错误: 缺少登录凭据。")
        return False

    with sync_playwright() as p:
        # --- 2. 配置启动参数 (含代理) ---
        launch_args = {
            "headless": True,
            "args": [
                '--disable-blink-features=AutomationControlled', 
                '--no-sandbox', 
                '--window-size=1920,1080'
            ]
        }

        # 如果环境变量里有代理 IP，则配置代理
        if proxy_host and proxy_port:
            print(f"配置 SOCKS5 代理: {proxy_host}:{proxy_port}")
            proxy_config = {
                "server": f"socks5://{proxy_host}:{proxy_port}"
            }
            # 如果有账号密码，添加认证
            if proxy_user and proxy_pass:
                proxy_config["username"] = proxy_user
                proxy_config["password"] = proxy_pass
            
            launch_args["proxy"] = proxy_config
        else:
            print("未检测到代理配置，使用直连模式。")

        # 启动浏览器
        browser = p.chromium.launch(**launch_args)

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale='ko-KR', timezone_id='Asia/Seoul'
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        page = context.new_page()
        page.set_default_timeout(60000)

        try:
            # --- 3. 登录逻辑 ---
            if remember_web_cookie:
                context.add_cookies([{
                    'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d',
                    'value': remember_web_cookie,
                    'domain': 'hub.weirdhost.xyz', 'path': '/',
                    'expires': int(time.time()) + 31536000, 'httpOnly': True, 'secure': True, 'sameSite': 'Lax'
                }])
            
            print(f"访问: {server_url}")
            # 增加 timeout 防止代理速度慢导致超时
            page.goto(server_url, wait_until="networkidle", timeout=90000)

            if "login" in page.url or "auth" in page.url:
                print("Cookie失效或未设置，转入账号密码登录...")
                if not (pterodactyl_email and pterodactyl_password): return False
                page.fill('input[name="username"]', pterodactyl_email)
                page.fill('input[name="password"]', pterodactyl_password)
                time.sleep(2)
                page.click('button[type="submit"]')
                page.wait_for_url("**/server/**", timeout=60000)

            # --- 4. 核心：网格地毯式轰炸 (Grid Bombing) ---
            print("等待页面元素加载...")
            add_button = page.locator('button:has-text("시간 추가")')
            add_button.wait_for(state='visible', timeout=60000) # 代理可能慢，增加等待时间
            add_button.scroll_into_view_if_needed()

            # [布局稳定锁]
            print("正在锁定布局 (等待广告位移)...")
            stable_count = 0
            last_y = 0
            for _ in range(20):
                box = add_button.bounding_box()
                if box:
                    if abs(box['y'] - last_y) < 2 and last_y != 0:
                        stable_count += 1
                    else:
                        stable_count = 0
                    last_y = box['y']
                    if stable_count >= 3: break
                time.sleep(0.5)
            print("布局已稳定。")

            # [网格轰炸逻辑]
            if add_button.is_enabled():
                print("按钮已亮，直接点击！")
            else:
                box = add_button.bounding_box()
                if box:
                    start_x = box['x']
                    start_y = box['y']
                    
                    # 扩大覆盖范围：覆盖复选框 + 文字
                    x_offsets = [10, 35, 60, 85, 110] 
                    y_offsets = [30, 45, 60, 75]
                    
                    print(f"开始通过代理执行 {len(x_offsets)*len(y_offsets)} 点网格轰炸...")
                    
                    for y_off in y_offsets:
                        for x_off in x_offsets:
                            target_x = start_x + x_off
                            target_y = start_y - y_off
                            
                            page.mouse.move(target_x, target_y)
                            page.mouse.down()
                            time.sleep(0.05)
                            page.mouse.up()
                            time.sleep(0.1)
                            
                        if add_button.is_enabled():
                            print(f"命中！验证通过。")
                            break
                    
                    print("轰炸结束，等待验证生效...")
                    time.sleep(8) # 代理网络可能有延迟，多等一会
                    page.screenshot(path="after_grid_click.png")

            # --- 5. 点击续期 ---
            if not add_button.is_enabled():
                print("尝试最后补刀...")
                if box:
                    page.mouse.click(box['x'] + 20, box['y'] - 50)
                    time.sleep(5)

            if add_button.is_enabled():
                print("验证通过！点击续期...")
                add_button.click()
                time.sleep(8)
                page.screenshot(path="final_result_proxy.png")
                
                content = page.content()
                if "success" in content.lower() or "extended" in content.lower():
                    print("任务成功！")
                    return True
                return True
            else:
                print("失败：验证未通过，请检查截图 (可能是代理IP质量不佳)。")
                page.screenshot(path="failed_proxy.png")
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
