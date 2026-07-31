from playwright.async_api import async_playwright, Error as PlaywrightError


class SiteScraper:

  def __init__(self, headless: bool = True):
    self.headless = headless

  async def scrape_url(self, url: str, timeout: int = 60000):
    """Asynchronously scrapes a target URL using Playwright.

    Safe for use inside FastAPI's event loop.
    """
    async with async_playwright() as p:
      browser = await p.chromium.launch(
          headless=self.headless,
          args=[
              "--no-sandbox",
              "--disable-setuid-sandbox",
              "--disable-dev-shm-usage",
              "--disable-accelerated-2d-canvas",
              "--disable-gpu",
          ],
      )

      context = await browser.new_context(
          user_agent=(
              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/120.0.0.0 Safari/537.36"
          )
      )

      page = await context.new_page()

      try:
        await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        title = await page.title()
        html_content = await page.content()
        text_content = await page.inner_text("body")

        return {
            "status": "success",
            "url": url,
            "title": title,
            "html": html_content,
            "html_length": len(html_content),
            "text_length": len(text_content),
            "error": None,
        }

      except PlaywrightError as pe:
        error_msg = f"Playwright error on {url}: {str(pe)}"
        print(f"[Warning] {error_msg}")
        return {
            "status": "error",
            "url": url,
            "title": "",
            "html": "",
            "html_length": 0,
            "text_length": 0,
            "error": error_msg,
        }
      except Exception as e:
        error_msg = f"Unexpected error on {url}: {str(e)}"
        print(f"[Warning] {error_msg}")
        return {
            "status": "error",
            "url": url,
            "title": "",
            "html": "",
            "html_length": 0,
            "text_length": 0,
            "error": error_msg,
        }
      finally:
        await browser.close()