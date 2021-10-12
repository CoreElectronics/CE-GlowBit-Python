import glowbit

matrix = glowbit.matrix8x8(tileRows = 3, tileCols = 3, brightness = 0.05, frameBufBrightness = 0.1, rateLimitFPS = 600)

matrix.drawChar("a", 0,0,0xFF)
matrix.pixelsShow()

#matrix.circularRainbow()

#matrix.blankDisplay()
