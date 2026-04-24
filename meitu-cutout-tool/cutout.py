"""
美图秀秀批量抠图半自动工具
- 自动打开 designkit 抠图页面
- 自动点击上传按钮并注入图片
- 你手动检查/编辑抠图效果
- 确认OK后手动下载，按回车继续下一张
- 全部完成后自动把透明背景填充绿色
"""

import os
import sys
import time
import glob
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from PIL import Image

MEITU_URL = "https://www.designkit.cn/cutout/?from=home_icon&matrix_channel=mtxx_web"
GREEN_COLOR = (0, 255, 0, 255)
# 固定的 Chrome 用户数据目录，保存登录状态
CHROME_PROFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome_profile")


def fill_green_background(input_path, output_path):
    img = Image.open(input_path).convert("RGBA")
    green_bg = Image.new("RGBA", img.size, GREEN_COLOR)
    green_bg.paste(img, mask=img)
    green_bg.convert("RGB").save(output_path)


def main():
    if len(sys.argv) < 2:
        print("用法: python cutout.py <图片文件夹路径>")
        print("示例: python cutout.py D:\\素材\\娃娃")
        sys.exit(1)

    input_dir = sys.argv[1]
    if not os.path.isdir(input_dir):
        print(f"文件夹不存在: {input_dir}")
        sys.exit(1)

    exts = ["*.png", "*.jpg", "*.jpeg", "*.webp"]
    images = []
    for ext in exts:
        images.extend(glob.glob(os.path.join(input_dir, ext)))
    images.sort()

    if not images:
        print("文件夹内没有找到图片")
        sys.exit(1)

    print(f"找到 {len(images)} 张图片")

    cutout_dir = os.path.join(input_dir, "cutout")
    green_dir = os.path.join(input_dir, "green")
    os.makedirs(cutout_dir, exist_ok=True)
    os.makedirs(green_dir, exist_ok=True)

    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": os.path.abspath(cutout_dir),
        "download.prompt_for_download": False,
    })
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR}")

    print("正在启动浏览器...")
    driver = webdriver.Chrome(options=chrome_options)

    # 打开页面，让用户确认登录状态
    driver.get(MEITU_URL)
    print("\n========================================")
    print("浏览器已打开，请确认登录状态")
    print("如果需要登录，请先在浏览器中登录会员账号")
    print("（登录状态会自动保存，下次无需重复登录）")
    input("确认已登录后按回车开始处理 >>> ")

    try:
        for i, img_path in enumerate(images):
            filename = os.path.basename(img_path)
            print(f"\n[{i+1}/{len(images)}] {filename}")
            print("正在打开抠图页面...")

            driver.get(MEITU_URL)
            time.sleep(5)

            # 点击上传按钮，触发动态生成 file input
            try:
                upload_btn = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".xdesign-image-upload-panel-uploadBtn"))
                )
                driver.execute_script("arguments[0].click()", upload_btn)
                time.sleep(2)

                # 找到动态生成的 file input 并上传
                file_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                )
                file_input.send_keys(os.path.abspath(img_path))
                print("已上传，等待抠图处理...")
                time.sleep(5)
            except Exception as e:
                print(f"自动上传失败: {e}")
                print("请手动上传图片")

            print("---")
            print("请检查抠图效果，需要的话手动编辑")
            print("确认后手动点【下载】保存图片")
            input("按回车继续下一张 >>> ")

    except KeyboardInterrupt:
        print("\n用户中断")
    finally:
        driver.quit()

    # 批量填充绿色背景
    print("\n========== 开始填充绿色背景 ==========")
    cutout_images = []
    for ext in exts:
        cutout_images.extend(glob.glob(os.path.join(cutout_dir, ext)))

    if not cutout_images:
        print("cutout 文件夹内没有找到抠好的图片，跳过绿色填充")
    else:
        for img_path in cutout_images:
            fname = os.path.basename(img_path)
            out_path = os.path.join(green_dir, fname)
            fill_green_background(img_path, out_path)
            print(f"  绿色背景: {fname}")
        print(f"\n完成! 绿色背景图片保存在: {green_dir}")


if __name__ == "__main__":
    main()
