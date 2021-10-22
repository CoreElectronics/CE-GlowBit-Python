import glowbit

myMatrix = glowbit.matrix4x4()

# Quickstart colour test

# myMatrix.demo()

# Getting a preset colour
# Other options: red(), green(), blue(), yellow(), purple(), cyan(), and black()
colour = myMatrix.white()
x = 0
y = 0
myMatrix.pixelSetXY(x,y, colour)
myMatrix.pixelsShow()

print("Press enter to continue")
input()

x = 1
y = 1
myMatrix.pixelSetXY(x,y, colour)
myMatrix.pixelsShow()

print("Press enter to continue")
input()

# Creating an RGB colour
# Each value can be 0 to 255
red = 100
green = 100
blue = 250
colour = myMatrix.rgbColour(red, green, blue)
myMatrix.pixelSetXY(1,2,colour)
myMatrix.pixelsShow()

print("Press enter to continue")
input()

# Updating FPS limit to a higher value
myMatrix.updateRateLimitFPS(80)
# Creating a spectrum RGB light source
for i in range(255):
    colour = myMatrix.wheel(i)
    myMatrix.pixelsFill(colour)
    myMatrix.pixelsShow()

myMatrix.updateRateLimitFPS(30)
# Creating a rainbow effect with the colourMapRainbow() colour map method
n = 10
while n > 0:
    for offset in range(33):
        for i in range(myMatrix.numCols):
            colour = myMatrix.colourMapRainbow(i, offset, offset+32)
            myMatrix.drawLine(i, 0, i, myMatrix.numRows, colour)
        myMatrix.pixelsShow()
    n -= 1

myMatrix.updateRateLimitFPS(10)

g1 = myMatrix.graph1D(originX = 0, originY = 0, length = 4, direction = "Right", minValue = 0, maxValue = 255)
g2 = myMatrix.graph1D(originX = 0, originY = 1, length = 4, direction = "Right", minValue = 0, maxValue = 255)
g3 = myMatrix.graph1D(originX = 0, originY = 2, length = 4, direction = "Right", minValue = 0, maxValue = 255)
g4 = myMatrix.graph1D(originX = 0, originY = 3, length = 4, direction = "Right", minValue = 0, maxValue = 255)

import random

n = 100

while n > 0:
    for g in [g1, g2, g3, g4]:
        x = random.randint(0,255)
        myMatrix.updateGraph1D(g, x)
    myMatrix.pixelsShow()
    n -= 1
