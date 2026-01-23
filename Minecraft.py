import os
import time
from playwright.sync_api import sync_playwright

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    # 1. 获取凭据
    remember_web_cookie = os.environ.get('REMEMBER_WEB_COOKIE')
    pterodactyl_email = os.environ.get('PTERODACTYL_EMAIL')
    pterodactyl_password = os.environ.get('PTERODACTYL_PASSWORD')

    # 获取代理配置 (仅 IP 和 端口)
    proxy_host = os.environ.get('PROXY_HOST')
    proxy_port = os.environ.get('PROXY_PORT')

    if not (remember_web_cookie or (pterodactyl_email and pterodactyl_password)):
        print("错误: 缺少登录凭据。")
        return False

    with sync_playwright() as p:
        # 2. 启动参数 (Chromium)
        launch_args = {
            "headless": True,
            "args": [
                '--disable-blink-features=AutomationControlled', 
                '--no-sandbox', 
                '--window-size=1920,1080'
            ]
        }

        # 配置 HTTP 代理 (无密码模式)
        if proxy_host and proxy_port:
            print(f"配置代理: {proxy_host}:{proxy_port}")
            print("网络链路: GHA -> WARP -> 你的代理 -> 目标网站")
            
            # 直接构造代理地址，不含账号密码
            launch_args["proxy"] = {
                "server": f"http://{proxy_host}:{proxy_port}"
            }
        else:
            print("未检测到代理配置，使用 WARP 直连模式。")

        # 启动浏览器
        browser = p.chromium.launch(**launch_args)

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale='ko-KR', timezone_id='Asia/Seoul'
        )
        # 隐藏 webdriver 特征
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        
        page = context.new_page()
        # WARP + 代理 延迟可能极高，设置 90秒 超时
        page.set_default_timeout(90000)

        try:
            # 3. 访问逻辑
            if remember_web_cookie:
                context.add_cookies([{
                    'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d',
                    'value': remember_web_cookie,
                    'domain': 'hub.weirdhost.xyz', 'path': '/',
                    'expires': int(time.time()) + 31536000, 'httpOnly': True, 'secure': True, 'sameSite': 'Lax'
                }])
            
            print(f"正在访问: {server_url}")
            
            try:
                # 使用 domcontentloaded 避免超时
                page.goto(server_url, wait_until="domcontentloaded", timeout=90000)
                print("页面结构加载完成，等待渲染...")
                time.sleep(8) # 增加等待时间让代理缓冲
            except Exception as e:
                print(f"页面加载警告 (可能是网络太慢): {e}")
                page.screenshot(path="connection_debug.png")

            # 登录处理
            if "login" in page.url or "auth" in page.url:
                print("需要登录...")
                if not (pterodactyl_email and pterodactyl_password): return False
                page.fill('input[name="username"]', pterodactyl_email)
                page.fill('input[name="password"]', pterodactyl_password)
                time.sleep(2)
                with page.expect_navigation(wait_until="domcontentloaded", timeout=90000):
                    page.click('button[type="submit"]')
                print("登录完成。")

            # 4. 寻找按钮与网格轰炸
            print("查找续期按钮...")
            try:
                add_button = page.locator('button:has-text("시간 추가")')
                add_button.wait_for(state='visible', timeout=60000)
                add_button.scroll_into_view_if_needed()
            except:
                print("错误：无法加载按钮。请检查 connection_debug.png，可能是代理不通。")
                return False

            # [布局稳定锁] 防止广告位移
            print("正在锁定布局...")
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
            print("布局稳定。")

            # [网格地毯式轰炸] V7 逻辑
            if add_button.is_enabled():
                print("按钮已亮，直接点击！")
            else:
                box = add_button.bounding_box()
                if box:
                    start_x = box['x']
                    start_y = box['y']
                    # 扩大扫描范围 (X: 10~110, Y: 30~75)
                    x_offsets = [10, 35, 60, 85, 110] 
                    y_offsets = [30, 45, 60, 75]
                    
                    print(f"执行网格轰炸 ({len(x_offsets)*len(y_offsets)}点)...")
                    for y_off in y_offsets:
                        for x_off in x_offsets:
                            # 移动并点击
                            page.mouse.move(start_x + x_off, start_y - y_off)
                            page.mouse.down()
                            time.sleep(0.05)
                            page.mouse.up()
                            time.sleep(0.1) # 快速连点
                            
                        # 每点完一行检查一次
                        if add_button.is_enabled():
                            print("命中！验证通过。")
                            break
                    
                    time.sleep(8)
                    page.screenshot(path="after_grid.png")

            # 5. 补刀与结果
            if not add_button.is_enabled():
                print("补刀点击...")
                if box:
                    page.mouse.click(box['x'] + 20, box['y'] - 50)
                    time.sleep(5)

            if add_button.is_enabled():
                add_button.click()
                time.sleep(8)
                page.screenshot(path="final_result.png")
                content = page.content()
                if "success" in content.lower() or "extended" in content.lower():
                    print("任务成功！")
                    return True
                return True
            else:
                print("失败：验证未通过。")
                page.screenshot(path="failed.png")
                return False

        except Exception as e:
            print(f"异常: {e}")
            page.screenshot(path="crash.png")
            return False
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    if add_server_time():
        exit(0)
    else:
        exit(1)
