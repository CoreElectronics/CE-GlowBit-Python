import glowbit
import time
import _thread
from math import cos,sin, pi

#tri = glowbit.triangle(pin=10,sm=3, numTris=4, rateLimitFPS = 5)
#m2 = glowbit.matrix4x4(tiles = 3, pin  = 2, sm=2, rateLimitFPS = 20)
matrix = glowbit.matrix8x8(tileRows = 1, tileCols = 1, pin=18, brightness = 0.1, sm=0, rateLimitFPS=100)
#stick = glowbit.stick(numLEDs = 24, sm=1, rateLimitFPS = 1, brightness=0.1)

matrix.fireworks()

matrix.rain()

matrix.addTextScroll("Testing", blocking=False, update=False)
matrix.addTextScroll("Testing", blocking=False, update=False, y = 8)
matrix.addTextScroll("Testing", blocking=True, y = 16)

g = matrix.graph2D(width = 0, height = 8, originY=7, originX=0, colourMap="Rainbow", bars=True, bgColour = 0xffffff)

x = 0
while x < 20*pi:
    g.addData(127*(sin(x)+1))
    matrix.pixelsFill(0)
    matrix.updateGraph2D(g)
    x += 2*pi/16

matrix.circularRainbow()
matrix.lineDemo()

asdf

g1 = stick.graph1D(minIndex = 5, maxIndex = 5+7, minValue=1, maxValue=8, update=False)
g2 = stick.graph1D(minIndex = 16, maxIndex = 23, minValue=1, maxValue=8, colourMap = "Rainbow")
while True:
    for v in range(9):
        stick.pixelsFill(0)
        stick.updateGraph1D(g1, v)
        stick.updateGraph1D(g2, v)
    for v in range(7,0,-1):
        stick.pixelsFill(0)
        stick.updateGraph1D(g1, v)
        stick.updateGraph1D(g2, v)
        
asdf

# x = 0
# while True:
#     tri.pixelsFill(0)
#     tri.fillTri(x%tri.numTris, 0xFF)
#     tri.pixelsShow()
#     x+=1
# 
# #matrix.printTextScroll("blocking test", update=False, blocking=False)
# #matrix.circularRainbow()
# #m2.circularRainbow()
# 
# asdf

def colourMap1(obj, index: int) -> int:
    return [0xFFFFFF, obj.wheel(20*index)]

def colourMap2(obj, index: int) -> int:
    return [obj.wheel(20*index), 0xFFFFFF]

x = 0
while x < 10000:
    if x % 24 == 0:
        #stick.addPulse(colour=[stick.rgbColour(255,0,0),stick.rgbColour(0,0,0),stick.rgbColour(0,0,255)], speed=-100, index = stick.numLEDs)
        if x % 48 == 0:
            stick.addPulse()
        else:
            stick.addPulse(speed=-100, index=23)
        #stick.addPulse(colour=[stick.rgbColour(255,0,0)], speed=10)
    x += 1
    stick.pixelsFill(0)
    stick.updatePulses()
    stick.pixelsShow()

matrix = glowbit.matrix8x8(tileRows = 3, tileCols = 3, pin=0, brightness = 10, frameBufBrightness=0.1, rateLimitCharactersPerSecond = 200)

tStart = time.ticks_ms()
matrix.circularRainbow()
print(time.ticks_ms() - tStart)

#matrix.printTextScroll("blocking test", update=True, blocking=True, colour = matrix.rgb2rgb565(0,100,0), bgColour = matrix.rgb2rgb565(200,0,0))
#matrix.printTextScroll("blocking test", update=False, blocking=False)
#while matrix.scrollingText:
#    matrix.pixels_show()
#matrix.printTextScroll("1dfgaw54ba4tvsef", y = 0, bgColour = 0x10, update=True)
# matrix.printTextScroll("1dfgaw54ba4tvsef", y = 0, bgColour = 0x10, update=False)
# matrix.printTextScroll("g5a y7bh6gevtvcaszd65q3", y = 8, bgColour = 0x10, update=False)
# matrix.printTextScroll("a ga4w5taw4trfcqwdf5636gqevw45rvwf", y = 16, bgColour = 0x10, update=False)
# 
# 
# 
# while matrix.scrollingText == True:
#     #print(matrix.scrollingText)
#     #time.sleep_ms(2)
#     matrix.pixels_show()

# matrix.printTextScroll("2222", y = 8, bgColour = 0x0, update=False)
# matrix.printTextScroll("3333", y = 16, bgColour = 0x0, update=False)

#while matrix.ScrollingText():
#    matrix.pixels_show()

#matrix.lineDemo()

#matrix.circularRainbow()

# Test framebuffer

# matrix.printTextScroll("this is a long string", y = 0, bgColour = 0x4, update=False)
# matrix.printTextScroll("Middle line is the best", y = 8, bgColour = 0x200, update=False)
# matrix.printTextScroll("LEEROY JENKINS", y = 16, bgColour = 0x8000, update=False)

# First call is Non-Blocking
#matrix.printTextScroll("a", bgColour = 0x2)
#matrix.printTextScroll("this is a long string", y = 0, bgColour = 0x4)
#matrix.printTextScroll("this is a long string", y = 8, bgColour = 0x80)
#matrix.printTextScroll("this is a long string", y = 16, bgColour = 0x2000)
# Second call blocks
#matrix.printTextScroll("CORE 0 - I love multithreading", y=12, x = 3, bgColour = 0x0080)

'''
# Draw a line

while True:
    y0 = 5
    x1 = matrix.numLEDsX-5
    y2 = matrix.numLEDsY-5
    for i in range(10):
        x0 = 5+i
        y1 = 5+i
        x2 = 15-i
        matrix.pixels_fill((0,0,0))
        matrix.drawTriangle(round(x0), round(y0), round(x1), round(y1), round(x2), round(y2), (10,10,10))
        matrix.drawRectangle(round(x0), round(y0), round(x2), round(y2), (0, 10, 0))
        matrix.pixels_set_xy(round(x0), round(y0), (10,0,0))
        matrix.pixels_set_xy(round(x1), round(y1), (0,10,0))
        matrix.pixels_set_xy(round(x2), round(y2), (0,0,10))
        
        matrix.pixels_show()
    for i in range(10, 0, -1):
        x0 = 5+i
        y1 = 5+i
        x2 = 15-i
        matrix.pixels_fill((0,0,0))
        matrix.drawTriangle(round(x0), round(y0), round(x1), round(y1), round(x2), round(y2), (10,10,10))
        matrix.drawRectangle(round(x0), round(y0), round(x2), round(y2), (0, 10, 0))
        matrix.pixels_set_xy(round(x0), round(y0), (10,0,0))
        matrix.pixels_set_xy(round(x1), round(y1), (0,10,0))
        matrix.pixels_set_xy(round(x2), round(y2), (0,0,10))
        matrix.pixels_show()
        
        
        
        
'''
