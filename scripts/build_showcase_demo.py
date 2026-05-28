from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "docs" / "assets" / "demo"
OUTPUT_VIDEO = ASSET_DIR / "winros_showcase.webm"
OUTPUT_POSTER = ASSET_DIR / "winros_showcase_poster.jpg"
OUTPUT_MANIFEST = ASSET_DIR / "manifest.json"

WIDTH = 1920
HEIGHT = 1080
FPS = 30
DURATION_SECONDS = 8
TOTAL_FRAMES = FPS * DURATION_SECONDS


@dataclass(frozen=True)
class ClipSpec:
    key: str
    title: str
    subtitle: str
    metric: str
    path: Path


CLIPS = (
    ClipSpec(
        key="g1_fast_run",
        title="人形机器人快跑",
        subtitle="G1 已训练权重推理预览",
        metric="人形运动控制",
        path=ASSET_DIR / "g1_fast_run.mp4",
    ),
    ClipSpec(
        key="go2_fast_run",
        title="机器狗快跑",
        subtitle="Go2 已训练权重推理预览",
        metric="四足速度跟踪",
        path=ASSET_DIR / "go2_fast_run.mp4",
    ),
    ClipSpec(
        key="go2_stairs",
        title="机器狗上楼梯",
        subtitle="Go2 楼梯课程学习结果",
        metric="楼梯地形泛化",
        path=ASSET_DIR / "go2_stairs.mp4",
    ),
)


