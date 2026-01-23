import os
import time
from playwright.sync_api import sync_playwright

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    # --- 1. 获取凭据 ---
    remember_web_cookie = os.environ.get('REMEMBER_WEB_COOKIE')
    pterodactyl_email = os.environ.get('PTERODACTYL_EMAIL')
    pterodactyl_password = os.environ.get('PTERODACTYL_PASSWORD')

    proxy_host = os.environ.get('PROXY_HOST')
    proxy_port = os.environ.get('PROXY_PORT')
    proxy_user = os.environ.get('PROXY_USERNAME')
    proxy_pass = os.environ.get('PROXY_PASSWORD')

    if not (remember_web_cookie or (pterodactyl_email and pterodactyl_password)):
        print("错误: 缺少登录凭据。")
        return False

    with sync_playwright() as p:
        # --- 2. 配置 Firefox (万能代理注入) ---
        launch_options = {
            "headless": True,
            "args": ['--window-size=1920,1080']
        }

        # 注入代理配置 (同时设置 HTTP, SSL, SOCKS)
        if proxy_host and proxy_port:
            print(f"配置 Firefox 代理 (HTTP/SOCKS兼容模式): {proxy_host}:{proxy_port}")
            try:
                port_int = int(proxy_port)
                # Firefox 首选项配置
                prefs = {
                    "network.proxy.type": 1,               # 手动代理
                    
                    # 同时配置 HTTP 和 HTTPS 代理 (应对 HTTP 代理)
                    "network.proxy.http": proxy_host,
                    "network.proxy.http_port": port_int,
                    "network.proxy.ssl": proxy_host,
                    "network.proxy.ssl_port": port_int,

                    # 同时配置 SOCKS 代理 (应对 SOCKS5 代理)
                    "network.proxy.socks": proxy_host,
                    "network.proxy.socks_port": port_int,
                    "network.proxy.socks_version": 5,
                    
                    "network.proxy.socks_remote_dns": True,
                    "network.http.connection-timeout": 60,
                    "network.http.response.timeout": 60
                }
                
                # 如果有账号密码，注入认证信息 (HTTP和SOCKS都注入)
                if proxy_user and proxy_pass:
                    print("检测到代理账号密码，已注入认证信息。")
                    # SOCKS 认证
                    prefs["network.proxy.socks_username"] = proxy_user
                    prefs["network.proxy.socks_password"] = proxy_pass
                    # Firefox 某些版本可能会自动处理 HTTP Auth，但主要通过弹窗，headless下较难
                    # 这里的配置主要保 SOCKS5 有密码的情况
                else:
                    print("未检测到代理账号密码，使用免密模式。")

                launch_options["firefox_user_prefs"] = prefs
                
            except ValueError:
                print("错误: 代理端口无效。")
                return False
        else:
            print("未检测到代理，使用直连。")

        # 启动 Firefox
        browser = p.firefox.launch(**launch_options)

        context = browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            viewport={'width': 1920, 'height': 1080},
            locale='ko-KR', timezone_id='Asia/Seoul'
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        
        page = context.new_page()
        page.set_default_timeout(60000)

        try:
            # --- 3. 访问与登录 ---
            if remember_web_cookie:
                context.add_cookies([{
                    'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d',
                    'value': remember_web_cookie,
                    'domain': 'hub.weirdhost.xyz', 'path': '/',
                    'expires': int(time.time()) + 31536000, 'httpOnly': True, 'secure': True, 'sameSite': 'Lax'
                }])
            
            print(f"正在通过代理访问: {server_url}")
            
            try:
                # 尝试访问，如果连不上直接捕获异常
                page.goto(server_url, wait_until="domcontentloaded", timeout=45000)
                print("页面连接成功，正在等待渲染...")
                time.sleep(5)
            except Exception as e:
                print("------------------------------------------------")
                print(f"【严重错误】无法连接到网站。代理 IP 可能已死或拒绝连接。")
                print(f"错误详情: {e}")
                print("------------------------------------------------")
                page.screenshot(path="connection_failed.png")
                return False
            
            # 检查是否掉到了登录页
            if "login" in page.url or "auth" in page.url:
                print("需要登录，执行账号密码登录...")
                if not (pterodactyl_email and pterodactyl_password): return False
                page.fill('input[name="username"]', pterodactyl_email)
                page.fill('input[name="password"]', pterodactyl_password)
                time.sleep(1)
                with page.expect_navigation(wait_until="domcontentloaded", timeout=60000):
                    page.click('button[type="submit"]')
                print("登录提交完成。")

            # --- 4. 核心：V7 网格地毯式轰炸 ---
            print("查找续期按钮...")
            try:
                add_button = page.locator('button:has-text("시간 추가")')
                add_button.wait_for(state='visible', timeout=30000)
                add_button.scroll_into_view_if_needed()
            except:
                print("错误：找不到续期按钮。可能是 Cloudflare 拦截了页面加载，或者代理速度太慢导致白屏。")
                page.screenshot(path="page_load_failed.png")
                return False

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

            # [网格轰炸]
            if add_button.is_enabled():
                print("按钮已亮，直接点击！")
            else:
                box = add_button.bounding_box()
                if box:
                    start_x = box['x']
                    start_y = box['y']
                    
                    # V7 轰炸坐标
                    x_offsets = [10, 35, 60, 85, 110] 
                    y_offsets = [30, 45, 60, 75]
                    
                    print(f"开始执行网格轰炸 ({len(x_offsets)*len(y_offsets)}次点击)...")
                    
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
                    time.sleep(8) 
                    page.screenshot(path="after_grid_click.png")

            # --- 5. 补刀与结果检查 ---
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
                print("失败：验证未通过，请检查截图 failed_proxy.png")
                page.screenshot(path="failed_proxy.png")
                return False

        except Exception as e:
            print(f"脚本执行期间发生异常: {e}")
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
