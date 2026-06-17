#!/usr/bin/env python3
"""
封面 SVG -> PNG 渲染器（沙箱适配）。

为什么需要它：沙箱通常没有 PingFang；自带中文字体 Droid Sans Fallback
不含拉丁字母和数字 —— 直接转 PNG 会让中文或英文数字变成方框 □。
本脚本按字符类型分别指定字体：中文用 Droid Sans Fallback，
纯西文元素 / 中英混排里的数字字母片段用 Liberation Sans。

依赖：pip install cairosvg --break-system-packages -q

用法：
    python3 render_cover.py 输入.svg 输出.png [宽 高]
    例：python3 render_cover.py cover.svg cover.png 1800 766

适配自定义封面：脚本对模板里的西文文本做了精准替换。
如果你改了封面文案/结构，按需调整下面 REPLACEMENTS 里的匹配串，
原则是——任何"纯西文/数字"或"中英混排"的 <text> 都要把西文片段
包进 <tspan font-family="Liberation Sans">...</tspan>。
渲染后务必用 Read 工具看一眼 PNG，确认没有方框。
"""
import sys
import cairosvg

CJK_FONT = "Droid Sans Fallback"   # 沙箱自带中文字体
LATIN_FONT = "Liberation Sans"      # 沙箱自带西文字体（Arial 替代）

# (查找串, 替换串)：把西文片段单独指定字体
REPLACEMENTS = [
    ("'PingFang SC','Microsoft YaHei',sans-serif", CJK_FONT),
    # 纯西文元素
    ('letter-spacing="3">WEEKLY TECH',
     f'font-family="{LATIN_FONT}" letter-spacing="3">WEEKLY TECH'),
    ('opacity="0.95">6.07 — 6.13',
     f'font-family="{LATIN_FONT}" opacity="0.95">6.07 — 6.13'),
    # 中英混排副标题：数字/符号片段用西文字体，中文留给根字体
    ('>5 条要闻 · 3 分钟读完<',
     f'><tspan font-family="{LATIN_FONT}">5 </tspan>条要闻'
     f'<tspan font-family="{LATIN_FONT}"> · 3 </tspan>分钟读完<'),
]


def main():
    if len(sys.argv) < 3:
        print("用法: python3 render_cover.py 输入.svg 输出.png [宽 高]")
        sys.exit(1)
    src, dst = sys.argv[1], sys.argv[2]
    w = int(sys.argv[3]) if len(sys.argv) > 3 else 1800
    h = int(sys.argv[4]) if len(sys.argv) > 4 else 766

    svg = open(src, encoding="utf-8").read()
    for find, repl in REPLACEMENTS:
        svg = svg.replace(find, repl)

    cairosvg.svg2png(bytestring=svg.encode("utf-8"),
                     write_to=dst, output_width=w, output_height=h)
    print(f"已生成 {dst} ({w}x{h})。请用 Read 工具检查是否有方框 □。")


if __name__ == "__main__":
    main()
