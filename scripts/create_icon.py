from pathlib import Path

from PIL import Image, ImageDraw


def rounded_rect(draw, xy, radius, fill):
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def draw_logo(size: int) -> Image.Image:
    scale = size / 128
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    def s(value):
        return int(round(value * scale))

    rounded_rect(draw, (0, 0, size, size), s(28), "#111827")
    rounded_rect(draw, (s(24), s(24), s(60), s(60)), s(9), "#FCA5A5")
    rounded_rect(draw, (s(68), s(24), s(104), s(60)), s(9), "#93C5FD")
    rounded_rect(draw, (s(24), s(68), s(60), s(104)), s(9), "#6EE7B7")
    rounded_rect(draw, (s(68), s(68), s(104), s(104)), s(9), "#D1D5DB")

    draw.line(
        [(s(38), s(43.5)), (s(46), s(51)), (s(59), s(36))],
        fill="#7F1D1D",
        width=max(1, s(6)),
        joint="curve",
    )
    draw.line([(s(76), s(42)), (s(96), s(42))], fill="#1E3A8A", width=max(1, s(6)))
    draw.line([(s(76), s(51)), (s(90), s(51))], fill="#1E3A8A", width=max(1, s(6)))
    draw.line([(s(34), s(80)), (s(50), s(80))], fill="#065F46", width=max(1, s(6)))
    draw.line([(s(34), s(92)), (s(54), s(92))], fill="#065F46", width=max(1, s(6)))
    draw.ellipse((s(76), s(76), s(96), s(96)), fill="#4B5563")
    return image


def main():
    output = Path("app/resources/imgs/app_logo.ico")
    output.parent.mkdir(parents=True, exist_ok=True)
    base = draw_logo(256)
    base.save(output, sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])


if __name__ == "__main__":
    main()
