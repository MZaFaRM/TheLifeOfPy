import os

assets = os.path.join(os.path.dirname(__file__), "..", "assets")
image_assets = os.path.join(assets, "images")
font_assets = os.path.join(assets, "fonts")

ENV_OFFSET_X = 50
ENV_OFFSET_Y = 100


class Colors:
    bg_color = (26, 26, 26)
    primary = (74, 227, 181)
    error = (255, 0, 0)
    white = (255, 255, 255)


class Fonts:
    # fmt: off
    PixelifySans = os.path.join(font_assets, "PixelifySans", "PixelifySans-Regular.otf")
    PixelifySansBold = os.path.join(font_assets, "PixelifySans", "PixelifySans-Bold.otf")
    PixelifySansBlack = os.path.join(font_assets, "PixelifySans", "PixelifySans-Black.otf")
    PixelifySansMedium = os.path.join(font_assets, "PixelifySans", "PixelifySans-Medium.otf")
    PixelifySansSemiBold = os.path.join(font_assets, "PixelifySans", "PixelifySans-SemiBold.otf")
    PixelifySansExtraBold = os.path.join(font_assets, "PixelifySans", "PixelifySans-ExtraBold.otf")
    
class InvalidConnection(Exception):
    pass