def font(name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts") / name,
        Path("C:/Windows/Fonts/NotoSansSC-VF.ttf"),
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


FONT = {
    "display": font("msyhbd.ttc", 58),
    "h1": font("msyhbd.ttc", 36),
    "h2": font("msyhbd.ttc", 27),
    "body": font("msyh.ttc", 23),
    "small": font("msyh.ttc", 18),
    "mono": font("consola.ttf", 20),
    "tiny": font("msyh.ttc", 16),
}


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def fit_frame(frame: np.ndarray, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(rgb)
    source_w, source_h = image.size
    scale = max(target_w / source_w, target_h / source_h)
    resized = image.resize((int(source_w * scale), int(source_h * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def paste_rounded(base: Image.Image, image: Image.Image, xy: tuple[int, int], radius: int) -> None:
    mask = Image.new("L", image.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, image.width, image.height), radius=radius, fill=255)
    base.paste(image, xy, mask)


def draw_sidebar(draw: ImageDraw.ImageDraw, frame_index: int) -> None:
    rounded(draw, (40, 40, 360, 1040), 24, "#f9fbfa", "#d7e1dc", 2)
    rounded(draw, (72, 72, 126, 126), 13, "#2f9e8f")
    draw.text((89, 82), "W", font=FONT["h2"], fill="white")
    draw.text((144, 73), "WinROS", font=FONT["h2"], fill="#17201d")
    draw.text((144, 109), "Windows 原生机器人平台", font=FONT["small"], fill="#68746f")

    items = [
        ("图形化控制台", "已连接"),
        ("MuJoCo 仿真", "三路预览"),
        ("强化学习推理", "已训练"),
        ("VLA 接口", "dry-run"),
        ("真机接口", "安全门控"),
    ]
    y = 180
    active = min(frame_index // 48, len(items) - 1)
    for idx, (label, value) in enumerate(items):
        fill = "#ffffff" if idx == active else "#f1f5f3"
        outline = "#2f9e8f" if idx == active else "#d7e1dc"
        rounded(draw, (72, y, 328, y + 70), 14, fill, outline, 2)
        draw.text((94, y + 14), label, font=FONT["body"], fill="#17201d")
        draw.text((94, y + 42), value, font=FONT["small"], fill="#2f766c")
        y += 88

    rounded(draw, (72, 760, 328, 950), 18, "#17201d")
    draw.text((94, 788), "安全门控", font=FONT["h2"], fill="white")
    draw.text((94, 833), "默认 dry-run", font=FONT["body"], fill="#a7ded7")
    draw.text((94, 870), "真机接口默认锁定", font=FONT["small"], fill="#d9e8e3")
    draw.text((94, 904), "所有命令先验证", font=FONT["small"], fill="#d9e8e3")


def draw_header(draw: ImageDraw.ImageDraw) -> None:
    draw.text((420, 62), "WinROS 平台演示", font=FONT["display"], fill="#14211d")
    draw.text(
        (424, 137),
        "在 Windows 上预览 ROS 2 + MuJoCo + 强化学习训练出的机器人策略。",
        font=FONT["body"],
        fill="#4d5d57",
    )

    badges = [("ROS 2", "#e8f1ff", "#255f9e"), ("MuJoCo", "#eaf8f4", "#1f766b"), ("RL 推理", "#fff3df", "#9c6112"), ("VLA 预留", "#f1edff", "#6d54a8")]
    x = 420
    for label, fill, color in badges:
        rounded(draw, (x, 188, x + 142, 232), 22, fill)
        draw.text((x + 28, 198), label, font=FONT["small"], fill=color)
        x += 158

    rounded(draw, (1470, 74, 1788, 170), 18, "#ffffff", "#d7e1dc", 2)
    draw.text((1492, 94), "权重推理预览", font=FONT["body"], fill="#17201d")
    draw.text((1492, 126), "本地 / CUDA / 可复现", font=FONT["small"], fill="#68746f")


def draw_video_card(
    base: Image.Image,
    draw: ImageDraw.ImageDraw,
    clip: ClipSpec,
    frame: np.ndarray,
    box: tuple[int, int, int, int],
    progress: float,
    active: bool,
) -> None:
    x1, y1, x2, y2 = box
    border = "#2f9e8f" if active else "#d7e1dc"
    rounded(draw, (x1, y1, x2, y2), 22, "#ffffff", border, 3 if active else 2)

    video_box = (x1 + 18, y1 + 78, x2 - 18, y2 - 74)
    video_img = fit_frame(frame, (video_box[2] - video_box[0], video_box[3] - video_box[1]))
    paste_rounded(base, video_img, (video_box[0], video_box[1]), 14)

    draw.text((x1 + 22, y1 + 18), clip.title, font=FONT["h2"], fill="#17201d")
    draw.text((x1 + 24, y1 + 51), clip.subtitle, font=FONT["small"], fill="#68746f")
    rounded(draw, (x2 - 150, y1 + 23, x2 - 24, y1 + 53), 15, "#edf8f5")
    draw.text((x2 - 124, y1 + 28), "预览中", font=FONT["tiny"], fill="#1f766b")

    draw.text((x1 + 24, y2 - 52), clip.metric, font=FONT["small"], fill="#4d5d57")
    bar_x1, bar_y1 = x1 + 24, y2 - 25
    bar_x2, bar_y2 = x2 - 24, y2 - 14
    rounded(draw, (bar_x1, bar_y1, bar_x2, bar_y2), 6, "#e7eeeb")
    rounded(draw, (bar_x1, bar_y1, int(bar_x1 + (bar_x2 - bar_x1) * progress), bar_y2), 6, "#2f9e8f")


def draw_bottom(draw: ImageDraw.ImageDraw, frame_index: int) -> None:
    rounded(draw, (420, 868, 1788, 1018), 22, "#ffffff", "#d7e1dc", 2)
    draw.text((452, 894), "平台流程", font=FONT["h2"], fill="#17201d")
    draw.text((452, 934), "选择权重  ->  策略推理  ->  命令校验  ->  仿真预览 / 遥测记录", font=FONT["body"], fill="#2f4f47")

    progress = (frame_index + 1) / TOTAL_FRAMES
    rounded(draw, (452, 982, 1370, 996), 8, "#e7eeeb")
    rounded(draw, (452, 982, int(452 + 918 * progress), 996), 8, "#2f9e8f")
    draw.text((1408, 920), f"进度 {frame_index + 1:03d}/{TOTAL_FRAMES}", font=FONT["body"], fill="#17201d")
    draw.text((1408, 955), "日志：dashboard / runs", font=FONT["small"], fill="#68746f")


def make_background(frame_index: int) -> Image.Image:
    base = Image.new("RGB", (WIDTH, HEIGHT), "#edf2ef")
    draw = ImageDraw.Draw(base)
    for x in range(0, WIDTH, 36):
        draw.line((x, 0, x - 280, HEIGHT), fill="#e5ece8", width=1)
    draw_sidebar(draw, frame_index)
    draw_header(draw)
    return base


def read_frame(captures: list[cv2.VideoCapture]) -> list[np.ndarray]:
    frames = []
    for capture in captures:
        ok, frame = capture.read()
        if not ok:
            capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = capture.read()
        if not ok:
            raise RuntimeError("Could not read source video frame")
        frames.append(frame)
    return frames


def repo_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def video_metadata(path: Path) -> dict[str, int | float | str]:
    metadata: dict[str, int | float | str] = {
        "asset": repo_path(path),
        "bytes": path.stat().st_size,
    }
    capture = cv2.VideoCapture(str(path))
    try:
        if capture.isOpened():
            fps = capture.get(cv2.CAP_PROP_FPS)
            frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if fps > 0:
                metadata["fps"] = round(float(fps), 3)
                metadata["duration_seconds"] = round(frames / fps, 3)
            if frames > 0:
                metadata["frames"] = frames
            if width > 0 and height > 0:
                metadata["resolution"] = f"{width}x{height}"
    finally:
        capture.release()
    return metadata


def public_checkpoint_label(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.replace("\\", "/")
    marker = "unitree_rl_mjlab/logs/rsl_rl/"
    if marker in normalized:
        return normalized.split(marker, 1)[1]
    return normalized


def write_manifest() -> None:
    previous: dict = {}
    if OUTPUT_MANIFEST.exists():
        previous = json.loads(OUTPUT_MANIFEST.read_text(encoding="utf-8"))

    previous_clips = {
        item.get("id"): item
        for item in previous.get("clips", [])
        if isinstance(item, dict) and item.get("id")
    }

    clips = []
    for clip in CLIPS:
        old = previous_clips.get(clip.key, {})
        item = {
            **old,
            "id": clip.key,
            "title_zh": clip.title,
            "subtitle_zh": clip.subtitle,
            "metric_zh": clip.metric,
            "record_command": old.get(
                "record_command",
                f"python .\\scripts\\record_unitree_mjlab_demo.py --profile {clip.key} --steps 240",
            ),
            "status": old.get("status", "generated"),
        }
        checkpoint = public_checkpoint_label(old.get("checkpoint"))
        if checkpoint:
            item["checkpoint"] = checkpoint
        item.update(video_metadata(clip.path))
        clips.append(item)

    manifest = {
        "schema_version": previous.get("schema_version", 1),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "project": previous.get("project", "WinROS"),
        "source_workspace": "external Unitree MJLab workspace, not distributed",
        "purpose": previous.get(
            "purpose",
            "GitHub first-screen demo for the Windows-first robotics learning platform.",
        ),
        "showcase": {
            **video_metadata(OUTPUT_VIDEO),
            "poster": repo_path(OUTPUT_POSTER),
            "poster_bytes": OUTPUT_POSTER.stat().st_size,
            "build_command": "python .\\scripts\\build_showcase_demo.py",
        },
        "clips": clips,
        "verification": previous.get(
            "verification",
            {
                "browser_playback": "open docs/demo/index.html and confirm all videos play",
                "python_tests": "python -m pytest",
            },
        ),
    }
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    missing = [str(clip.path) for clip in CLIPS if not clip.path.exists()]
    if missing:
        raise FileNotFoundError("Missing source videos: " + ", ".join(missing))

    captures = [cv2.VideoCapture(str(clip.path)) for clip in CLIPS]
    for clip, capture in zip(CLIPS, captures, strict=True):
        if not capture.isOpened():
            raise RuntimeError(f"Could not open {clip.path}")

    fourcc = cv2.VideoWriter_fourcc(*"VP90")
    writer = cv2.VideoWriter(str(OUTPUT_VIDEO), fourcc, FPS, (WIDTH, HEIGHT))
    if not writer.isOpened():
        raise RuntimeError(f"Could not create {OUTPUT_VIDEO}")

    card_boxes = (
        (420, 285, 872, 812),
        (908, 285, 1360, 812),
        (1396, 285, 1848, 812),
    )

    poster_frame = None
    try:
        for frame_index in range(TOTAL_FRAMES):
            frames = read_frame(captures)
            base = make_background(frame_index)
            draw = ImageDraw.Draw(base)
            progress = (frame_index + 1) / TOTAL_FRAMES
            active_index = min(frame_index // 80, 2)
            for idx, (clip, frame, box) in enumerate(zip(CLIPS, frames, card_boxes, strict=True)):
                draw_video_card(base, draw, clip, frame, box, progress, active=idx == active_index)
            draw_bottom(draw, frame_index)

            if frame_index == FPS:
                poster_frame = base.copy()
            writer.write(cv2.cvtColor(np.array(base), cv2.COLOR_RGB2BGR))
    finally:
        writer.release()
        for capture in captures:
            capture.release()

    if poster_frame is None:
        poster_frame = make_background(0)
    poster_frame.save(OUTPUT_POSTER, quality=92)
    write_manifest()
    print(f"Wrote {OUTPUT_VIDEO}")
    print(f"Wrote {OUTPUT_POSTER}")
    print(f"Wrote {OUTPUT_MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
