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
        # 1. 启动浏览器 (配置反检测)
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
                    'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d', # 请确认这个名字是最新的
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

            # --- 3. 核心：地毯式网格轰炸 (Grid Bombing) ---
            print("等待页面元素加载...")
            add_button = page.locator('button:has-text("시간 추가")')
            add_button.wait_for(state='visible', timeout=30000)
            add_button.scroll_into_view_if_needed()

            # [布局稳定锁] 等待绿色横幅把页面挤完
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
                    # 以按钮左上角为基准
                    start_x = box['x']
                    start_y = box['y']
                    
                    # 定义扫描网格：覆盖按钮上方 30px 到 80px 的所有区域
                    # X轴：从左边缘(0)向右扫描 100px (覆盖复选框和文字)
                    # Y轴：向上扫描 30, 45, 60, 75 px (确保高度覆盖)
                    x_offsets = [10, 35, 60, 85] 
                    y_offsets = [30, 45, 60, 75]
                    
                    print(f"开始执行 {len(x_offsets)*len(y_offsets)} 点网格轰炸...")
                    
                    for y_off in y_offsets:
                        for x_off in x_offsets:
                            # 目标坐标
                            target_x = start_x + x_off
                            target_y = start_y - y_off
                            
                            # 移动并点击
                            page.mouse.move(target_x, target_y)
                            page.mouse.down()
                            time.sleep(0.05)
                            page.mouse.up()
                            time.sleep(0.1) # 快速连点
                            
                        # 每点完一行，检查一次是否成功
                        if add_button.is_enabled():
                            print(f"命中！验证通过 (高度 -{y_off}px)")
                            break
                    
                    print("轰炸结束，等待验证生效...")
                    time.sleep(5)
                    page.screenshot(path="after_grid_click.png")

            # --- 4. 点击续期 ---
            if not add_button.is_enabled():
                # 最后的盲点尝试
                print("尝试最后一次补刀点击...")
                if box:
                    page.mouse.click(box['x'] + 20, box['y'] - 50)
                    time.sleep(5)

            if add_button.is_enabled():
                print("验证通过！点击续期...")
                add_button.click()
                time.sleep(5)
                page.screenshot(path="final_result_v7.png")
                
                content = page.content()
                if "success" in content.lower() or "extended" in content.lower():
                    print("任务成功！")
                    return True
                return True
            else:
                print("失败：验证未通过，请检查 after_grid_click.png")
                page.screenshot(path="failed_final.png")
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
