import os
import time
from playwright.sync_api import sync_playwright

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    remember_web_cookie = os.environ.get('REMEMBER_WEB_COOKIE')
    pterodactyl_email = os.environ.get('PTERODACTYL_EMAIL')
    pterodactyl_password = os.environ.get('PTERODACTYL_PASSWORD')

    # 核心：直接使用本地 WARP 提供的 SOCKS5 代理
    warp_proxy = "socks5://127.0.0.1:40000"

    with sync_playwright() as p:
        print(f"正在通过 WARP 出口访问 (127.0.0.1:40000)...")
        
        browser = p.chromium.launch(
            headless=True,
            proxy={"server": warp_proxy}, 
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox', '--window-size=1920,1080']
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        # 隐藏自动化特征
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        page = context.new_page()
        page.set_default_timeout(60000)

        try:
            # 注入登录 Cookie
            if remember_web_cookie:
                context.add_cookies([{
                    'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d',
                    'value': remember_web_cookie,
                    'domain': 'hub.weirdhost.xyz', 'path': '/',
                    'httpOnly': True, 'secure': True, 'sameSite': 'Lax'
                }])
            
            print(f"目标: {server_url}")
            page.goto(server_url, wait_until="domcontentloaded")
            
            # 等待 10 秒让 Cloudflare 验证框加载并尝试自动通过
            time.sleep(10)
            page.screenshot(path="warp_check.png")

            # 寻找“时间追加”按钮
            add_button = page.locator('button:has-text("시간 추가")')
            
            if add_button.count() > 0:
                # 如果按钮还是灰色的（没通过验证），执行 V7 轰炸
                if not add_button.is_enabled():
                    print("检测到验证拦截，执行网格轰炸...")
                    box = add_button.bounding_box()
                    if box:
                        # 在按钮上方区域进行 3x3 点击
                        for y_off in [40, 55, 70]:
                            for x_off in [20, 50, 80]:
                                page.mouse.click(box['x'] + x_off, box['y'] - y_off)
                                time.sleep(0.5)
                        
                        print("轰炸完成，等待验证生效...")
                        time.sleep(8)

                if add_button.is_enabled():
                    add_button.click()
                    print("✅ 成功点击续期按钮！")
                    time.sleep(5)
                    page.screenshot(path="final_result.png")
                    return True
                else:
                    print("❌ 按钮依然处于禁用状态")
            else:
                print("❌ 未能在页面上找到续期按钮")
                
            page.screenshot(path="failed.png")
            return False

        except Exception as e:
            print(f"执行异常: {e}")
            page.screenshot(path="error.png")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    if add_server_time():
        exit(0)
    else:
        exit(1)
