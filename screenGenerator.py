import base64
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def screenshot_full_cdp(url, output_path='full_screenshot.png', width=1920):
    # 1) Configuro Chrome headless (nuova modalità) e lancio
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument(f"--window-size={width},1080")
    # disabilito GPU e barre di scorrimento
    options.add_argument("--disable-gpu")
    options.add_argument("--hide-scrollbars")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    # 2) Vado alla pagina
    driver.get(url)

    # 3) Calcolo l'altezza totale del documento
    total_height = driver.execute_script("""
        return Math.max(
            document.body.scrollHeight,
            document.documentElement.scrollHeight
        );
    """)

    # 4) Imposto le metriche per catturare tutta l’altezza
    driver.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": width,
            "height": total_height,
            "deviceScaleFactor": 1,
            "mobile": False
        }
    )

    # 5) Catturo lo screenshot beyond viewport
    result = driver.execute_cdp_cmd("Page.captureScreenshot", {
        "fromSurface": True,
        "captureBeyondViewport": True
    })
    img_data = base64.b64decode(result["data"])
    with open(output_path, "wb") as f:
        f.write(img_data)

    print(f"[✅] Full-page screenshot salvato in: {output_path}")
    driver.quit()


if __name__ == "__main__":
    screenshot_full_cdp(
        "https://www.chess.com/login_and_go?returnUrl=https://www.chess.com/home",
        "pagina_intera_cdp.png"
    )
