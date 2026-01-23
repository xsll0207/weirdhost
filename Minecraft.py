import os
import time
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    cookie_value = os.environ.get('REMEMBER_WEB_COOKIE')
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            proxy={"server": "socks5://127.0.0.1:40000"},
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        # 强制隐藏自动化特征
        stealth_sync(page)
        
        if cookie_value:
            context.add_cookies([{
                'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d',
                'value': cookie_value,
                'domain': 'hub.weirdhost.xyz', 'path': '/',
                'httpOnly': True, 'secure': True, 'sameSite': 'Lax'
            }])

        try:
            print(f"正在访问控制台: {server_url}")
            page.goto(server_url, wait_until="networkidle", timeout=60000)
            
            # 关键等待：给横幅和验证码留出足够的加载时间
            time.sleep(15) 
            
            # 定位按钮锚点
            btn = page.locator('button:has-text("시간 추가")')
            btn.wait_for(state='visible')
            box = btn.bounding_box()
            
            if box:
                print("执行网格轰炸 5.0 (极高密度覆盖复选框核心区域)...")
                # 坐标分析: 
                # 复选框小方块中心在按钮左边缘 (box['x']) 的右侧约 20-35 像素处
                # 纵向高度在按钮上方 55-75 像素处
                
                # 定义密集的点击点阵
                x_targets = [box['x'] + 22, box['x'] + 27, box['x'] + 32, box['x'] + 37, box['x'] + 42]
                y_targets = [box['y'] - 58, box['y'] - 63, box['y'] - 68, box['y'] - 73]
                
                for ty in y_targets:
                    for tx in x_targets:
                        page.mouse.click(tx, ty)
                        time.sleep(0.1) 
                
                print("点击完成，等待 20 秒让 Cloudflare 完成挑战...")
                time.sleep(20) 
                page.screenshot(path="after_bombing_final.png")

            # 最终执行续期
            print("尝试最终续期点击...")
            btn.click()
            time.sleep(10)
            
            # 结果校验：寻找“成功”关键字
            content = page.content()
            if "성공" in content or "Success" in content or "성공적으로" in content:
                print("✅ 任务真正成功：服务器时长已增加！")
                page.screenshot(path="final_success.png")
                return True
            else:
                print("⚠️ 警告：续期失败。请检查 after_bombing_final.png 的小方框是否变绿。")
                page.screenshot(path="failed_check.png")
                return False

        except Exception as e:
            print(f"脚本异常: {e}")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    if not add_server_time():
        exit(1)
