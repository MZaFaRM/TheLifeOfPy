import os

assets = os.path.join(os.path.dirname(__file__), "assets")
image_assets = os.path.join(assets, "images")
font_assets = os.path.join(assets, "fonts")


class Colors:
    bg_color = (26, 26, 26)
    primary = (74, 227, 181)


class Fonts:
    # fmt: off
    PixelifySans = os.path.join(font_assets, "PixelifySans", "PixelifySans-Regular.ttf")
    PixelifySansBold = os.path.join(font_assets, "PixelifySans", "PixelifySans-Bold.ttf")
    PixelifySansMedium = os.path.join(font_assets, "PixelifySans", "PixelifySans-Medium.ttf")
    PixelifySansSemiBold = os.path.join(font_assets, "PixelifySans", "PixelifySans-SemiBold.ttf")
