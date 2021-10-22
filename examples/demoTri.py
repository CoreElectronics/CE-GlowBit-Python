import glowbit

tri = glowbit.triangle(4, pin = 18, rateLimitFPS = 10)

n = 0
while True:
    tri.pixelsFill(0)
    tri.fillTri(n, 0xFFFFFF)
    tri.pixelsShow()
    n += 1
    if n == tri.numTris:
        n = 0

