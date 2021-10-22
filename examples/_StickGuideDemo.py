import glowbit

myStick = glowbit.stick()

# Quickstart colour test
myStick.demo()

# Getting a preset colour
# Other options: red(), green(), blue(), yellow(), purple(), cyan(), and black()
colour = myStick.white()
pixelNumber = 0
myStick.pixelSet(pixelNumber, colour)
myStick.pixelsShow()

# Creating an RGB colour
# Each value can be 0 to 255
red = 30
green = 100
blue = 250
colour = myStick.rgbColour(red, green, blue)
pixelNumber = 1
myStick.pixelSet(pixelNumber,colour)
myStick.pixelsShow()

# Creating a spectrum RGB light source
for i in range(255*2):
    colour = myStick.wheel(i)
    myStick.pixelsFill(colour)
    myStick.pixelsShow()

# Creating a rainbow effect with the colourMapRainbow() colour map method
while True:
    for offset in range(33):
        for i in range(8):
            myStick.pixelSet(i, myStick.colourMapRainbow(i, offset, offset+32))
        myStick.pixelsShow()

# Sending pulses when a button is pushed
import machine
switch = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)
n = 0
while True:
    if switch.value() == 0:
        myStick.addPulse(colour=myStick.wheel(n))
        n += 10
    # Make all pixels black
    myStick.pixelsFill(0)
    # Draw any pulses
    myStick.updatePulses()
    # Update the physical LEDs
    myStick.pixelsShow()

# Drawing a graph based on ADC value
import machine
adc = machine.ADC(machine.Pin(26))

myGraph =  myStick.newGraph1D(minIndex = 0, maxIndex = 7, minValue = 0, maxValue = 65535)
while True:
    adcValue = adc.read_u16()
    myStick.updateGraph1D(myGraph, adcValue)
    myStick.pixelsShow()
