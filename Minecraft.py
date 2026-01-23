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
        # 1. 启动浏览器 (隐身配置)
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
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
                print("Cookie 失效，尝试密码登录...")
                if not (pterodactyl_email and pterodactyl_password): return False
                page.fill('input[name="username"]', pterodactyl_email)
                page.fill('input[name="password"]', pterodactyl_password)
                time.sleep(1)
                page.click('button[type="submit"]')
                page.wait_for_url("**/server/**", timeout=30000)

            # --- 3. 核心：垂直扫描点击 (Vertical Scan) ---
            print("等待页面加载...")
            time.sleep(5) # 等待那个绿色的横幅广告完全推开布局

            add_button = page.locator('button:has-text("시간 추가")')
            add_button.wait_for(state='visible', timeout=30000)
            add_button.scroll_into_view_if_needed()
            
            # 再次等待一下，确保滚动完成
            time.sleep(2)

            # 检查按钮是否本来就是亮着的（可能已经验证过了）
            if add_button.is_enabled():
                print("运气不错！按钮已经是可点击状态，直接点击。")
                add_button.click()
            else:
                print("按钮禁用中，开始【垂直多点扫描】寻找 Cloudflare 验证框...")
                
                # 获取按钮的基准坐标
                box = add_button.bounding_box()
                if not box:
                    print("无法获取按钮坐标！")
                    return False
                
                # 按钮的中心 X 坐标
                center_x = box['x'] + 25 # 偏左一点，通常 checkbox 在左边
                base_y = box['y'] # 按钮的顶部 Y 坐标

                # --- 扫描策略 ---
                # Cloudflare 框通常在按钮上方 30px 到 80px 之间
                # 我们每隔 15px 点一次，覆盖横幅导致的位移
                offsets = [35, 50, 65, 80] 
                
                for offset in offsets:
                    target_y = base_y - offset
                    print(f"尝试点击高度: 按钮上方 {offset}px (坐标: {int(center_x)}, {int(target_y)})")
                    
                    # 移动鼠标并点击
                    page.mouse.move(center_x, target_y)
                    time.sleep(0.3)
                    page.mouse.down()
                    time.sleep(0.1)
                    page.mouse.up()
                    
                    # 点完一次，等一小会儿看效果
                    time.sleep(2)
                    
                    # 检查按钮是不是亮了
                    if add_button.is_enabled():
                        print(f"成功！在上方 {offset}px 处击中验证框！")
                        break
                    else:
                        print("未命中，尝试下一个高度...")

            # --- 4. 最终尝试点击续期 ---
            print("扫描结束，检查结果...")
            page.screenshot(path="after_scan_click.png")

            if add_button.is_enabled():
                print("验证通过！点击续期按钮...")
                # 使用坐标点击按钮，防止被透明层遮挡
                btn_box = add_button.bounding_box()
                if btn_box:
                    page.mouse.click(btn_box['x'] + btn_box['width']/2, btn_box['y'] + btn_box['height']/2)
                else:
                    add_button.click()
                
                time.sleep(5)
                page.screenshot(path="final_result_v5.png")
                
                content = page.content()
                if "success" in content.lower() or "extended" in content.lower():
                    print("任务圆满成功！")
                    return True
                else:
                    # 有时候没提示文字但只要不报错就算成功
                    print("流程完成，请检查 final_result_v5.png")
                    return True
            else:
                print("失败：扫描了多个位置，但按钮依然不可用。可能是 IP 被 Cloudflare 暂时拉黑。")
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
