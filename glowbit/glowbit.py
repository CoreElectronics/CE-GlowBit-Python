import os
_SYSNAME = os.uname().sysname

if _SYSNAME == 'rp2':
    from machine import Pin
    import micropython
    import rp2

if _SYSNAME == 'Linux':
    import rpi_ws281x as ws

    # Dummy ptr32() for within micropython.viper
    def ptr32(arg):
        return arg
    # Dummy class for @micropython decorator
    class micropython():
        def viper(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
    
    # Dummy class for @rp2 decorator
    class rp2():
        class PIO():
            OUT_LOW = None
            SHIFT_LEFT = None
        def asm_pio(sideset_init, out_shiftdir, autopull, pull_thresh):
            def wrapper(*argx, **kwargs):
                return None
            return wrapper 


from petme128 import petme128
import time
import array
import gc


## @brief
#
# Methods for transforming colours to 32-bit packed GlowBit colour values
#
# A packed 32-bit GlowBit colour is an integer with 8-bits per colour channel data encoded in hexadecimal as follows:
# 
# 0x00RRGGBB
#
# where RR, GG, and BB are hexadecimal values (decimal [0,255]) and the most significant 8 bits are reserved and left as zero.

class colourFunctions():

    ## @brief Converts an integer "colour wheel position" to a packed 32-bit RGB GlowBit colour value.
    #
    # The "pos" argument is required as this is a micropython viper function.
    #
    # \param pos: Colour wheel position [0,255] is mapped to a pure hue in the RGB colourspace. A value of 0 or 255 is mapped to pure red with a smooth red-yellow-green-blue-purple-magenta-red transion for other values.
    # \return 32-bit integer GlowBit colour value

    @micropython.viper
    def wheel(self,pos: int) -> int:
        # Input a value 0 to 255 to get a color value.
        # The colours are a transition r - g - b - back to r.
        pos = pos % 255
        if pos < 85:
            return ((255 - pos * 3)<<16) |  ((pos * 3)<<8)
        if pos < 170:
            pos -= 85
            return ((255 - pos * 3)<<8 | (pos * 3))
        pos -= 170
        return ((pos * 3)<<16) | (255 - pos * 3)
    
    ## @brief Converts the r, g, and b integer arguments to a packed 32-bit RGB GlowBit colour value
    #
    # All arguments are required as this is a micropython viper function.
    #
    # \param r: The red intensity, [0,255]
    # \param g: The green intensity, [0,255]
    # \param b: The blue intensity, [0,255]
    # \return Packed 32-bit GlowBit colour value

    @micropython.viper
    def rgbColour(self, r: int, g: int, b: int) -> int:
        return ( (r<<16) | (g<<8) | b )
   
    ## @brief Converts a 32-bit GlowBit colour value to an (R,G,B) tuple.
    #
    # \param colour A 32-bit GlowBit colour value
    # \return A tuple in the format (R,G,B) containing the RGB components of the colour parameter

    def glowbitColour2RGB(self, colour):
        return ( (colour&0xFF0000) >> 16 , (colour&0xFF00)>> 8, (colour&0xFF) )

    ## @brief Returns the GlowBit colour value for pure red
    def red(self):
        return 0xFF0000

    ## @brief Returns the GlowBit colour value for pure green
    def green(self):
        return 0x00FF00

    ## @brief Returns the GlowBit colour value for pure blue
    def blue(self):
        return 0x0000FF

    ## @brief Returns the GlowBit colour value for yellow
    def yellow(self):
        return 0xFFFF00

    ## @brief Returns the GlowBit colour value for purple
    def purple(self):
        return 0xFF00FF

    ## @brief Returns the GlowBit colour value for cyan
    def cyan(self):
        return 0x00FFFF

    ## @brief Returns the GlowBit colour value for white
    def white(self):
        return 0xFFFFFF

    ## @brief Returns the GlowBit colour value for black
    def black(self):
        return 0x000000

## @brief Methods which calculate colour gradients.
#
# Custom colour map methods can be written and passed to several GlowBit library methods (eg: glowbit.stick.graph1D) but must accept the same positional arguments as the methods in this class:
#
# def colourMapFunction(self, index, minIndex, maxIndex):

class colourMaps():

    ## @brief Trivial colourmap method which always returns the colour in the parent object.
    #
    # \param index Dummy argument for compatibility with colourmap method API
    # \param minIndex Dummy argument for compatibility with colourmap method API
    # \param maxIndex Dummy argument for compatibility with colourmap method API

    def colourMapSolid(self, index, minIndex, maxIndex):
        return self.colour
        

    ## @brief Maps the pure hue colour wheel between minIndex and maxIndex
    #
    # \param index The value to be mapped
    # \param minIndex The value of index mapped to a colour wheel angle of 0 degrees
    # \param maxIndex The value of index mapped to a colour wheel angle of 360 degrees
    # \return The 32-bit packed GlowBit colour value 

    def colourMapRainbow(self, index, minIndex, maxIndex):
        return self.wheel(int(((index-minIndex)*255)/(maxIndex-minIndex)))

## @brief Low-level methods common to all GlowBit classes

class glowbit(colourFunctions, colourMaps):
    @rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
    def _ws2812():
        T1 = 2
        T2 = 5
        T3 = 3
        wrap_target()
        label("bitloop")
        out(x, 1)               .side(0)    [T3 - 1]
        jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
        jmp("bitloop")          .side(1)    [T2 - 1]
        label("do_zero")
        nop()                   .side(0)    [T2 - 1]
        wrap()

    @micropython.viper
    def _pixelsShowPico(self):
        self.__syncWait()
        gc.collect()
        ar = self.dimmer_ar
        br = int(self.brightness)
        for i,c in enumerate(self.ar):
            r = int((((int(c) >> 16) & 0xFF) * br) >> 8)
            g = int((((int(c) >> 8) & 0xFF) * br) >> 8)
            b = int(((int(c) & 0xFF) * br) >> 8)
            ar[i] = (g<<16) | (r<<8) | b    
            self.sm.put(ar[i], 8)

    def _pixelsShowRPi(self):
        self.__syncWait()
        br = self.brightness
        for i,c in enumerate(self.ar):
            r = int((((int(c) >> 16) & 0xFF) * br) >> 8)
            g = int((((int(c) >> 8) & 0xFF) * br) >> 8)
            b = int(((int(c) & 0xFF) * br) >> 8)
            self.strip.setPixelColor(i, (r<<16) | (g<<8) | b)
        self.strip.show()
   
    def __syncWait(self):
        while self.ticks_ms() < (self.lastFrame_ms + 1000 // self.rateLimit):
            continue
        self.lastFrame_ms = self.ticks_ms()
    
    def _ticks_ms_Linux(self):
        return time.time()*1000
          

    ## @brief Pushes the internal pixel data buffer to the physical GlowBit LEDs
    # 
    # This function must be called before the connected GlowBit LEDs will change colour.
    # 
    # Note that several GlowBit library methods call this method unconditionally (eg: glowbit.blankDisplay ) or optionally (eg: by passing the update = True parameter to stick.graph1D() )
    def pixelsShow(self):
        return

    ## @brief Sets the i'th GlowBit LED to a 32-bit GlowBit colour value.
    # 
    # NB: For efficiency, this method does not do any bounds checking. If the value of the parameter i is larger than the number of LEDs it will cause an IndexError exception.
    #
    # \param i An LED's index
    # \param colour The 32-bit GlowBit colour value

    @micropython.viper
    def pixelSet(self, i: int, colour: int):
        self.ar[i] = colour
    
    ## @brief Sets the i'th GlowBit LED to a 32-bit GlowBit colour value and updates the physical LEDs.
    # 
    # NB: For efficiency, this method does not do any index bounds checking. If the value of the parameter i is larger than the number of LEDs it will cause an IndexError exception.
    #
    # \param i An LED's index
    # \param colour The 32-bit GlowBit colour value

    @micropython.viper
    def pixelSetNow(self, i: int, colour: int):
        self.ar[i] = colour
        self.pixelsShow()
        
    ## @brief Adds a 32-bit GlowBit colour value to the i'th LED in the internal buffer only.
    #
    # Data colour corruption will occur if the sum result of any RGB value exceeds 255. Care must be taken to avoid this manually. eg: if the blue channel's resulting intensity value is 256 it will be set to zero and the red channel incremented by 1. See the colourFunctions class documentation for the 32-bit GlowBit colour specification.
    #
    # NB: For efficiency, this method does not do any index bounds checking. If the value of the parameter i is larger than the number of LEDs it will cause an IndexError exception.
    #
    # \param i An LED's index
    # \param colour The 32-bit GlowBit colour value
    # 

    @micropython.viper
    def pixelAdd(self, i: int, colour: int):
        tmp = int(self.ar[i]) + colour
        self.ar[i] = tmp
 
    ## @brief Adds a 32-bit GlowBit colour value to the i'th LED in the internal buffer. This function performs "saturating" arithmetic. It is much slower than pixelAdd but will saturate at 255 to avoid data corruption.
    #
    # NB: For efficiency, this method does not do any index bounds checking. If the value of the parameter i is larger than the number of LEDs it will cause an IndexError exception.
    #
    # \param i An LED's index
    # \param colour The 32-bit GlowBit colour value
    # 

    @micropython.viper
    def pixelSaturatingAdd(self, i: int, colour: int):
        tmp = int(self.ar[i])
        r = (colour & 0xFF0000) >> 16
        g = (colour & 0x00FF00) >> 8
        b = (colour & 0x0000FF)
        
        r2 = (tmp & 0xFF0000) >> 16
        g2 = (tmp & 0x00FF00) >> 8
        b2 = (tmp & 0x0000FF)

        r3 = r + r2
        g3 = g + g2
        b3 = b + b2

        if r3 > 255:
            r3 = 255
        if g3 > 255:
            g3 = 255
        if b3 > 255:
            b3 = 255

        self.ar[i] = (r3 << 16) + (g3 << 8) + b3
           
    ## @brief Fills all pixels with a solid colour value
    #
    # \param colour The 32-bit GlowBit colour value

    @micropython.viper
    def pixelsFill(self, colour: int):
        ar = self.ar
        for i in range(int(len(self.ar))):
            ar[i] = colour
            
    ## @brief Fills all pixels with a solid colour value and updates the physical LEDs.
    #
    # \param colour The 32-bit GlowBit colour value

    @micropython.viper
    def pixelsFillNow(self, colour: int):
        ar = ptr32(self.ar)
        for i in range(int(len(self.ar))):
            ar[i] = colour
        self.pixelsShow()
        
    ## @brief Blanks the entire GlowBit display. ie: sets the colour value of all GlowBit LEDs to zero in the internal buffer and updates the physical LEDs.
    #
    #

    @micropython.viper
    def blankDisplay(self):
        ar = self.ar
        for i in range(int(len(self.ar))):
            ar[i] = 0
        self.pixelsShow()
  

    ## @brief Returns the 32-bit GlowBit colour value of the i'th LED
    #
    # \param i The index of the LED
    # \return The 32-bit GlowBit colour value of the i'th LED

    def getPixel(self, N):
        return self.ar[N]

    ## @brief Sets a new value for the GlowBit display's frames per second (FPS) limiter.
    #
    # \param rateLimitFPS An integer in units of frames per second.

    def updateRateLimitFPS(self, rateLimitFPS):
        self.rateLimit = rateLimitFPS

    ## @brief Calculates an estimate for the total power draw given the current display data. Use as a general guide only, error range is around 10-20%.
    #
    # The estimate is a 4th order polynomical interpolation given measurements of white brightness. The power consumption of pure colours will tend to be under-estimated by up to about 10-20%.
    #
    # Data was measured at a supply voltage of 3.3V but supply current was not found to vary significantly with supply voltage.
    #
    # \return The current consumption of the framebuffer in amps.
    def power(self):
        p = 0
        for i in range(self.numLEDs):
            (r,g,b) = self.glowbitColour2RGB(self.ar[i])
            x = (r+g+b)*self.brightness/255
            p += (6.74277e-14*x**4)- (1.25707e-10*x**3) + (8.07761e-8*x**2) + (2.30660e-5*x) + 4.61474e-4
        return p

    ## @brief Sets random colour values on every LED on the attached GlowBit display. This function is blocking, it does not return until the number of frames specified in the iters parameter have been drawn.
    #
    # \param iters The number of frames to draw.

    def chaos(self, iters = 100):
        import random
        ar = self.ar
        while iters > 0:
            for i in range(int(self.numLEDs)):
                ar[i] = int(random.randint(0, 0xFFFFFF))
            self.pixelsShow()
            iters -= 1
        self.blankDisplay()

## @brief Methods specific to 2D matrix displays and tiled arrangements thereof.
#
# This class should not be used directly; its methods are inherited by the glowbit.matrix8x8 and glowbit.matrix4x4 classes.

class glowbitMatrix(glowbit):

    ## @brief Sets the colour value of the GlowBit LED at a given x-y coordinate
    #
    # The coordinate assumes an origin in the upper left of the display with x increasing to the right and y increasing downwards.
    #
    # If the x-y coordinate falls outside the display's boundary this function will "wrap-around". For example, A dot placed just off the right edge will appear along the left edge in the same row.
    #
    # Advanced: If seeking maximum speed consider modifying the ar[] array directly
    #
    # \param x The x coordinate of the GlowBit LED. x must be an integer.
    # \param y The y coordinate of the GlowBit LED. y must be an integer.
    # \param colour A packed 32-bit GlowBit colour value

    @micropython.viper
    def pixelSetXY(self, x: int, y: int, colour: int):
        x = x % int(self.numLEDsX)
        y = y % int(self.numLEDsY)
        self.ar[int(self.remap(x,y))] = colour
   
    ## @brief Sets the colour value of the GlowBit LED at a given x-y coordinate and immediately calls pixelsShow() to update the physical LEDs.
    #
    # The coordinate assumes an origin in the upper left of the display with x increasing to the right and y increasing downwards.
    #
    # If the x-y coordinate falls outside the display's boundary this function will "wrap-around". For example, A dot placed just off the right edge will appear along the left edge.
    # 
    # Advanced: If seeking maximum speed consider modifying the ar[] array directly
    #
    # \param x The x coordinate of the GlowBit LED. x must be an integer.
    # \param y The y coordinate of the GlowBit LED. y must be an integer.
    # \param colour A packed 32-bit GlowBit colour value

    @micropython.viper
    def pixelSetXYNow(self, x: int, y: int, colour: int):
        x = x % int(self.numLEDsX)
        y = y % int(self.numLEDsY)
        i = int(self.remap(x,y))
        self.ar[i % int(self.numLEDs)] = colour
        self.pixelsShow()
    
    ## @brief Sets the colour value of the GlowBit LED at a given x-y coordinate
    #
    # The coordinate assumes an origin in the upper left of the display with x increasing to the right and y increasing downwards.
    #
    # If the x-y coordinate falls outside the display's boundary the display's internal buffer will not be modified. 
    #
    # \param x The x coordinate of the GlowBit LED. x must be an integer.
    # \param y The y coordinate of the GlowBit LED. y must be an integer.
    # \param colour A packed 32-bit GlowBit colour value
 
    @micropython.viper
    def pixelSetXYClip(self, x: int, y: int, colour: int):
        if x >= 0 and y >= 0 and x < int(self.numLEDsX) and y < int(self.numLEDsY):
            self.ar[int(self.remap(x,y))] = colour

    ## @brief Adds the colour value to the GlowBit LED at a given (x,y) coordinate
    #
    # The coordinate assumes an origin in the upper left of the display with x increasing to the right and y increasing downwards.
    #
    # If the x-y coordinate falls outside the display's boundary this function will "wrap-around". For example, A dot placed just off the right edge will appear along the left edge.
    #
     # Data colour corruption will occur if the sum result of any RGB value exceeds 255. Care must be taken to avoid this manually. eg: if the blue channel's resulting intensity value is 256 it will be set to zero and the red channel incremented by 1. See the colourFunctions class documentation for the 32-bit GlowBit colour specification.
    #
    # \param x The x coordinate of the GlowBit LED. x must be an integer.
    # \param y The y coordinate of the GlowBit LED. y must be an integer.
    # \param colour A packed 32-bit GlowBit colour value

    @micropython.viper
    def pixelAddXY(self, x: int, y: int, colour: int):
        x = x % int(self.numLEDsX)
        y = y % int(self.numLEDsY)
        i = int(self.remap(x,y))
        self.ar[i] = int(self.ar[i]) + colour

    ## @brief Adds the colour value to the GlowBit LED at a given (x,y) coordinate
    #
    # The coordinate assumes an origin in the upper left of the display with x increasing to the right and y increasing downwards.
    #
    # If the x-y coordinate falls outside the display's boundary the display's internal buffer will not be modified. 
    #
     # Data colour corruption will occur if the sum result of any RGB value exceeds 255. Care must be taken to avoid this manually. eg: if the blue channel's resulting intensity value is 256 it will be set to zero and the red channel incremented by 1. See the colourFunctions class documentation for the 32-bit GlowBit colour specification.
    #
    # \param x The x coordinate of the GlowBit LED. x must be an integer.
    # \param y The y coordinate of the GlowBit LED. y must be an integer.
    # \param colour A packed 32-bit GlowBit colour value

    @micropython.viper
    def pixelAddXYClip(self, x: int, y: int, colour: int):
        if x >= 0 and y >= 0 and x < int(self.numLEDsX) and y < int(self.numLEDsY):
            self.ar[int(self.remap(x,y))] = colour + int(self.ar[int(self.remap(x,y))])
   
    ## @brief Returns the 32-bit GlowBit colour value of the LED at a given (x,y) coordinate
    #
    # If the (x,y) coordinate falls outside of the display's boundary an IndexError exception may be thrown or the GlowBit colour value of an undefined pixel may be returned.
    #
    # \param i The index of the LED
    # \return The 32-bit GlowBit colour value of the i'th LED

    def getPixelXY(self, x, y):
        return self.ar[remap(x,y)]

    ## @brief Draws a straight line between (x0,y0) and (x1,y1) in the specified 32-bit GlowBit colour.
    #
    # If pixel is drawn off the screen a "clipping" effect will be inherited from the behaviour of pixelSetXYClip(). ie: Pixels landing off the screen will not be drawn.
    #
    # \param x0 The line's starting x coordinate
    # \param y0 The line's starting y coordinate
    # \param x1 The line's ending x coordinate
    # \param y1 The line's ending y coordinate
    # \param colour A packed 32-bit GlowBit colour value

    @micropython.viper
    def drawLine(self, x0: int, y0: int, x1: int, y1: int, colour: int):
        steep = abs(y1-y0) > abs(x1-x0)
        
        if steep:
            # Swap x/y
            tmp = x0
            x0 = y0
            y0 = tmp
            
            tmp = y1
            y1 = x1
            x1 = tmp
        
        if x0 > x1:
            # Swap start/end
            tmp = x0
            x0 = x1
            x1 = tmp
            tmp = y0
            y0 = y1
            y1 = tmp
        
        dx = x1 - x0;
        dy = int(abs(y1-y0))
        
        err = dx >> 1 # Divide by 2
        
        if(y0 < y1):
            ystep = 1
        else:
            ystep = -1
            
        while x0 <= x1:
            if steep:
                self.pixelSetXYClip(y0, x0, colour)
            else:
                self.pixelSetXYClip(x0, y0, colour)
            err -= dy
            if err < 0:
                y0 += ystep
                err += dx
            x0 += 1
       
    ## @brief Draws a triangle with vertices (corners) at (x0,y0), (x1, y1), and (x2,y2). All lines are drawn with the specified colour.
    #
    # If pixel is drawn off the screen a "clipping" effect will be inherited from the behaviour of pixelSetXYClip(). ie: Pixels landing off the screen will not be drawn.
    #
    # \param x0 The x coordinate of the first vertex
    # \param y0 The y coordinate of the first vertex
    # \param x1 The x coordinate of the second vertex
    # \param y1 The y coordinate of the second vertex
    # \param x2 The x coordinate of the third vertex
    # \param y2 The y coordinate of the third vertex
    # \param colour A packed 32-bit GlowBit colour value

    def drawTriangle(self, x0,y0, x1, y1, x2, y2, colour):
        self.drawLine(x0, y0, x1, y1, colour)
        self.drawLine(x1, y1, x2, y2, colour)
        self.drawLine(x2, y2, x0, y0, colour)
     
    ## @brief Draws a rectangle with upper-left corner (x0,y0) and lower right corner (x1, y1). All edge lines are drawn with the specified colour.
    # 
    # Pixels inside the rectangle are left unmodified.
    #
    # If pixel is drawn off the screen a "clipping" effect will be inherited from the behaviour of pixelSetXYClip(). ie: Pixels landing off the screen will not be drawn.
    #
    # \param x0 The x coordinate of the upper left corner
    # \param y0 The y coordinate of the upper left corner
    # \param x1 The x coordinate of the lower right corner
    # \param y1 The y coordinate of the lower right corner
    # \param colour A packed 32-bit GlowBit colour value

    def drawRectangle(self, x0, y0, x1, y1, colour):
        self.drawLine(x0, y0, x1, y0, colour)
        self.drawLine(x1, y0, x1, y1, colour)
        self.drawLine(x1, y1, x0, y1, colour)
        self.drawLine(x0, y1, x0, y0, colour)
   
    ## @brief Draws a rectangle with upper-left corner (x0,y0) and lower right corner (x1, y1). The rectangle is then filled to form a solid block of the specified colour.
    #
    # This method overwrites pixel data with the colour value.
    #
    # If pixel is drawn off the screen a "clipping" effect will be inherited from the behaviour of pixelSetXYClip(). ie: Pixels landing off the screen will not be drawn.
    #
    # \param x0 The x coordinate of the upper left corner
    # \param y0 The y coordinate of the upper left corner
    # \param x1 The x coordinate of the lower right corner
    # \param y1 The y coordinate of the lower right corner
    # \param colour A packed 32-bit GlowBit colour value

    @micropython.viper
    def drawRectangleFill(self, x0: int, y0: int, x1: int, y1: int, colour):
        for x in range(x0, x1+1):
            for y in range(y0, y1+1):
                self.pixelSetXY(x,y,colour)

    ## @brief Draws a rectangle with upper-left corner (x0,y0) and lower right corner (x1, y1). The rectangle is then filled to form a solid block of the specified colour.
    #
    # This method adds a colour to every pixel, allowing a rectangle to be drawn over the top of other pixel data.
    #
    # If pixel is drawn off the screen a "clipping" effect will be inherited from the behaviour of pixelSetXYClip(). ie: Pixels landing off the screen will not be drawn.
    #
    # \param x0 The x coordinate of the upper left corner
    # \param y0 The y coordinate of the upper left corner
    # \param x1 The x coordinate of the lower right corner
    # \param y1 The y coordinate of the lower right corner
    # \param colour A packed 32-bit GlowBit colour value

    @micropython.viper
    def drawRectangleFillAdd(self, x0: int, y0: int, x1: int, y1: int, colour):
        for x in range(x0, x1+1):
            for y in range(y0, y1+1):
                self.pixelAddXY(x,y,colour)

    ## @brief Draws a circle with center (x0,y0) and radius r. The circle's outline is drawn in the specified colour. Pixels inside the circle are not modified.
    # 
    # \param x0 The x coordinate of the circle's center
    # \param y0 The y coordinate of the circle's center
    # \param colour A packed 32-bit GlowBit colour value

    def drawCircle(self, x0, y0, r, colour):
        f = 1-r
        ddf_x = 1
        ddf_y = -2*r
        x = 0
        y = r
        self.pixelSetXYClip(x0, y0 + r, colour)
        self.pixelSetXYClip(x0, y0 - r, colour)
        self.pixelSetXYClip(x0 + r, y0, colour)
        self.pixelSetXYClip(x0 - r, y0, colour)
        
        while x < y:
            if f >= 0: 
                y -= 1
                ddf_y += 2
                f += ddf_y
            x += 1
            ddf_x += 2
            f += ddf_x
            self.pixelSetXYClip(x0 + x, y0 + y, colour)
            self.pixelSetXYClip(x0 - x, y0 + y, colour)
            self.pixelSetXYClip(x0 + x, y0 - y, colour)
            self.pixelSetXYClip(x0 - x, y0 - y, colour)
            self.pixelSetXYClip(x0 + y, y0 + x, colour)
            self.pixelSetXYClip(x0 - y, y0 + x, colour)
            self.pixelSetXYClip(x0 + y, y0 - x, colour)
            self.pixelSetXYClip(x0 - y, y0 - x, colour)
   
    ## @brief One dimensional graph object for graph bars on GlowBit Matrix displays.
    class graph1D(colourFunctions, colourMaps):

        ## @brief Initialisation routine for the glowbit.matrix.graph1D object. A graph1D object will be drawn with a fixed width of 1 pixel and arbitrary length.
        #
        # \param originX The x coordinate of the graph's origin. The "minValue" argument will be mapped to this pixel.
        # \param originY The y coordinate of the graph's origin. The "minValue" argument will be mapped to this pixel.
        # \param length The length, in pixels, of the graph's drawing area.
        # \param direction One of "Up", "Down", "Left", or "Right". Specifies the direction in which the graph will be drawn.
        # \param minValue The value which will be mapped to the origin.
        # \param maxValue The value which will be mapped to the 'end' of the graph. The (x,y) coordinate will be 'length' pixels away from the origin in the direction specified by 'direction'.
        # \param colour A packed 32-bit GlowBit colour value. Used by the "Solid" colourmap, ignored by the "Rainbow" colourmap. Can also be accessed when writing custom colour map functions.
        # \param colourMap Either the string "Solid" or "Rainbow" or a pointer to a custom colour map function. Custom colour maps must take the parameters colourMap(self, index, minIndex, maxIndex).
        # \param update If update=True then a call to updateGraph1D() will, in turn, call glowbit.pixelsShow() to update the physical LEDs.
        def __init__(self, originX = 0, originY = 7, length = 8, direction = "Up", minValue=0, maxValue=255, colour = 0xFFFFFF, colourMap = "Solid", update = False):
            self.minValue = minValue
            self.maxValue = maxValue
            self.originX = originX
            self.originY = originY
            self.length = length

            self.orientation = -1
            self.inc = 0
            if direction == "Up":
                self.orientation = 1
                self.inc = -1 # Y decreases towards the top
            if direction == "Down":
                self.orientation = 1
                self.inc = 1 # Y increases down
            if direction == "Left":
                self.orientation = 0
                self.inc = -1
            if direction == "Right":
                self.orientation = 0
                self.inc = 1
            
            if self.orientation == -1 or self.inc == 0:
                print("Invalid direction \"", direction, "\".")
                print("Valid options: Up, Down, Left, Right")
                print("Defaulting to Up")
                self.orientation = 1
                self.inc = 1

            self.m = (length)/(maxValue-minValue)
            self.update = update
            self.colour = colour

            if callable(colourMap) == True:
                self.colourMap = colourMap
            elif colourMap == "Solid":
                self.colourMap = self.colourMapSolid
            elif colourMap == "Rainbow":
                self.colourMap = self.colourMapRainbow
   
    ## @brief Wrapper method to create a graph1D object
    #
    # Calling matrix.graph1D() directly is recommended - this is only here so that it appears more clearly in the Doxygen.

    def newGraph1D(self,originX = 0, originY = 7, length = 8, direction = "Up", minValue=0, maxValue=255, colour = 0xFFFFFF, colourMap = "Solid", update = False):
        return self.graph1D(originX, originY, length, direction, minValue, maxValue, colour, colourMap, update)

    ## @brief Updates a graph1D object, draws it to the display buffer.
    #
    # If the graph1D object was created with "update = True" this function will call pixelsShow() to update the physical display before returning.
    #
    # \param graph A graph1D object as returned by glowbitMatrix.graph1D()
    # \param value The value to draw to the graph. It will be mapped to the graph bet

    def updateGraph1D(self, graph, value):
        N = round(graph.m*(value - graph.minValue))

        m = graph.colourMap
        if graph.orientation == 1:
            n = 0
            for idxY in range(graph.originY, graph.originY+graph.inc*(graph.length), graph.inc):
                if n < N:
                    self.pixelSetXY(graph.originX, idxY, m(idxY, graph.originY, graph.originY+(graph.inc*graph.length-1)))
                else:
                    self.pixelSetXY(graph.originX, idxY, 0)
                n += 1

        if graph.orientation == 0:
            n = 0
            for idxX in range(graph.originX, graph.originX+graph.inc*(graph.length), graph.inc):
                if n < N:
                    self.pixelSetXY(idxX, graph.originY, m(idxX, graph.originX, graph.originX+(graph.inc*graph.length-1)))
                else:
                    self.pixelSetXY(idxX, graph.originY, 0)
                n += 1

        if graph.update == True:
            self.pixelsShow()

    ## @brief Object for drawing 2 dimensional time series graphs on GlowBit Matrix displays.

    class graph2D(colourFunctions, colourMaps):

        ## @brief Initialisation routine for the glowbit.matrix.graph2D object.
        #
        # A graph2D object will be drawn to a rectangular region specified by the origin, width, and height.
        #
        # This graph type is explicitly designed to draw time series data.
        #
        # \param originX The x coordinate of the graph's origin (lower left corner).
        # \param originY The y coordinate of the graph's origin (lower left corner).
        # \param width The width, in pixels, of the graph's drawing area.
        # \param height The height, in pixels, of the graph's drawing area
        # \param minValue The value which will be mapped to the bottom edge.
        # \param maxValue The value which will be mapped to the upper edge.
        # \param colour A packed 32-bit GlowBit colour value. Used by the "Solid" colourmap, ignored by the "Rainbow" colourmap. Can also be accessed when writing custom colour map functions.
        # \param bgColour A packed 32-bit GlowBit colour value which is drawn to the entire graph area prior to drawing the data.
        # \param colourMap Either the string "Solid" or "Rainbow" or a pointer to a custom colour map function. Custom colour maps must take the parameters colourMap(self, index, minIndex, maxIndex).
        # \param update If update=True then a call to updateGraph2D() will, in turn, call glowbit.pixelsShow() to update the physical LEDs.

        def __init__(self, originX = 0, originY = 7, width = 8, height = 8, minValue=0, maxValue=255, colour = 0xFFFFFF, bgColour = 0x000000, colourMap = "Solid", update = False, bars = False):
            self.minValue = minValue
            self.maxValue = maxValue
            self.originX = originX
            self.originY = originY
            self.width = width
            self.height = height
            self.colour = colour
            self.bgColour = bgColour
            self.update = update
            self.m = (-height)/(maxValue-minValue)
            self.offset = originY+self.m*minValue
            self.bars = bars
            
            self.data = []
            
            if callable(colourMap) == True:
                self.colourMap = colourMap
            elif colourMap == "Solid":
                self.colourMap = self.colourMapSolid
            elif colourMap == "Rainbow":
                self.colourMap = self.colourMapRainbow
    
    ## @brief Updates a 2D graph with a new value.
    # 
    # \param graph A graph2D object created graph2D
    # \param value A new value to draw to the graph. This value will be drawn on the right edge and the oldest value will be deleted.

    def updateGraph2D(self, graph, value):
        graph.data.insert(0,value)
        if len(graph.data) > graph.width:
            graph.data.pop()
        x = graph.originX+graph.width-1
        m = graph.colourMap
        self.drawRectangleFill(graph.originX, graph.originY-graph.height+1, graph.originX+graph.width-1, graph.originY, graph.bgColour)
        for value in graph.data:
            y = round(-graph.height/(graph.maxValue-graph.minValue )*(value - graph.minValue) + graph.originY + 1)
            if graph.bars == True:
                for idx in range(y, graph.originY+1):
                    if x >= graph.originX and x < graph.originX+graph.width and idx <= graph.originY and idx > graph.originY-graph.height:
                        self.pixelSet(self.remap(x,idx), m(idx, graph.originY, graph.originY+graph.height-1))
            else:
                if x >= graph.originX and x < graph.originX+graph.width and y <= graph.originY and y > graph.originY-graph.height:
                    self.pixelSet(self.remap(x,y), m(y - graph.originY, graph.originY, graph.originY+graph.height-1))
            x -= 1
        if graph.update == True:
            self.pixelsShow()

    ## @brief Demonstrate drawing an animated line

    def lineDemo(self, iters = 10):
        self.blankDisplay()
        while iters > 0:
            for x in range(self.numLEDsX):
                self.pixelsFill(0)
                self.drawLine(x, 0, self.numLEDsX-x-1, self.numLEDsY-1, self.rgbColour(255,255,255))
                self.pixelsShow()
            for x in range(self.numLEDsX-2, 0, -1):
                self.pixelsFill(0)
                self.drawLine(x, 0, self.numLEDsX-x-1, self.numLEDsY-1, self.rgbColour(255,255,255))
                self.pixelsShow()
            iters -= 1
        self.blankDisplay()
    
    ## @brief Demonstrate drawing randomly placed, randomly coloured, expanding circles.
    #
    # Note that pixelsFill(0) is only called after drawing an expanding circle, simulating a mostly filled circle. Gaps are an artefact of the circle drawing algorithm, not a bug.

    def fireworks(self, iters = 10):
        self.blankDisplay()
        import random
        while iters > 0:
            self.pixelsFill(0)
            colour = random.randint(0, 0xFFFFFF)
            Cx = random.randint(0, self.numLEDsX-1)
            Cy = random.randint(0, self.numLEDsY-1)
            for r in range(self.numLEDsX//2):
                self.drawCircle(Cx, Cy, r, colour)
                self.pixelsShow()
            for r in range(self.numLEDsX//2):
                self.drawCircle(Cx, Cy, r, 0)
                self.pixelsShow()
            iters -= 1
    
    ## @brief Demonstration of a rainbow effect is pseudo-polar coordinates.
    #
    # This function intentionally uses integer arithmetic for performance reasons. As such, it is drawn half a pixel off center.
    # 
    # The function animates 255 frames then returns.

    @micropython.viper
    def circularRainbow(self):
        self.blankDisplay()
        maxX = int(self.numLEDsX)
        maxY = int(self.numLEDsY)
        ar = self.ar
        pixelSetXY = self.pixelSetXY
        wheel = self.wheel
        show = self.pixelsShow
        for colourOffset in range(255):
            for x in range(maxX):
                for y in range(maxY):
                    temp1 = (x-((maxX-1) // 2))
                    temp1 *= temp1
                    temp2 = (y-((maxY-1) // 2))
                    temp2 *= temp2
                    r2 = temp1 + temp2
                    # Square root estimate
                    r = 5
                    r = (r + r2//r) // 2
                    pixelSetXY(x,y,wheel((r*300)//maxX - colourOffset*10))
            show()

    ## @brief A class used by the rain() demonstration

    class raindrop():
        def __init__(self, x, speed):
            self.x = x
            self.speed = speed
            self.y = 0
        
        def update(self):
            self.y += self.speed
            return (self.x, (self.y//10))
        
        def getY(self):
            return (self.y//10)

    ## @brief A "digital rain" demonstration.
    #
    # \param iters The number of frames on which raindrops can be drawn
    # \param density The density of raindrops in units of "drops per 4x4 square". The number of drops on the screen will be kept at (number of pixels)*(density)/16

    def rain(self, iters = 200, density=1):
        import random
        self.blankDisplay()
        drops = []
        toDel = []
        c1 = self.rgbColour(200,255,200)
        c2 = self.rgbColour(0,127,0)
        c3 = self.rgbColour(0,64,0)
        c4 = self.rgbColour(0,32,0)
        c5 = self.rgbColour(0,16,0)
        iter = 0
        p = random.randint(0,self.numLEDsX)
        drops.append(self.raindrop(p, random.randint(2,round(self.numLEDsX))))
        while len(drops) > 0:
            while len(drops)/(density) < self.numLEDs/16 and iters > 0:
                p = random.randint(0,self.numLEDsX)
                drops.append(self.raindrop(p, random.randint(2,round(self.numLEDsX))))
            '''
            Optimised the fill out by just making sure the last pixel drawn in a drop is zero
            '''
            for drop in drops:
                (x,y) = drop.update()
                py = y
                self.pixelSetXYClip(x,y, c1)
                self.pixelSetXYClip(x,y-1, c2)
                self.pixelSetXYClip(x,y-2, c3)
                self.pixelSetXYClip(x,y-3, c4)
                self.pixelSetXYClip(x,y-4, c5)
                self.pixelSetXYClip(x,y-5, 0)
                self.pixelSetXYClip(x,y-6, 0)
                self.pixelSetXYClip(x,y-7, 0)

            for drop in reversed(drops):
                if drop.getY() > self.numLEDsY+6:
                    drops.remove(drop)

            iters -= 1
            self.pixelsShow();

    ## @brief Demonstrates creation of non-blocking scrolling text. Only compatible with the GlowBit Matrix 8x8 and tiled arrangements thereof.
    #
    # \param text A string of text which is scrolled across the top row of the display.

    def textDemo(self, text = "Scrolling Text Demo"):
        self.blankDisplay()
        self.addTextScroll(text)
        while self.scrollingText:
            self.updateTextScroll()
            self.pixelsShow()

    ## @brief Draws a single pixel at a random coordinate and "bounces" it around the display

    def bounce(self, iters = 500):
        import random
        Px = random.randint(0, self.numLEDsX-1)
        Py = random.randint(0, self.numLEDsY-1)
        Vx = 2*random.random()-1
        Vy = 2*random.random()-1

        while iters > 0:
            self.pixelSetXY(int(Px), int(Py), 0)
            Px += Vx
            Py += Vy
            self.pixelSetXY(int(Px), int(Py), self.wheel(iters%255))
            if Px < 1 or Px > self.numLEDsX-1:
                Vx *= -1
            if Py < 1 or Py > self.numLEDsY-1:
                Vy *= -1
            iters -= 1
            self.pixelsShow()
        self.blankDisplay()

    ## @brief Runs several demo functions

    def demo(self):
        print("matrix.fireworks()")
        self.fireworks()
        if isinstance(self, matrix8x8):
            print("matrix.textDemo()")
            self.textDemo()
        print("matrix.circularRainbow()")
        self.circularRainbow()
        print("matrix.rain()")
        if isinstance(self, matrix8x8):
            self.rain()
        else:
            self.rain(density=3)
        print("matrix.lineDemo()")
        self.lineDemo()
        print("matrix.bounce()")
        self.bounce()
        self.blankDisplay()

# @brief Class for driving GlowBit Stick modules

class stick(glowbit):

    ## @brief Initialisation routine for GlowBit stick modules and tiled arrays thereof.
    # 
    # \param numLEDs The total number of LEDs. Should be set to 8 * (the number of tiled modules).
    # \param pin The GPIO pin connected to the GlowBit stick module. Defaults to 18 as that pin is compatible with the Raspberry Pi and Raspberry Pi Pico. Any pin can be used on the Raspberry Pi Pico, only pins 18 and 12 are valid on the Raspberry Pi.
    # \param brightness The relative brightness of the LEDs. Colours drawn to the internal buffer should be in the range [0,255] and the brightness parameter scales this value before drawing to the physical display. If brightness is an integer it should be in the range [0,255]. If brightness is floating point it is assumed to be in the range [0,1.0].
    # \param rateLimitFPS The maximum frame rate of the display in frames per second. The pixelsShow() function blocks to enforce this limit.
    # \param sm (Raspberry Pi Pico only) The PIO state machine to generate the GlowBit data stream. Each connected GlowBit display chain requires a unique state machine. Valid values are in the range [0,7].

    def __init__(self, numLEDs = 8, pin = 18, brightness = 20, rateLimitFPS = 30, sm = 0):
        if _SYSNAME == 'rp2':
            self.sm = rp2.StateMachine(sm, self._ws2812, freq=8_000_000, sideset_base=Pin(pin))
            self.sm.active(1)
            self.pixelsShow = self._pixelsShowPico
            self.ticks_ms = time.ticks_ms

        self.numLEDs = numLEDs

        if _SYSNAME == 'Linux':
            self.strip = ws.PixelStrip(numLEDs, pin)
            self.strip.begin()
            self.pixelsShow = self._pixelsShowRPi
            self.ticks_ms = self._ticks_ms_Linux

        self.lastFrame_ms = self.ticks_ms()

        self.ar = array.array("I", [0 for _ in range(self.numLEDs)])
        self.dimmer_ar = array.array("I", [0 for _ in range(self.numLEDs)])
        if rateLimitFPS > 0: 
            self.rateLimit = rateLimitFPS
        else:
            self.rateLimit = 100
        
        if brightness <= 1.0 and isinstance(brightness, float):
            self.brightness = int(brightness*255)
        else:
            self.brightness = int(brightness)
        
        self.pixelsFill(0)
        self.pixelsShow()
        
        # The list of pulses which are drawn upon a call 
        self.pulses = []

    ## @brief A class for animating "pulses" which move down a GlowBit stick.

    class pulse(colourFunctions, colourMaps):

        ## @brief Initialisation routine for the GlowBit Stick pulse object.
        #
        # This function uses the pixelSaturatingAdd() method so multiple pulses can be drawn without colour values corrupting due to addition overflow. 
        #
        # \param speed The speed of the pulse in units of (pixels moved per frame) * 100. A value of 100 means the pulse will move 1 pixels per frame. A speed of 1 will move a pulse 1 pixel every 100 frames. Speed can be positive or negative to allow pulses to move in either direction.
        # \param colour A list of 32-bit GlowBit colours for the pulse. The pulse will have a width equal to the number of elements in this list. A list entry of -1 will have the colour set by a colour map function.
        # \param index The initial index of the pulse. Generally recommended to set to 0 if speed > 0 and numLEDs if speed < 0.
        # \param colourMap Either the string "Solid" or "Rainbow" or a custom function pointer. Custom functions must take the positional arguments: colourMapFunction(self, index, minIndex, maxIndex). When calling colour map functions updatePulses() sets minIndex to 0 and maxIndex to numLEDs.

        def __init__(self, speed = 100, colour = [0xFFFFFF], index = 0, colourMap = None):
            ## Speed of the pulse
            self.speed = speed 
            ## Initial index of the pulse
            self.index = index
            self._position = self.index*100 # index * 100
           
            if type(colour) is list:
                ## A list of 32-bit GlowBit colour values. Each one is drawn to a pixel; a -1 indicates the use of the colourMap function
                self.colour = colour
            else:
                self.colour = [colour]

            if callable(colourMap) == True:
                ## Either the string "Solid" or "Rainbow" or a function pointer to a custom colourmap. Only sets pixel colour for pixels with a colour of -1.
                self.colourMap = colourMap
            elif colourMap == "Solid":
                self.colourMap = self.colourMapSolid
            elif colourMap == "Rainbow":
                self.colourMap = self.colourMapRainbow
            else:
                self.colourMap = None
            
        def _update(self):
            self._position += self.speed
            self.index = self._position//100

    ## @brief Add a pulse to the list of pulses    
    #
    # \param speed The speed of the pulse in units of (pixels moved per frame) * 100. A value of 100 means the pulse will move 1 pixels per frame. A speed of 1 will move a pulse 1 pixel every 100 frames. Speed can be positive or negative to allow pulses to move in either direction.
    # \param colour A list of 32-bit GlowBit colours for the pulse. The pulse will have a width equal to the number of elements in this list. A list entry of -1 will have the colour set by a colour map function.
    # \param index The initial index of the pulse. Generally recommended to set to 0 if speed > 0 and numLEDs if speed < 0.
    # \param colourMap Either the string "Solid" or "Rainbow" or a custom function pointer. Custom functions must take the positional arguments: colourMapFunction(self, index, minIndex, maxIndex). When calling colour map functions updatePulses() sets minIndex to 0 and maxIndex to numLEDs.

    def addPulse(self, speed = 100, colour = [0xFFFFFF], index = 0, colourMap = None):
        self.pulses.append(self.pulse(speed, colour, index, colourMap))
    

    ## @brief Update the position of all pulses in self.pulses[] and draw them to the internal buffer.
    #
    # A call to pixelsShow() must be done manually to update the physical LEDs.

    def updatePulses(self):
        for p in self.pulses:
            i = p.index
            for c in p.colour:
                if c == -1:
                    if callable(p.colourMap):
                        c = p.colourMap(i, 0, self.numLEDs)
                    else:
                        c = 0
                if i >=0 and i < self.numLEDs:
                    self.pixelSaturatingAdd(i, c)
                i -= 1
            p._update()
            
        for p in reversed(self.pulses):
            if p.index - len(p.colour) >= self.numLEDs:
                self.pulses.remove(p)
            if p.index + len(p.colour) < 0:
                self.pulses.remove(p)
       

    ## @brief One dimensional graph ofject for drawing a graph bar on a GlowBit Stick display
    class graph1D(colourFunctions, colourMaps):

        ## @brief Initialisation routine for the glowbit.stick.graph1D object. This object is drawn to the display with glowbit.stick.updateGraph1D.
        # 
        # \param minIndex The pixel index for the start of the graph
        # \param maxIndex The pixel index for the end of the graph
        # \param minValue The numerical value of the start of the graph
        # \param maxValue The numerical value of the end of the graph
        # \param colour The graph's colour if using the Solid colourmap
        # \param colourMap Either the string "Solid" or "Rainbow" or a function pointer to a custom colour map. Custom colour maps must take the parameters colourMap(Self, index, minIndex, maxIndex).
        # \param update If this is set to True then a call to updateGraph1D() will automatically call pixelsShow() to update the physical display.

        def __init__(self, minIndex = 0, maxIndex = 7, minValue=0, maxValue=255, colour = 0xFFFFFF, colourMap = "Solid", update = False):
            self.minValue = minValue
            self.maxValue = maxValue
            self.minIndex = minIndex
            self.maxIndex = maxIndex
            # Gradientand offset have +1 and -1 respectively to map "minValue" to an index of -1.
            # With rounding this provides 0.5 "pixel widths" of value range at the bottom end before minIndex turns on
            # and 0.5 "pixels widths" at the top end before maxIndex turns off.
            self.m = (maxIndex-minIndex+1)/(maxValue-minValue)
            self.offset = minIndex-1-self.m*minValue
            self.update = update
            self.colour = colour

            if callable(colourMap) == True:
                self.colourMap = colourMap
            elif colourMap == "Solid":
                self.colourMap = self.colourMapSolid
            elif colourMap == "Rainbow":
                self.colourMap = self.colourMapRainbow
 
    ## @brief Wrapper function to create graph1D objects. Returns a new stick.graph1D() object.
    #
    # See also stick.graph1D()
    # 
    # \param minIndex The pixel index for the start of the graph
    # \param maxIndex The pixel index for the end of the graph
    # \param minValue The numerical value of the start of the graph
    # \param maxValue The numerical value of the end of the graph
    # \param colour The graph's colour if using the Solid colourmap
    # \param colourMap Either the string "Solid" or "Rainbow" or a function pointer to a custom colour map. Custom colour maps must take the parameters colourMap(Self, index, minIndex, maxIndex).
    # \param update If this is set to True then a call to updateGraph1D() will automatically call pixelsShow() to update the physical display.

    def newGraph1D(self, minIndex = 0, maxIndex = 7, minValue = 0, maxValue = 255, colour = 0xFFFFFF, colourMap = "Solid", update = False):
        return self.graph1D(minIndex, maxIndex, minValue, maxValue, colour, colourMap, update)

    ## @brief Updates a graph1D object, drawing it to the display.
    # 
    # If the graph1D object was created with "update = True" this function will call pixelsShow() to update the physical display before returning.
    #
    # \param graph A graph1D object as returned by stick.graph1D
    # \param value The numerical value to plot on the graph

    def updateGraph1D(self, graph, value):
        i = round(graph.m*value + graph.offset)
        m = graph.colourMap
        for idx in range(graph.minIndex, i+1):
            self.pixelSet(idx, m(idx, graph.minIndex, graph.maxIndex))
        for idx in range(i+1, graph.maxIndex+1):
            self.pixelSet(idx, 0)
        if graph.update == True:
            self.pixelsShow()
        
    ## @brief Fill a "slice" of the GlowBit stick's pixels with a solid colour.
    # 
    # By default it will fill the entire display with a solid colour.
    # 
    # \param i The minimum index to fill
    # \param j The maximum index to fill
    # \param colour A 32-bit GlowBit colour value

    def fillSlice(self, i=0, j=-1, colour = 0xFFFFFF):
        if j == -1:
            j = self.numLEDs
        for k in range(i, j+1):
            self.pixelSet(k, colour)

    ## @brief A demonstration of the use of "pulse" objects
    # 
    # The pulse traveling "up" the stick is drawn with default arguments: a single white pixel
    # 
    # The pulse returning "down" the stick is drawn with a 3-pixel list of colours. The first and last are coloured with the "Rainbow" colour map, changing colour with pixel index, while the middle is white.
    # 
    # \param iters The number of frames which are drawn before returning.
    def pulseDemo(self, iters = 100):
        while iters > 0:
            if iters % (self.numLEDs+4) == 0:
                if iters % (2*(self.numLEDs+4)) == 0:
                    self.addPulse()
                else:
                    self.addPulse(speed=-100, index=self.numLEDs, colourMap="Rainbow", colour=[-1, self.rgbColour(255,255,255), -1])
            self.pixelsFill(0)
            self.updatePulses()
            self.pixelsShow()
            iters -= 1

    ## @brief A demonstration of the use of "graph1D" objects
    #
    # This demonstration alternates between drawing two graphs with different colour maps; one with the "Rainbow" map, covering the full colour wheel, and another of solid white.
    # \param iters The number of times both graphs are drawn.
    def graphDemo(self, iters = 3):
        g1 = stick.graph1D(minIndex = 0, maxIndex = 7, minValue=1, maxValue=8, update=True, colourMap = "Rainbow")
        g2 = stick.graph1D(minIndex = 0, maxIndex = 7, minValue=1, maxValue=8, update=True, colourMap = "Solid")
        while iters > 0:
            for x in range(1,9):
                self.updateGraph1D(g1, x)
            for x in range(8,-1, -1):
                self.updateGraph1D(g1, x)
            for x in range(1,9):
                self.updateGraph1D(g2, x)
            for x in range(8,-1, -1):
                self.updateGraph1D(g2, x)

            iters -= 1

    ## @brief A Demonstration of the use of the "fillSlice" method.
    #
    # Animates a red, green, and blue slice "moving" down the GlowBit Stick display.
    #
    # The number of iterations is fixed due to the bit shift operation being used to change colour.
    def sliceDemo(self):
        iters = 3
        colour = 0xFF0000
        while iters > 0:
            for i in range(self.numLEDs):
                self.pixelsFill(0)
                self.fillSlice(0, i, colour)
                self.pixelsShow()
            for i in range(self.numLEDs):
                self.pixelsFill(0)
                self.fillSlice(i, self.numLEDs-1, colour)
                self.pixelsShow()
            colour = colour >> 8
            iters -= 1

        self.pixelsFill(0)
        self.pixelsShow()

    ## @brief Uses the colourMapRainbow() colour map to display a colourful animation
    def rainbowDemo(self, iters = 5):
        while iters > 0:
            for offset in range(33):
                for i in range(8):
                    self.pixelSet(i, self.colourMapRainbow(i,offset, offset+32))
                self.pixelsShow()
            iters -= 1

    ## @brief Runs several demo patterns
    def demo(self):
        print("stick.rainbowDemo()")
        self.rainbowDemo()
        print("stick.pulseDemo()")
        self.pulseDemo()
        print("stick.graphDemo()")
        self.graphDemo()
        print("stick.sliceDemo()")
        self.sliceDemo()

## @brief The class specific to the GlowBit Rainbow
#
# This class inherits all the functionality of the GlowBit Stick and extends it with Rainbow-specific methods.

class rainbow(stick):

    ## @brief Initialisation routine for GlowBit rainbow modules.
    # 
    # \param numLEDs The total number of LEDs. Should be set to 13 * (the number of tiled modules).
    # \param pin The GPIO pin connected to the GlowBit Rainbow module. Defaults to 18 as that pin is compatible with the Raspberry Pi and Raspberry Pi Pico. Any pin can be used on the Raspberry Pi Pico, only pins 18 and 12 are valid on the Raspberry Pi.
    # \param brightness The relative brightness of the LEDs. Colours drawn to the internal buffer should be in the range [0,255] and the brightness parameter scales this value before drawing to the physical display. If brightness is an integer it should be in the range [0,255]. If brightness is floating point it is assumed to be in the range [0,1.0].
    # \param rateLimitFPS The maximum frame rate of the display in frames per second. The pixelsShow() function blocks to enforce this limit.

    def __init__(self, numLEDs = 13, pin = 18, brightness = 40, rateLimitFPS = 60, sm = 0):
        super().__init__(numLEDs, pin, brightness, rateLimitFPS, sm)
        self.drawRainbow()

    ## @brief Sets the colour of a pixel on the GlowBit Rainbow, addressed by its angle label.
    #
    #
    # \param angle An integer number in degrees equal to an angle label on the GlowBit Rainbow PCB.
    # \param colour A 32-bit GlowBit colour value

    def pixelSetAngle(self, angle, colour):
        self.pixelSet(angle//15, colour)

    ## @brief Colours each pixel to display a rainbow spectrum.
    #
    # This method calls pixelsShow().
    #
    # \param offset A "phase" offset mapping [0,360] degrees to [0,255]. A value of 0 displays red at angle 0 and purple at angle 180. A modulo-255 operation is performed, allowing this value to be any integer. The rainLoop() method varies this value to display an animation.

    def drawRainbow(self, offset = 0):
        colPhase = offset
        for i in range(self.numLEDs):
            self.pixelSet(i, self.wheel(colPhase%255))
            colPhase += 17 # "True" rainbow, red to purple
        self.pixelsShow()
    
    ## @brief Displays a rainbow animation in an infinite loop. This method demonstrates the use of drawRainbow().

    def demo(self):
        x = 0
        while True:
            self.drawRainbow(x)
            x += 1

## @brief Class for driving triangular GlowBit modules

class triangle(glowbit):

    ## @brief Initialisation routine for triangular GlowBit modules and tiled arrays thereof.
    # 
    # \param numTris The number of triangle modules in the tiled array.
    # \param LEDsPerTri The number of LEDs on each triangular module.
    # \param pin The GPIO pin connected to the GlowBit stick module. Defaults to 18 as that pin is compatible with the Raspberry Pi and Raspberry Pi Pico. Any pin can be used on the Raspberry Pi Pico, only pins 18 and 12 are valid on the Raspberry Pi.
    # \param brightness The relative brightness of the LEDs. Colours drawn to the internal buffer should be in the range [0,255] and the brightness parameter scales this value before drawing to the physical display. If brightness is an integer it should be in the range [0,255]. If brightness is floating point it is assumed to be in the range [0,1.0].
    # \param rateLimitFPS The maximum frame rate of the display in frames per second. The pixelsShow() function blocks to enforce this limit.
    # \param sm (Raspberry Pi Pico only) The PIO state machine to generate the GlowBit data stream. Each connected GlowBit display chain requires a unique state machine. Valid values are in the range [0,7].

    def __init__(self, numTris = 1, LEDsPerTri = 6, pin = 18, brightness = 20, rateLimitFPS = 20, sm = 0):
        if _SYSNAME == 'rp2':
            self.sm = rp2.StateMachine(sm, self._ws2812, freq=8_000_000, sideset_base=Pin(pin))
            self.sm.active(1)
            self.pixelsShow = self._pixelsShowPico
            self.ticks_ms = time.ticks_ms

        self.LEDsPerTri = LEDsPerTri
        self.numLEDs = numTris*LEDsPerTri
        self.numTris = numTris

        if _SYSNAME == 'Linux':
            self.strip = ws.PixelStrip(self.numLEDs, pin)
            self.strip.begin()
            self.pixelsShow = self._pixelsShowRPi
            self.ticks_ms = self._ticks_ms_Linux

        self.ar = array.array("I", [0 for _ in range(self.numLEDs)])
        self.dimmer_ar = array.array("I", [0 for _ in range(self.numLEDs)])
        
        if rateLimitFPS > 0: 
            self.rateLimit = rateLimitFPS
        else:
            self.rateLimit = 100
        
        if brightness <= 1.0 and isinstance(brightness, float):
            self.brightness = int(brightness*255)
        else:
            self.brightness = int(brightness)
        
        self.pixelsFill(0)
        self.lastFrame_ms = self.ticks_ms()
        self.pixelsShow()
        
    ## @brief Fills all LEDs on a given triangle with the same colour.
    #
    # \param tri The triangle to fill. The first triangle is addressed with 0.
    # \param colour A 32-bit GlowBit colour value

    def fillTri(self, tri, colour):
        addr = self.LEDsPerTri*tri
        for i in range(addr, addr+self.LEDsPerTri):
            self.ar[i] = colour

    ## @brief Displays a simple demo pattern

    def demo(self):
       import random 
       for i in range(2):
           for j in range(self.numTris):
               self.fillTri(j, self.wheel(random.randint(0,255)))

## @brief Class for driving GlowBit Matrix 4x4 modules and horizontally tiled arrangements thereof.
#
# NB: The 4x4 matrix is designed to only tile horizontally, making an Nx4 pixel display. 
#
# If manually tiling horizontally and vertically a custom remapping function will need to be written.
#
# The custom mapping function has the form mapFunction(self, x: int, y: int) -> int and returns a "one dimensional" pixel index given an (x,y) coordinate.
#
# No checking is performed before calling the mapping function. An exception will be raised if the positional arguments are incorrect.

class matrix4x4(glowbitMatrix):

    ## @brief Initialisation routine for GlowBit stick modules and tiled arrays thereof.
    # 
    # \param tiles The number of tiled GlowBit Matrix 4x4 modules.
    # \param pin The GPIO pin connected to the GlowBit stick module. Defaults to 18 as that pin is compatible with the Raspberry Pi and Raspberry Pi Pico. Any pin can be used on the Raspberry Pi Pico, only pins 18 and 12 are valid on the Raspberry Pi.
    # \param brightness The relative brightness of the LEDs. Colours drawn to the internal buffer should be in the range [0,255] and the brightness parameter scales this value before drawing to the physical display. If brightness is an integer it should be in the range [0,255]. If brightness is floating point it is assumed to be in the range [0,1.0].
    # \param mapFunction A function pointer to a custom pixel mapping function. Only required if mapping pixels to non-standard tiling arrangements.
    # \param rateLimitFPS The maximum frame rate of the display in frames per second. The pixelsShow() function blocks to enforce this limit.
    # \param sm (Raspberry Pi Pico only) The PIO state machine to generate the GlowBit data stream. Each connected GlowBit display chain requires a unique state machine. Valid values are in the range [0,7].


    def __init__(self, tiles = 1, pin = 18, brightness = 20, mapFunction = None, rateLimitFPS = 30, sm = 0):
        if _SYSNAME == 'rp2':
            self.sm = rp2.StateMachine(sm, self._ws2812, freq=8_000_000, sideset_base=Pin(pin))
            self.sm.active(1)
            self.pixelsShow = self._pixelsShowPico
            self.ticks_ms = time.ticks_ms

        self.tiles = tiles
        self.numLEDs = tiles*16
        self.numLEDsX = tiles*4
        self.numLEDsY = 4
        # Convenience variable; equal to numLEDsX
        self.numCols = self.numLEDsX
        # Convenience variable; equal to numLEDsY
        self.numRows = self.numLEDsY

        if _SYSNAME == 'Linux':
            self.strip = ws.PixelStrip(self.numLEDs, pin)
            self.strip.begin()
            self.pixelsShow = self._pixelsShowRPi
            self.ticks_ms = self._ticks_ms_Linux

        self.ar = array.array("I", [0 for _ in range(self.numLEDs)])
        self.dimmer_ar = array.array("I", [0 for _ in range(self.numLEDs)])
        self.lastFrame_ms = self.ticks_ms()
        self.scrollingText = False # Only required because the self.pixelsShow() function is shared with the 8x8
        
        if brightness <= 1.0 and isinstance(brightness, float):
            self.brightness = int(brightness*255)
        else:
            self.brightness = int(brightness)

        if callable(mapFunction) is True:
            self.remap = mapFunction
        else:
            self.remap = self.remap4x4
            
        if rateLimitFPS > 0: 
            self.rateLimit = rateLimitFPS
        else:
            self.rateLimit = 100
            
        # Blank display
        self.pixelsFill(0)
        self.pixelsShow()
        self.pixelsShow() # On fresh power-on this is needed twice. Why?!?!

    ## @brief Maps an (x,y) coordinate on a 4 row, Nx4 column, tiled GlowBit Matrix 4x4 array to an array index for the internal buffer.
    #
    # It is recommended to use pixelSetXY() (and variants) instead of this function.
    #
    # The return value can be passed to pixelSet(i, colour) (and its variants pixelSetNow() etc) in place of the paramter "i".
    # 
    # The (x,y) coordinates assume (0,0) in the upper left corner of the display with x increasing to the right and y increasing down
    #
    # This function does not do boundary checking and may return a value which is outside the array, causing an IndexError exception to be raised.
    #
    # \param x The x coordinate of the pixel to index
    # \param y The y coordinate of the pixel to index

    @micropython.viper
    def remap4x4(self, x: int,y: int) -> int:
        mc = x // 4 # Module col that x falls into
        mx = x - 4*mc # Module x position - inside sub-module, relative to (0,0) top left
        TopLeftIndex = mc * 16 # ASSUMES 4X4 MODULES
        LEDsBefore = 4*y + x - 4*mc # LEDs before in a module
        return TopLeftIndex + LEDsBefore
   


## @brief Class for driving GlowBit Matrix 8x8 modules and tiled arrangements thereof.
#
# The GlowBit Matrix 8x8 is designed to tile in two dimensions to create arbitratily large displays without the need for "air-wiring" of the data signal.
#
# The remap8x8() method maps an (x,y) coordinate to a pixel index if the data signal "snakes" back and forth. When viewed from the REAR of a tiled array data-in is soldered to the top right module, moves right to left, then left to right on the 2nd row, etc. See https://glowbit.io/02 for assembly details.
# \verbatim
#  ---<  Data routing: view from REAR (ie: when soldering Din / Dout pads).
# |
#  >---
#     |
#  ---<
# \endverbatim
#

class matrix8x8(glowbitMatrix):
    
    ## @brief Initialisation routine for GlowBit stick modules and tiled arrays thereof.
    # 
    # \param tileRows The number of tiled GlowBit Matrix 8x8 module rows.
    # \param tileCols The number of tiled GlowBit Matrix 8x8 module columns.
    # \param pin The GPIO pin connected to the GlowBit stick module. Defaults to 18 as that pin is compatible with the Raspberry Pi and Raspberry Pi Pico. Any pin can be used on the Raspberry Pi Pico, only pins 18 and 12 are valid on the Raspberry Pi.
    # \param brightness The relative brightness of the LEDs. Colours drawn to the internal buffer should be in the range [0,255] and the brightness parameter scales this value before drawing to the physical display. If brightness is an integer it should be in the range [0,255]. If brightness is floating point it is assumed to be in the range [0,1.0].
    # \param mapFunction A function pointer to a custom pixel mapping function. Only required if mapping pixels to non-standard tiling arrangements.
    # \param rateLimitFPS The maximum frame rate of the display in frames per second. The pixelsShow() function blocks to enforce this limit. This argument defaults to -1 to allow rateLimitCharactersPerSecond to preference this parameter if it is not set. If neither rateLimitFPS or rateLimitCharactersPerSecond are set the limit is set to 30 FPS.
    # \param rateLimitCharactersPerSecond If given a positive value the display update rate is set to display this many characters of scrolling text per second. A value of 1 is fast, but readable. This value can be fractional (eg: 0.5).
    # \param sm (Raspberry Pi Pico only) The PIO state machine to generate the GlowBit data stream. Each connected GlowBit display chain requires a unique state machine. Valid values are in the range [0,7].

    def __init__(self, tileRows = 1, tileCols = 1, pin = 18, brightness = 20, mapFunction = None, rateLimitFPS = -1, rateLimitCharactersPerSecond = -1, sm = 0):
    
        self.tileRows = tileRows
        self.tileCols = tileCols
        self.numLEDs = tileRows*tileCols*64
        self.numLEDsX = tileCols*8
        self.numLEDsY = tileRows*8
        # Convenience variable; equal to numLEDsX
        self.numCols = self.numLEDsX
        # Convenience variable; equal to numLEDsY
        self.numRows = self.numLEDsY
        
        if _SYSNAME == 'rp2':
            self.sm = rp2.StateMachine(sm, self._ws2812, freq=8_000_000, sideset_base=Pin(pin))
            self.sm.active(1)
            self.pixelsShow = self._pixelsShowPico
            self.ticks_ms = time.ticks_ms

        if _SYSNAME == 'Linux':
            self.strip = ws.PixelStrip(self.numLEDs, pin)
            self.strip.begin()
            self.pixelsShow = self._pixelsShowRPi
            self.ticks_ms = self._ticks_ms_Linux

        self.ar = array.array("I", [0 for _ in range(self.numLEDs)])
        self.dimmer_ar = array.array("I", [0 for _ in range(self.numLEDs)])
        
        if brightness <= 1.0 and isinstance(brightness, float):
            self.brightness = int(brightness*255)
        else:
            self.brightness = int(brightness)
        
        # Set to True while a scrolling text object is available to be drawn.
        self.scrollingText = False
        
        self.lastFrame_ms = self.ticks_ms()
        
        if rateLimitFPS > 0: 
            self.rateLimit = rateLimitFPS
        elif rateLimitCharactersPerSecond > 0:
            self.rateLimit = rateLimitCharactersPerSecond * 8
        else:
            self.rateLimit = 30
        
        self.scrollingTextList = []
        
        if callable(mapFunction) is True:
            self.remap = mapFunction
            print(self.remap)
        else:
            self.remap = self.remap8x8
            
        # Blank display
        self.blankDisplay()
        self.blankDisplay()

    ## @brief Prints a string of text to a tiled GlowBit Matrix 8x8 display, automatically wrapping to new lines as required. Each character occupies an 8x8 pixel area.
    #
    # Characters which do not fit on the display are truncated.
    #
    # \param string The string to print to the display.
    # \param x The x coordinate of the upper left corner of the first character
    # \param y The y coordinate of the upper left corner of the first character
    # \param colour A 32-bit GlowBit colour value. All pixels in every character will be drawn in this colour.
    def printTextWrap(self, string, x = 0, y = 0, colour = 0xFFFFFF):
        Px = x
        Py = y
        for char in string:
            if Py < self.numLEDsY - 7:
                self.drawChar(char, Px, Py, colour)
            Px += 8
            if Px + 1 >= self.numLEDsX:
                Py += 8
                if x < 0:
                    Px = 0
                else:
                    Px = x

    class _textScroll():
        def __init__(self, string, y = 0, x = 0, colour = 0xFFFFFF, bgColour = 0):
            self.x = x
            self.y = y
            self.colour = colour
            self.bgColour = bgColour
            self.string = string
    
    ## @brief Adds a line of scrolling text to the display.
    #
    # This method can be blocking or non-blocking.
    #
    # If blocking the scrolling text will be drawn to the physical display and the method won't return until the animation is complete.
    #
    # If non-blockig this method will return quickly, allowing subsequent calls to updateTextScroll() to control the rate of scrolling text animation. The text will scroll to the left one pixel with each call to updateTextScroll().
    #
    # The update prameter is provided for convinience; if it is set to True a call to updateTextScroll() will automatically call pixelsShow(). Setting update to False allows the text scroll to be synchronised with other drawing updates.
    #
    # \param string The string of text to scroll across the display
    # \param y The y coordinate of the top edge of the text
    # \param x The initial location of the text relative to the right edge of the display. Setting positive will scroll the text from further off the edge, producing a delay before it is visible. Setting negative will cause the text to appear on the display instantly before scrolling to the left. In units of pixels.
    # \param colour The colour of the scrolling text characters. A 32-bit GlowBit colour value
    # \param bgColour The colour of the background (ie: all pixels in the 8-row high area the text is drawn to which aren't part of a character). A 32-bit GlowBit colour value.
    # \param update Passing update = True causes updateTextScroll() to call pixelsShow(). Otherwise pixelsShow() must be called manually, allowing synchronisation of scrolling text with other animated features.
    # \param blocking Passing blocking = True will draw the scrolling text to the screen immediately and this method will not return until the text has scrolled off the display.

    def addTextScroll(self, string, y = 0, x = 0, colour = 0xFFFFFF, bgColour = 0x000000, update=False, blocking=False):
        self.scrollingTextList.append(self._textScroll(string, y, -self.numLEDsX-x, colour, bgColour))
        self.updateText = update
        # Set to True if scrolling text exists to be drawn.
        self.scrollingText = True
        if blocking == True:
            self.updateText = True
            while self.scrollingText > 0:
                self.updateTextScroll()
         
    ## @brief Update a scrolling text animation
    #
    # addTextScroll() must be called at least once for scrolling text to be drawn to the display.

    def updateTextScroll(self):
        for textLine in self.scrollingTextList:
            x = 0
            self.drawRectangleFill(0,textLine.y,self.numLEDsX, textLine.y+7, textLine.bgColour)
            for c in textLine.string:
                self.drawChar(c, -textLine.x+8*x, textLine.y, textLine.colour)
                x += 1
            textLine.x += 1
                            
        for textLine in reversed(self.scrollingTextList):
            if textLine.x == 8*len(textLine.string)+1:
                self.scrollingTextList.remove(textLine)
        
        if self.updateText == True:
            self.pixelsShow()
        if len(self.scrollingTextList) == 0:
            self.scrollingText = False

    ## @brief Maps an (x,y) coordinate on a tiled GlowBit Matrix 8x8 array to an internal buffer array index.
    #
    # It is recommended to use pixelSetXY() (and variants) instead of this function.
    # 
    # The return value can be passed to pixelSet(i, colour) (and its variants pixelSetNow() etc) in place of the paramter "i".
    # 
    # The (x,y) coordinates assume (0,0) in the upper left corner of the display with x increasing to the right and y increasing down
    #
    # This function does not do boundary checking and may return a value which is outside the array, causing an IndexError exception to be raised.
    # 
    # \param x The x coordinate of the pixel to index
    # \param y The y coordinate of the pixel to index

    @micropython.viper
    def remap8x8(self, x: int,y: int) -> int:
        #mr = (y // 8) # Module row that y falls into
        #mc = (x // 8) # Module col that x falls into
        #mx = (x - 8*mc) # Module x position - inside sub-module, relative to (0,0) top left
        #my = (y - 8*mr) # Module y position - inside sub-module, relative to (0,0) top left
        if (y//8) % 2 == 0:
            # Module row is even
            return 64*((y//8)*int(self.tileCols) + x//8) + (8*(y%8) + x%8)
        else:
            return 64*((y//8)*int(self.tileCols) + (int(self.tileCols) - x//8 - 1)) + (8*(y%8) + x%8)
        #TopLeftIndex = (ModulesBefore * 64) # ASSUMES 8X8 MODULES
        #LEDsBefore = (8*(y-8*mr) + x-8*mc) # LEDs before in a module
        #return (ModulesBefore * 64) + (8*(y%8) + x%8)
        #return (ModulesBefore * 64) + (8*(y-8*(y//8)) + x-8*(x//8))

    ## @brief Draw a single character to the display
    #
    # For increased performance on Micropython boards this method uses the Micropython Viper code emitter so all arguments are necessary.
    #
    # See also: addTextScroll() / updateTextScroll() for built-in scrolling text and printTextWrap() for printing static text with automatic line feeds.
    #
    # \param char A single character string. This character will be drawn to the internal buffer.
    # \param Px The x coordinate of the upper left corner of the character. Characters occupy an 8x8 pixel area.
    # \param Py The y coordinate of the upper left corner of the character. Characters occupy an 8x8 pixel area.
    # \param colour A 32-bit GlowBit colour value

    @micropython.viper
    def drawChar(self, char, Px: int, Py: int, colour: int):
        if Px < -7 or Px > int(self.numLEDsX):
            return
        ar = ptr32(self.ar)
        remap = self.remap
        x = Px
        y = Py
        charIdx = (int(ord(char))-32)*8
        N = int(self.numLEDs)
        maxCol = int(min(8, int(self.numLEDsX)-Px))
        if x < 0:
            minCol = -1*x
            x = 0
        else:
            minCol = 0
        tileCols = int(self.tileCols)
        for col in range(minCol, maxCol):
            dat = int(petme128[charIdx + col])
            ar[int(remap(x,y))] += ((dat)&1)*(colour)
            ar[int(remap(x,y+1))] += ((dat>>1)&1)*colour
            ar[int(remap(x,y+2))] += ((dat>>2)&1)*colour
            ar[int(remap(x,y+3))] += ((dat>>3)&1)*colour
            ar[int(remap(x,y+4))] += ((dat>>4)&1)*colour
            ar[int(remap(x,y+5))] += ((dat>>5)&1)*colour
            ar[int(remap(x,y+6))] += ((dat>>6)&1)*colour
            ar[int(remap(x,y+7))] += ((dat>>7)&1)*colour
            x += 1
    
    ## @brief Changes the 8x8 matrix display's update rate in units of "characters of scrolling text per second".
    #
    # For example, a value of 2 would scroll 2 charcters per second; leaving each character at least partly visible for 0.5 seconds.

    def updateRateLimitCharactersPerSecond(self, rateLimitCharactersPerSecond):
        self.rateLimit = rateLimitCharactersPerSecond * 8
