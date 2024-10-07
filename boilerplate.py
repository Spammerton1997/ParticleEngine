import math
import numpy as np

sin_lookup = [math.sin(math.radians(x)) for x in range(360)]
def quicksin(x:float):
    x = round(x) % 360
    return sin_lookup[x]

def quickrand(x):
    return np.random.randint(0,x)

neighbor_cords = [
    (0,1),
    (1,1),
    (1,0),
    (1,-1),
    (0,-1),
    (-1,-1),
    (-1,0),
    (-1,1)
]