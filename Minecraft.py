import os
import time
from playwright.sync_api import sync_playwright

# --- 兼容性隐身特征注入 ---
def apply_stealth_safely(page):
    try:
        # 尝试方案 A: 标准同步导出
        from playwright_stealth import stealth_sync
        stealth_sync(page)
        print("Stealth 注入: 方案 A 成功")
    except Exception:
        try:
            # 尝试方案 B: 类方法应用
            from playwright_stealth import Stealth
            Stealth().apply(page)
            print("Stealth 注入: 方案 B 成功")
        except Exception as e:
            # 兜底：如果库损坏，依然尝试执行坐标点击
            print(f"Stealth 注入跳过: {e}")

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    cookie_value = os.environ.get('REMEMBER_WEB_COOKIE')
    
    with sync_playwright() as p:
        # 启动浏览器，通过 WARP 提供的 40000 端口进行 SOCKS5 代理
        browser = p.chromium.launch(
            headless=True,
            proxy={"server": "socks5://127.0.0.1:40000"},
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        apply_stealth_safely(page)
        
        if cookie_value:
            context.add_cookies([{
                'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d',
                'value': cookie_value,
                'domain': 'hub.weirdhost.xyz', 'path': '/',
                'httpOnly': True, 'secure': True, 'sameSite': 'Lax'
            }])

        try:
            print(f"正在访问: {server_url}")
            page.goto(server_url, wait_until="domcontentloaded", timeout=60000)
            
            # 等待布局稳定，防止绿色横幅位移影响坐标
            print("等待 15 秒让验证框稳定...")
            time.sleep(15) 
            
            # 以“追加时间”按钮为锚点计算坐标
            btn = page.locator('button:has-text("시간 추가")')
            btn.wait_for(state='visible')
            box = btn.bounding_box()
            
            if box:
                # 网格轰炸 3.5：针对 failed_check.png 中极度靠左的复选框
                print("执行网格轰炸 (精准覆盖左侧复选框区域)...")
                # 按钮左边缘是 box['x']。复选框中心约在左起 20-50px 处。
                x_targets = [box['x'] + 20, box['x'] + 30, box['x'] + 40, box['x'] + 50]
                # 纵向高度在按钮上方 55-75px 处
                y_targets = [box['y'] - 55, box['y'] - 62, box['y'] - 69]
                
                for ty in y_targets:
                    for tx in x_targets:
                        page.mouse.click(tx, ty)
                        time.sleep(0.1) 
                
                print("轰炸结束，等待验证生效...")
                time.sleep(15) 
                page.screenshot(path="after_bombing.png")

            # 最终续期动作
            print("尝试点击续期按钮...")
            btn.click()
            time.sleep(10)
            
            # 成功性校验：寻找页面中的韩语成功关键字
            content = page.content()
            if "성공" in content or "Success" in content:
                print("✅ 确认成功：服务器时长已增加！")
                page.screenshot(path="final_success.png")
                return True
            else:
                print("⚠️ 警告：虽然点击了按钮，但未检测到成功反馈。")
                page.screenshot(path="failed_check.png")
                return False

        except Exception as e:
            print(f"脚本执行错误: {e}")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    if not add_server_time():
        exit(1)
