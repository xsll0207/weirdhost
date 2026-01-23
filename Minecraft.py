import os
import time
from playwright.sync_api import sync_playwright
# 修正导入方式：明确导入同步模式所需的 stealth_sync 函数
try:
    from playwright_stealth import stealth_sync
except ImportError:
    # 兼容部分版本的导入方式
    from playwright_stealth import stealth_sync as stealth_sync

def add_server_time(server_url="https://hub.weirdhost.xyz/server/20a83c55"):
    cookie_value = os.environ.get('REMEMBER_WEB_COOKIE')
    
    with sync_playwright() as p:
        # 1. 启动浏览器
        browser = p.chromium.launch(
            headless=True,
            proxy={"server": "socks5://127.0.0.1:40000"},
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = context.new_page()
        # 使用正确的函数隐藏自动化特征
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
            page.goto(server_url, wait_until="domcontentloaded", timeout=60000)
            
            # 等待渲染，预留时间给 Cloudflare 盾
            print("等待 15 秒让验证框稳定...")
            time.sleep(15) 
            
            # 定位续期按钮作为锚点
            button = page.locator('button:has-text("시간 추가")')
            button.wait_for(state='visible')
            box = button.bounding_box()
            
            if box:
                # 重新校准：针对 failed_check.png 中复选框方框的精准点击
                print("执行网格轰炸 3.2 (覆盖复选框核心区域)...")
                # 按钮左边缘是 box['x']，复选框中心约在左移 30px 左右
                x_targets = [box['x'] + 25, box['x'] + 35, box['x'] + 45]
                y_targets = [box['y'] - 55, box['y'] - 60, box['y'] - 65]
                
                for ty in y_targets:
                    for tx in x_targets:
                        page.mouse.click(tx, ty)
                        time.sleep(0.1) 
                
                print("点击完成，预留 15 秒观察打钩状态...")
                time.sleep(15) 
                page.screenshot(path="after_bombing.png")

            # 执行续期点击
            print("尝试最终续期点击...")
            button.click()
            time.sleep(8)
            
            # 结果深度校验
            content = page.content()
            if "성공" in content or "Success" in content:
                print("✅ 确认：续期任务完全成功！")
                page.screenshot(path="final_success.png")
                return True
            else:
                print("⚠️ 警告：点击完成但未检测到成功提示，请检查 after_bombing.png 是否打钩。")
                page.screenshot(path="failed_check.png")
                return False

        except Exception as e:
            print(f"脚本异常: {e}")
            page.screenshot(path="error.png")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    if not add_server_time():
        exit(1)
