"""
娃娃图片对齐工具：旋转矫正 + 脚底对齐 + 水平居中
"""

import os, sys, glob, math
import numpy as np
from PIL import Image


def get_bbox(arr):
    alpha = arr[:, :, 3]
    rows = np.any(alpha > 10, axis=1)
    cols = np.any(alpha > 10, axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    return rmin, rmax, cmin, cmax


def get_tilt_angle(arr):
    alpha = arr[:, :, 3]
    ys, xs = np.where(alpha > 10)
    if len(ys) == 0:
        return 0
    h = ys.max() - ys.min()
    top_mask = ys < (ys.min() + h // 4)
    bot_mask = ys > (ys.max() - h // 4)
    if top_mask.sum() == 0 or bot_mask.sum() == 0:
        return 0
    top_cx = xs[top_mask].mean()
    bot_cx = xs[bot_mask].mean()
    top_cy = ys[top_mask].mean()
    bot_cy = ys[bot_mask].mean()
    return math.degrees(math.atan2(bot_cx - top_cx, bot_cy - top_cy))


def align_images(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    images = sorted(glob.glob(os.path.join(input_dir, "*.png")) +
                    glob.glob(os.path.join(input_dir, "*.PNG")))
    if not images:
        print("没有找到图片"); return

    # 统一缩放到第一张图的尺寸
    OUT_W, OUT_H = Image.open(images[0]).size

    infos = []
    for p in images:
        img = Image.open(p).convert("RGBA")
        W, H = img.size
        if (W, H) != (OUT_W, OUT_H):
            img = img.resize((OUT_W, OUT_H), Image.LANCZOS)
        arr = np.array(img)

        # 旋转矫正
        angle = get_tilt_angle(arr)
        if abs(angle) > 0.5:
            arr = np.array(img.rotate(-angle, resample=Image.BICUBIC, expand=False))

        rmin, rmax, cmin, cmax = get_bbox(arr)
        infos.append({"path": p, "arr": arr, "foot": rmax, "cx": (cmin + cmax) // 2,
                      "angle": angle})

    max_foot = max(i["foot"] for i in infos)

    for info in infos:
        arr = info["arr"]
        dy = max_foot - info["foot"]
        dx = OUT_W // 2 - info["cx"]

        new_arr = np.zeros((OUT_H, OUT_W, 4), dtype=np.uint8)
        sy1, sy2, sx1, sx2 = 0, OUT_H, 0, OUT_W
        dy1, dy2, dx1, dx2 = dy, dy + OUT_H, dx, dx + OUT_W

        if dy1 < 0: sy1 -= dy1; dy1 = 0
        if dy2 > OUT_H: sy2 -= dy2 - OUT_H; dy2 = OUT_H
        if dx1 < 0: sx1 -= dx1; dx1 = 0
        if dx2 > OUT_W: sx2 -= dx2 - OUT_W; dx2 = OUT_W

        new_arr[dy1:dy2, dx1:dx2] = arr[sy1:sy2, sx1:sx2]

        fname = os.path.basename(info["path"])
        Image.fromarray(new_arr, "RGBA").save(os.path.join(output_dir, fname))
        print(f"  完成: {fname}  angle={info['angle']:+.1f}°  dy={dy:+d}  dx={dx:+d}")

    print(f"\n全部完成，输出在: {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python align.py <抠图文件夹> [输出文件夹]"); sys.exit(1)
    input_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(input_dir, "aligned")
    align_images(input_dir, output_dir)
