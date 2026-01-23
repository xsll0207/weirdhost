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
        # 1. 浏览器启动配置 (隐身模式 + 窗口大小调整)
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
        
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

        page = context.new_page()
        page.set_default_timeout(60000)

        try:
            # 2. 登录流程
            if remember_web_cookie:
                print("尝试 Cookie 登录...")
                context.add_cookies([{
                    'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d', # 确保名字正确
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

            # --- 3. 核心修改：相对坐标锚定打击 ---
            print("正在定位 '시간 추가' 按钮以计算锚点...")
            add_button_selector = 'button:has-text("시간 추가")'
            add_button = page.locator(add_button_selector)
            add_button.wait_for(state='visible', timeout=30000)
            
            # 必须滚动到视图内，确保坐标计算准确
            add_button.scroll_into_view_if_needed()
            time.sleep(2) # 等待滚动和广告加载导致的布局稳定

            # 获取按钮的坐标盒子 (x, y, width, height)
            box = add_button.bounding_box()
            
            if box:
                print(f"按钮坐标: x={box['x']}, y={box['y']}")
                
                # --- 智能计算打击点 ---
                # 策略：Cloudflare 验证框就在按钮正上方。
                # 无论广告怎么把按钮往下挤，验证框永远跟着按钮走。
                # 我们瞄准按钮【左边缘向右 28px】，【上边缘向上 35px】的位置。
                # 这个位置通常是 Cloudflare checkbox 的正中心。
                
                target_x = box['x'] + 28
                target_y = box['y'] - 35
                
                print(f"计算打击坐标: x={target_x}, y={target_y}")
                print("执行鼠标点击 (模拟真人)...")
                
                # 移动鼠标并点击
                page.mouse.move(target_x, target_y)
                time.sleep(0.5)
                page.mouse.down()
                time.sleep(0.1)
                page.mouse.up()
                
                print("已点击，等待 8 秒验证生效...")
                time.sleep(8)
                page.screenshot(path="after_smart_click.png")
            else:
                print("严重错误：无法获取按钮坐标。")
                return False

            # --- 4. 点击续期按钮 ---
            # 检查按钮是否已启用 (Enable)
            if not add_button.is_enabled():
                print("按钮仍处于禁用状态，可能点击偏了，尝试备用方案：点击稍微偏上的位置...")
                # 备用打击：再往上抬 15 像素
                if box:
                    page.mouse.click(box['x'] + 28, box['y'] - 50)
                    time.sleep(5)
            
            if add_button.is_enabled():
                print("验证似乎成功，按钮已启用！点击续期...")
                # 同样用坐标点按钮，防止被透明层遮挡
                if box:
                    page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                else:
                    add_button.click()
                    
                time.sleep(5)
                page.screenshot(path="final_success_v3.png")
                
                content = page.content()
                if "success" in content.lower() or "extended" in content.lower():
                    print("任务圆满成功！")
                    return True
                else:
                    print("流程走完，请检查截图确认结果。")
                    return True
            else:
                print("失败：验证框始终未通过。")
                return False

        except Exception as e:
            print(f"脚本出错: {e}")
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
