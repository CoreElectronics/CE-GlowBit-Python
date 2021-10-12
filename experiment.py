import rpi_ws281x as ws

LED_COUNT = 12
LED_FREQ_HZ = 8000000
LED_CHANNEL = 0
LED_DMA_NUM = 10
LED_GPIO = 18

leds = ws.new_ws2811_t()
ch = ws.ws2811_channel_get(leds, 0)
ws.ws2811_channel_t_count_set(ch, LED_COUNT)
ws.ws2811_channel_t_gpionum_set(ch, LED_GPIO)
ws.ws2811_channel_t_invert_set(ch, 0)
ws.ws2811_channel_t_brightness_set(ch, 255)
ws.ws2811_t_freq_set(leds, 800000)
ws.ws2811_t_dmanum_set(leds, LED_DMA_NUM)

resp = ws.ws2811_init(leds)
