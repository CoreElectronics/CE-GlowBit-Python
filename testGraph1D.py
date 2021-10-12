import glowbit

matrix = glowbit.matrix4x4(rateLimitFPS = 5, tiles=3)
graph1 = matrix.graph1D(originX = 11, originY = 0, direction = "Left", length=12, maxValue=12, colourMap = "Rainbow", update=False)
graph2 = matrix.graph1D(originX = 0, originY = 3, direction = "Right", length=12, maxValue=12, colourMap = "Rainbow", update=True)

for x in range(13):
    matrix.updateGraph1D(graph1, x)
    matrix.updateGraph1D(graph2, x)
for x in range(12, -1, -1):
    matrix.updateGraph1D(graph1, x)
    matrix.updateGraph1D(graph2, x)

graph1 = matrix.graph1D(originX = 11, originY = 0, direction = "Down", length=4, maxValue=4, colourMap = "Rainbow", update=False)
graph2 = matrix.graph1D(originX = 0, originY = 3, direction = "Up", length=4, maxValue=4, colourMap = "Rainbow", update=True)

for x in range(5):
    matrix.updateGraph1D(graph1, x)
    matrix.updateGraph1D(graph2, x)
for x in range(4, -1, -1):
    matrix.updateGraph1D(graph1, x)
    matrix.updateGraph1D(graph2, x)
