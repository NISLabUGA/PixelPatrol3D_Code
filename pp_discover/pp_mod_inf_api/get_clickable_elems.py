import asyncio
from playwright.async_api import async_playwright
import json
import os
from urllib.parse import urlparse
from pyvirtualdisplay import Display
import nest_asyncio

nest_asyncio.apply()

async def process_url(url):
    data_dir = './data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)

    display = Display(visible=0, size=(1920, 1080))
    display.start()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            ignore_https_errors=True
        )
        page = await context.new_page()

        attempt = 0
        RETRY_LIMIT = 3
        clickable_elements = []

        while attempt < RETRY_LIMIT:
            try:
                attempt += 1
                print(f"Attempt {attempt} to process {url}")

                await page.goto(url, wait_until='domcontentloaded', timeout=5000)
                # await asyncio.wait_for(page.goto(url, wait_until='domcontentloaded', timeout=5000), timeout=30)

                print(f"Navigated to {url}")

                # clickable_elements = await find_clickable_elements(page)
                clickable_elements = await asyncio.wait_for(find_clickable_elements(page), timeout=30)

                parsed_url = urlparse(url)
                base_filename = parsed_url.hostname.replace('www.', '')  # Removes 'www.' if present
                with open(f'{data_dir}/{base_filename}.json', 'w') as f:
                    json.dump(clickable_elements, f, indent=4)
                await page.screenshot(path=f'{data_dir}/{base_filename}.png')

                print(f"Successfully processed {url}")
                break
            except Exception as err:
                print(f"Failed processing {url} on attempt {attempt}: {err}")
                if attempt >= RETRY_LIMIT:
                    print(f"Exceeded retry limit for {url}")

        await browser.close()
        display.stop()

    return clickable_elements

async def find_clickable_elements(page):
    clickable_elements = []

    async def dfs(element):
        try:
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            is_hidden_or_dropdown = await element.evaluate('el => {'
                'const style = getComputedStyle(el);'
                'const isHidden = style.display === "none" || style.visibility === "hidden" || style.opacity === "0" || el.offsetWidth === 0 || el.offsetHeight === 0;'
                'const isDropdown = el.tagName.toLowerCase() === "select" || Array.from(el.classList).includes("dropdown");'
                'return isHidden || isDropdown;'
                '}')

            if is_hidden_or_dropdown:
                return

            is_visible = await element.evaluate('el => {'
                'const style = getComputedStyle(el);'
                'return ('
                'style.display !== "none" &&'
                'style.visibility !== "hidden" &&'
                'style.opacity !== "0" &&'
                'el.offsetWidth > 0 &&'
                'el.offsetHeight > 0'
                ');'
                '}')

            if is_visible:
                is_attached = await element.evaluate('el => !!el.isConnected')
                has_pointer_events = await element.evaluate('el => getComputedStyle(el).pointerEvents !== "none"')

                if is_attached and has_pointer_events:
                    bounding_box = await element.bounding_box()
                    if bounding_box:
                        x = bounding_box['x'] + bounding_box['width'] / 2
                        y = bounding_box['y'] + bounding_box['height'] / 2
                        # print(f"Moving mouse to element at ({x}, {y})")

                        await page.mouse.move(x, y)

                        await asyncio.sleep(0.003)

                        is_clickable_on_hover = await page.evaluate('el => {'
                            'const hoverCursor = getComputedStyle(el).cursor;'
                            'return hoverCursor === "pointer" || (hoverCursor === "text" && (el.tagName.toLowerCase() === "input" || el.tagName.toLowerCase() === "textarea" || el.isContentEditable));'
                            '}', element)

                        if is_clickable_on_hover:
                            clickable_elements.append(bounding_box)

                        await asyncio.sleep(0.003)

            children = await element.query_selector_all('>*')
            for child in children:
                await dfs(child)

        except Exception as inner_err:
            print(f"Skipped element due to error: {inner_err}")

    root = await page.query_selector('body')
    await dfs(root)

    return [bbox for i, bbox in enumerate(clickable_elements) if not any(
        j != i and bbox['x'] >= other['x'] and bbox['y'] >= other['y'] and
        bbox['x'] + bbox['width'] <= other['x'] + other['width'] and
        bbox['y'] + bbox['height'] <= other['y'] + other['height']
        for j, other in enumerate(clickable_elements)
    )]

def get_clickable_elements(url):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(process_url(url))

# Example usage:
# elements = run('https://example.com')
# print(elements)
