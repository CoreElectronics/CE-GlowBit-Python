import glowbit
import time

matrix = glowbit.matrix8x8(tileRows = 3, tileCols = 3, brightness = 0.05, frameBufBrightness = 0.1, rateLimitFPS = 100)

matrix.printTextScroll("This is a long string.", blocking=False, update=False)

for x in range(0, -100, -1):
    matrix.pixelsFill(0)
    matrix.printTextWrap("123456789", x = x, colour = 0xFF)
    matrix.pixelsShow()
