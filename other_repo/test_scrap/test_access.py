#!/usr/bin/env python3
"""简单的测试脚本，验证能否访问网站"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

print("正在初始化浏览器...")
chrome_options = Options()
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")

try:
    driver = webdriver.Chrome(options=chrome_options)
    print("✓ 浏览器初始化成功")
    
    url = "https://www.masslandrecords.com/MiddlesexNorth/D/Default.aspx"
    print(f"正在访问: {url}")
    driver.get(url)
    
    # 等待页面加载
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("✓ 页面加载完成")
    
    # 查找Book输入框
    print("查找Book输入框...")
    try:
        book_input = wait.until(
            EC.presence_of_element_located((By.ID, "SearchFormEx1_ACSTextBox_Book"))
        )
        print("✓ 找到Book输入框")
        print(f"  输入框值: {book_input.get_attribute('value')}")
    except Exception as e:
        print(f"✗ 找不到Book输入框: {e}")
        print(f"当前URL: {driver.current_url}")
        print(f"页面标题: {driver.title}")
    
    # 等待5秒以便观察
    print("\n等待5秒以便观察...")
    time.sleep(5)
    
    driver.quit()
    print("✓ 测试完成")
    
except Exception as e:
    print(f"✗ 错误: {e}")
    import traceback
    traceback.print_exc()
    try:
        driver.quit()
    except:
        pass

