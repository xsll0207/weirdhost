import os
import time
from playwright.sync_api import sync_playwright

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    remember_web_cookie = os.environ.get('REMEMBER_WEB_COOKIE')
    pterodactyl_email = os.environ.get('PTERODACTYL_EMAIL')
    pterodactyl_password = os.environ.get('PTERODACTYL_PASSWORD')

    if not (remember_web_cookie or (pterodactyl_email and pterodactyl_password)):
        print("错误: 缺少登录凭据。")
        return False

    with sync_playwright() as p:
        # 1. 启动配置
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox', '--window-size=1920,1080']
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale='ko-KR', timezone_id='Asia/Seoul'
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        page = context.new_page()
        page.set_default_timeout(60000)

        try:
            # 2. 登录逻辑
            if remember_web_cookie:
                context.add_cookies([{
                    'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d', # 确保名字正确
                    'value': remember_web_cookie,
                    'domain': 'hub.weirdhost.xyz', 'path': '/',
                    'expires': int(time.time()) + 31536000, 'httpOnly': True, 'secure': True, 'sameSite': 'Lax'
                }])
            
            print(f"访问: {server_url}")
            page.goto(server_url, wait_until="networkidle")

            if "login" in page.url or "auth" in page.url:
                print("转入账号密码登录...")
                if not (pterodactyl_email and pterodactyl_password): return False
                page.fill('input[name="username"]', pterodactyl_email)
                page.fill('input[name="password"]', pterodactyl_password)
                time.sleep(1)
                page.click('button[type="submit"]')
                page.wait_for_url("**/server/**", timeout=30000)

            # --- 3. 核心：布局锁定 + 精确左侧打击 ---
            print("等待页面元素加载...")
            add_button = page.locator('button:has-text("시간 추가")')
            add_button.wait_for(state='visible', timeout=30000)
            add_button.scroll_into_view_if_needed()

            # [步骤A] 布局稳定锁：等待绿色横幅广告加载完成，防止坐标跳变
            print("正在锁定布局 (防止绿色横幅干扰)...")
            stable_count = 0
            last_y = 0
            for _ in range(20): # 检测 10 秒
                box = add_button.bounding_box()
                if box:
                    if abs(box['y'] - last_y) < 2 and last_y != 0:
                        stable_count += 1
                    else:
                        stable_count = 0
                    last_y = box['y']
                    if stable_count >= 3: break # 连续稳定，跳出
                time.sleep(0.5)
            print("布局已稳定。")

            # [步骤B] 寻找 Cloudflare iframe 并执行“微调连点”
            # 直接找 iframe，不猜按钮上方的距离，因为 iframe 的位置最准
            cf_iframe = page.locator('iframe[src*="turnstile"], iframe[src*="cloudflare"]').first
            
            if cf_iframe.count() > 0:
                cf_box = cf_iframe.bounding_box()
                if cf_box:
                    print(f"找到验证框: {cf_box}")
                    
                    # 关键修改：只点击左侧 15px - 20px 区域 (复选框红心)
                    # 之前的 +25px 可能太右了，打到了文字上
                    center_y = cf_box['y'] + (cf_box['height'] / 2)
                    
                    # 连点三次，覆盖 X 轴微小偏差
                    x_targets = [15, 20, 25] 
                    
                    for x_offset in x_targets:
                        target_x = cf_box['x'] + x_offset
                        print(f"狙击点击: ({int(target_x)}, {int(center_y)})")
                        
                        page.mouse.move(target_x, center_y)
                        time.sleep(0.2)
                        page.mouse.down()
                        time.sleep(0.1)
                        page.mouse.up()
                        time.sleep(0.5) # 点完等一下
                        
                    print("点击完毕，等待验证变绿...")
                    time.sleep(8)
                    page.screenshot(path="after_precision_click.png")
            else:
                print("未直接找到 iframe，使用按钮坐标盲点...")
                # 备用：如果找不到 iframe，用按钮坐标推算，但这次 x 只加 18
                btn_box = add_button.bounding_box()
                if btn_box:
                    page.mouse.click(btn_box['x'] + 18, btn_box['y'] - 45)
                    time.sleep(8)

            # --- 4. 点击续期 ---
            if add_button.is_enabled():
                print("验证通过！点击续期...")
                add_button.click()
                time.sleep(5)
                page.screenshot(path="final_result_v6.png")
                
                content = page.content()
                if "success" in content.lower() or "extended" in content.lower():
                    print("任务成功！")
                    return True
                return True
            else:
                print("失败：验证框未通过。")
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
