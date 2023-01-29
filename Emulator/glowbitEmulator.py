import sys
sys.path.insert(0, '../glowbit')
import glowbit
import os
from colorama import Fore, Back, Style
from time import sleep 

class WSE:
    def PixelStrip(self, numLEDs: int, pin :int):
        return self

    def begin(self):
        return None
    
    def setPixelColor(self, x: int, colour: int):
        return None
    
    def show(self):
        return None
        
ws = WSE()   

class matrix8x8(glowbit.matrix8x8):

    def __init__(self, tileRows = 1, tileCols = 1, pin = 18, brightness = 20, mapFunction = None, rateLimitFPS = -1, rateLimitCharactersPerSecond = -1, sm = 0):
        self.tileRows = tileRows
        self.tileCols = tileCols
        self.numLEDs = tileRows*tileCols*64
        self.numLEDsX = tileCols*8
        self.numLEDsY = tileRows*8
        self.numCols = self.numLEDsX
        self.numRows = self.numLEDsY
        
        self.strip = ws.PixelStrip(self.numLEDs, pin)
        self.strip.begin()
        self.pixelsShow = self._pixelsShowRPi
        self.ticks_ms = self._ticks_ms_Linux

        super().__init__(tileRows, tileCols, pin, brightness, mapFunction, rateLimitFPS, rateLimitCharactersPerSecond, sm)
        self.pixelsShow = self.draw

    def getColor(self, row: int, col: int):
        colInt = self.ar[self.remap(col, row)]
        r = (colInt&0xFF0000) >> 16 
        g = (colInt&0xFF00)>> 8
        b = (colInt&0xFF)
        # need a better way to do this
        if (r >= 150 and g < 150 and b < 150):
            return Fore.RED
        if (r < 150 and g >= 150 and b < 150):
            return Fore.GREEN
        if (r < 150 and g < 150 and b >= 150):
            return Fore.BLUE
        if (r >= 150 and g >= 150 and b < 150):
            return Fore.YELLOW
        if (r >= 150 and g >= 150 and b >= 150):
            return Fore.WHITE
        if (r < 50 and g < 50 and b < 50):
            return Fore.BLACK
        return Fore.MAGENTA

    def draw(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        for r in range (self.tileRows*8):
            for c in range (self.tileCols*8):
                col = self.getColor(r, c)
                print(Back.BLACK + col + '■', end=' ') 
            print()
        print(Style.RESET_ALL)
        sleep(0.25)
    

    def blankDisplay(self):
        for i in range(int(len(self.ar))):
            self.ar[i] = self.rgbColour(0,0,0)
        self.pixelsShow()
    

