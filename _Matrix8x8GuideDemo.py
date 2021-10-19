import glowbit
import math

myMatrix = glowbit.matrix8x8()

# Play an array of demos
# myMatrix.demo()

# Setting a pixel in the top left corner with a preset clolour
colour = myMatrix.yellow()
x = 0
y = 0
myMatrix.pixelSetXY(x,y,colour)
myMatrix.pixelsShow()

# Setting a pixel near the middle of the display a given RGB colour
r = 80
g = 100
b = 200
colour = myMatrix.rgbColour(r, g, b)
myMatrix.pixelSetXY(3,4, colour)
myMatrix.pixelsShow()

# Filling the screen with RGB eye candy

myMatrix.updateRateLimitFPS(100)
for i in range(255):
    colour = myMatrix.wheel(i)
    myMatrix.pixelsFill(colour)
    myMatrix.pixelsShow()


# Sine wave graph

sinGraph = myMatrix.graph2D(minValue=-1, maxValue=1, update=True)

myMatrix.updateRateLimitFPS(15)

while True:
    t = myMatrix.ticks_ms()/1000
    myMatrix.updateGraph2D(sinGraph, math.sin(2*math.pi*1*t))

