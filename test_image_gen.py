"""测试 Gemini-API 图片生成功能"""
import asyncio
import sys
import json
import http.cookiejar
from pathlib import Path

# 从 CDP 获取 Gemini cookies
async def fetch_cookies_from_cdp():
    """从 CDP 127.0.0.1:9223 获取 gemini.google.com 的 cookies"""
    import urllib.request

    # 获取 debug URL
    try:
        resp = urllib.request.urlopen("http://127.0.0.1:9223/json/version")
        version_info = json.loads(resp.read())
        ws_url = version_info.get("webSocketDebuggerUrl")
        print(f"Browser WS URL: {ws_url}")
    except Exception as e:
        print(f"Cannot connect to CDP: {e}")
        return None, None

    # 使用 CDP HTTP endpoint 获取 cookies
    try:
        # 获取第一个 page target
        resp = urllib.request.urlopen("http://127.0.0.1:9223/json")
        targets = json.loads(resp.read())
        page_targets = [t for t in targets if t.get("type") == "page"]
        if not page_targets:
            print("No page targets found")
            return None, None

        # 直接用 DevTools Protocol HTTP endpoint
        # /json/protocol 不行，需要用 ws
        # 改用 browser-level cookie API via HTTP
        return None, None
    except Exception as e:
        print(f"Error getting cookies: {e}")
        return None, None


async def main():
    from gemini_webapi import GeminiClient

    # 尝试从环境变量获取 cookies
    import os
    secure_1psid = os.environ.get("SECURE_1PSID", "")
    secure_1psidts = os.environ.get("SECURE_1PSIDTS", "")

    # 如果环境变量没有，尝试从 CDP 读取
    if not secure_1psid or not secure_1psidts:
        print("尝试从 CDP 获取 cookies...")
        cookies = await fetch_cookies_from_cdp()
        if cookies and cookies[0]:
            secure_1psid, secure_1psidts = cookies

    if not secure_1psid or not secure_1psidts:
        print("请提供 cookies:")
        print("  export SECURE_1PSID='your_cookie_value'")
        print("  export SECURE_1PSIDTS='your_cookie_value'")
        print("")
        print("或者直接在下方输入:")
        secure_1psid = input("__Secure-1PSID: ").strip()
        secure_1psidts = input("__Secure-1PSIDTS: ").strip()
        if not secure_1psid or not secure_1psidts:
            print("未提供 cookies，退出")
            return

    print(f"Cookie 长度: 1PSID={len(secure_1psid)}, 1PSIDTS={len(secure_1psidts)}")

    client = GeminiClient(secure_1psid, secure_1psidts, verify=False)

    try:
        await client.init(auto_refresh=True, verbose=True)
        print("初始化成功!")
    except Exception as e:
        print(f"初始化失败: {e}")
        return

    try:
        # 测试图片生成
        print("\n=== 测试图片生成 ===")
        response = await client.generate_content(
            "Generate a simple red circle on white background"
        )
        print(f"文本回复: {response.text[:200] if response.text else '(无文本)'}")
        print(f"图片数量: {len(response.images)}")

        for i, image in enumerate(response.images):
            print(f"  图片 {i}: {type(image).__name__}")
            print(f"    URL: {image.url[:100]}...")
            # 保存到 temp 目录
            output_dir = Path("/tmp/gemini_test")
            output_dir.mkdir(exist_ok=True)
            try:
                path = await image.save(
                    path=str(output_dir),
                    filename=f"test_image_{i}.png",
                    verbose=True,
                )
                print(f"    保存成功: {path}")
            except Exception as e:
                print(f"    保存失败: {e}")

        print("\n测试完成!")

    except Exception as e:
        print(f"生成失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
