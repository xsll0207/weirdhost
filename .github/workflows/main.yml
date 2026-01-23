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
        # 1. 启动浏览器（必须 headed 才能让你手动点 CF）
        browser = p.chromium.launch(
            headless=False,
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
            # 2. 登录逻辑
            if remember_web_cookie:
                context.add_cookies([{
                    'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d',
                    'value': remember_web_cookie,
                    'domain': 'hub.weirdhost.xyz',
                    'path': '/',
                    'expires': int(time.time()) + 31536000,
                    'httpOnly': True,
                    'secure': True,
                    'sameSite': 'Lax'
                }])

            print(f"访问: {server_url}")
            page.goto(server_url, wait_until="domcontentloaded")

            if "login" in page.url or "auth" in page.url:
                print("转入账号密码登录...")
                if not (pterodactyl_email and pterodactyl_password):
                    return False
                page.fill('input[name="username"]', pterodactyl_email)
                page.fill('input[name="password"]', pterodactyl_password)
                page.click('button[type="submit"]')
                page.wait_for_url("**/server/**", timeout=30000)

            # ====== 3. 检测 CF 验证并等待你手动点击 ======
            # 只做“检测 + 暂停”，不做自动点（合规做法）
            def wait_for_human_complete_cf(timeout_sec=300):
                """
                检测到疑似 CF challenge/Turnstile 时，截图并暂停等待你手动完成。
                返回 True 表示未检测到或已完成，False 表示超时。
                """
                start = time.time()
                while time.time() - start < timeout_sec:
                    # 常见 CF 挑战 iframe 域名（只用于检测是否出现）
                    cf_iframe = page.locator('iframe[src*="challenges.cloudflare.com"]')
                    # 页面上常见的“请确认你是人类”文案（韩文/英文都可能）
                    cf_text = page.locator('text=/사람인지 확인|Verify you are human|Checking your browser/i')

                    # 如果检测到挑战存在
                    if cf_iframe.count() > 0 or cf_text.count() > 0:
                        print("检测到 Cloudflare 人机验证。请你在弹出的浏览器窗口里手动完成验证。")
                        page.screenshot(path="cf_detected.png", full_page=True)
                        print("已保存截图 cf_detected.png")
                        input("完成验证后回到终端按回车继续...")

                        # 给验证生效一点时间
                        time.sleep(2)

                        # 再检测一次：如果不见了就认为完成
                        if cf_iframe.count() == 0 and cf_text.count() == 0:
                            print("CF 验证似乎已完成，继续执行。")
                            return True

                        # 还在：继续循环让你再点
                        print("验证似乎仍存在，可能需要再次操作。")
                    else:
                        # 未检测到 CF，直接通过
                        return True

                    time.sleep(1)

                print("等待手动验证超时。")
                page.screenshot(path="cf_timeout.png", full_page=True)
                return False

            if not wait_for_human_complete_cf(timeout_sec=600):
                return False

            # ====== 4. 点击续期按钮 ======
            print("等待页面元素加载...")
            add_button = page.locator('button:has-text("시간 추가")')
            add_button.wait_for(state='visible', timeout=30000)
            add_button.scroll_into_view_if_needed()

            # 再次确认可点
            if not add_button.is_enabled():
                print("시간 추가 按钮不可用，可能验证未生效或页面未刷新。尝试刷新一次。")
                page.reload(wait_until="domcontentloaded")
                time.sleep(2)
                add_button = page.locator('button:has-text("시간 추가")')
                add_button.wait_for(state='visible', timeout=30000)
                add_button.scroll_into_view_if_needed()

            if add_button.is_enabled():
                print("点击续期...")
                add_button.click()
                time.sleep(3)
                page.screenshot(path="final_result.png", full_page=True)
                print("已保存 final_result.png")
                return True
            else:
                print("失败：시간 추가 仍不可点击。")
                page.screenshot(path="failed_final.png", full_page=True)
                return False

        except Exception as e:
            print(f"脚本异常: {e}")
            page.screenshot(path="error_crash.png", full_page=True)
            return False
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    raise SystemExit(0 if add_server_time() else 1)
