import os
import time
from playwright.sync_api import sync_playwright

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    cookie_value = os.environ.get('REMEMBER_WEB_COOKIE')
    
    with sync_playwright() as p:
        # 强制使用本地 WARP 代理，避免 GHA 数据中心 IP 封锁
        browser = p.chromium.launch(
            headless=True,
            proxy={"server": "socks5://127.0.0.1:40000"},
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        
        # 注入身份验证 Cookie
        if cookie_value:
            context.add_cookies([{
                'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d',
                'value': cookie_value,
                'domain': 'hub.weirdhost.xyz', 'path': '/',
                'httpOnly': True, 'secure': True, 'sameSite': 'Lax'
            }])
        
        page = context.new_page()
        page.set_default_timeout(60000)

        try:
            print(f"正在访问服务器控制台: {server_url}")
            page.goto(server_url, wait_until="domcontentloaded")
            
            # 等待页面和 Cloudflare 验证加载
            print("等待 12 秒让验证框渲染...")
            time.sleep(12) 
            
            # 1. 尝试直接穿透 iframe 点击“文字”
            try:
                # 定位 Cloudflare 专用的安全挑战 iframe
                cf_frame = page.frame_locator('iframe[title*="Cloudflare security challenge"]')
                # 尝试点击包含特定文字的复选框区域
                cf_frame.get_by_text("Verify you are human").click(timeout=5000)
                print("已尝试通过 iframe 穿透点击文字。")
            except Exception as e:
                print(f"直接点击 iframe 失败，转入坐标打击方案。")

            # 2. 坐标打击：以“追加时间”按钮为基准向上偏移
            # 这种方法可以无视顶部横幅导致的整体位移
            button = page.locator('button:has-text("시간 추가")')
            button.wait_for(state='visible')
            box = button.bounding_box()
            
            if box and not button.is_enabled():
                print("检测到按钮仍处于禁用状态，执行相对坐标点击...")
                # 在按钮中心位置向上偏移约 55 像素，即为验证框中心
                target_x = box['x'] + (box['width'] / 2)
                target_y = box['y'] - 55 
                
                # 模拟鼠标移动并点击，增加真实性
                page.mouse.move(target_x, target_y)
                page.mouse.down()
                time.sleep(0.1)
                page.mouse.up()
                print(f"已点击相对坐标: ({target_x}, {target_y})")
            
            # 3. 最终确认并执行续期
            time.sleep(8) # 等待验证生效
            if button.is_enabled():
                button.click()
                print("✅ 续期按钮点击成功！")
                time.sleep(5)
                page.screenshot(path="final_success.png")
                return True
            else:
                print("❌ 验证仍未通过，请检查 screenshots 附件")
                page.screenshot(path="failed_at_last.png")
                return False

        except Exception as e:
            print(f"执行过程中发生异常: {e}")
            page.screenshot(path="error_trace.png")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    if add_server_time():
        exit(0)
    else:
        exit(1)
