import glowbit

matrix = glowbit.matrix8x8(rateLimitFPS = 5)

graph1 = matrix.graph1D(originX = 7, originY = 0, direction = "Left", length=8, maxValue=8, colourMap = "Rainbow")
graph2 = matrix.graph1D(originX = 0, originY = 7, direction = "Right", length=8, maxValue=8, colourMap = "Rainbow", update=True)

for x in range(9):
    matrix.updateGraph1D(graph1, x)
    matrix.updateGraph1D(graph2, x)

for x in range(8, -1, -1):
    matrix.updateGraph1D(graph1, x)
    matrix.updateGraph1D(graph2, x)

graph1 = matrix.graph1D(originX = 7, originY = 0, direction = "Down", length=8, maxValue=8, colourMap = "Rainbow")
graph2 = matrix.graph1D(originX = 0, originY = 7, direction = "Up", length=8, maxValue=8, colourMap = "Rainbow", update=True)

for x in range(9):
    matrix.updateGraph1D(graph1, x)
    matrix.updateGraph1D(graph2, x)
for x in range(8, -1, -1):
    matrix.updateGraph1D(graph1, x)
    matrix.updateGraph1D(graph2, x)
