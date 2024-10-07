from math import sqrt

def infect(pos:tuple[int,int], part_data:list, neighbors:list, simstate):
    active = False
    for pos, data in neighbors:
        if data[0] == part_data[0]:
            continue
        simstate.set(pos, part_data)
        active = True

    return part_data, True, active

def flammable_infect(pos:tuple[int,int], part_data:list, neighbors:list, simstate):
    active = False
    burned = False
    for pos, data in neighbors:
        if data[0] == part_data[0]:
            continue

        if data[0] in hot_parts:
            burned = True
        else:
            simstate.set(pos, part_data)
        active = True

    if burned:
        ember = particle_data[10]["created"].copy()
        ember[0] = 10
        return ember, True, True
    return part_data, True, active

def corrode(pos:tuple[int,int], part_data:list, neighbors:list, simstate):
    active = False

    powder = particle_data[1]["created"].copy()
    powder[0] = 1
    for pos, data in neighbors:
        if particle_data[data[0]]["type"] == "solid":
            simstate.set(pos, powder.copy())
            active = True

    return part_data, True, active

def melt(pos:tuple[int,int], part_data:list, neighbors:list, simstate):
    active = False

    for pos, data in neighbors:
        if data[0] == 16:
            simstate.set(pos, part_data)
            active = True

    return part_data, True, active

def _explode(pos, radius, simstate, particle):
    x, y = pos
    for i in range(x - radius, x + radius + 1):
        for j in range(y - radius, y + radius + 1):
            if sqrt((i - x)**2 + (j - y)**2) <= radius:
                if j > 0:
                    simstate.set((i, j), particle.copy())

def bomb(pos:tuple[int,int], part_data:list, neighbors:list, simstate):
    if not neighbors:
        return part_data, True, False
    exploded = False
    for pos, data in neighbors:
        if not data[0] == part_data[0]:
            exploded = True
            break
    
    if exploded:
        ember = particle_data[10]["created"].copy()
        ember[0] = 10
        
        radius = part_data[1]
        _explode(pos, radius, simstate, ember)

        return ember, True, False
    return part_data, True, False

def lithium(pos:tuple[int,int], part_data:list, neighbors:list, simstate):
    if not neighbors:
        return part_data, True, False
    exploded = False
    for pos, data in neighbors:
        if data[0] == 3:
            exploded = True
            break

    if exploded:
        ember = particle_data[10]["created"].copy()
        ember[0] = 10
        _explode(pos, 3, simstate, ember)
        return ember, True, False

    return part_data, True, False

def fuse(pos:tuple[int,int], part_data:list, neighbors:list, simstate):
    if not neighbors:
        return part_data, True, False
    exploded = False
    for pos, data in neighbors:
        if data[0] in hot_parts:
            exploded = True
            break

    if exploded:
        ember = particle_data[10]["created"].copy()
        ember[0] = 10
        _explode(pos, 3, simstate, ember)
        return ember, True, False

    return part_data, True, False

def flammable(pos:tuple[int,int], part_data:list, neighbors:list, simstate):
    if not neighbors:
        return part_data, True, False
    burned = False
    for pos, data in neighbors:
        if data[0] in hot_parts:
            burned = True
            break

    if burned:
        ember = particle_data[10]["created"].copy()
        ember[0] = 10
        return ember, True, False

    return part_data, True, False

def expire(pos:tuple[int,int], part_data:list, neighbors:list, simstate):
    part_data[1] -= 1
    if part_data[1] < 0:
        return part_data, False, False
    return part_data, True, True

def meltable(pos:tuple[int,int], part_data:list, neighbors:list, simstate):
    if not neighbors:
        return part_data, True, False
    melted = False
    for pos, data in neighbors:
        if data[0] in hot_parts:
            melted = True
            break

    if melted:
        water = particle_data[3]["created"].copy()
        water[0] = 3
        return water, True, False

    return part_data, True, False

type_behaviours = {
    "solid": [],
    "powder":  [
        (0,-1),
        (1,-1),
        (-1,-1)
    ],
    "liquid": [
        (0,-1),
        (1,-1),
        (-1,-1),
        (1,0),
        (-1,0)
    ]
}

def new_part(life:int=0):
    return [-1, life]

hot_parts = [10,3,17]

particle_data = [
    { # 0
        "name": "stone",
        "color": [90,90,90],
        "type": "solid",
        "created": new_part()
    },
    { # 1
        "name": "sand",
        "color": [255,255,100],
        "type": "powder",
        "move_down_chance": 80,
        "created": new_part()
    },
    { # 2
        "name": "crystal",
        "color": [100,255,255],
        "type": "solid",
        "render": "powder",
        "created": new_part()
    },
    { # 3
        "name": "water",
        "color": [0,0,255],
        "type": "liquid",
        "move_down_chance": 60,
        "created": new_part()
    },
    { # 4
        "name": "void",
        "color": [200,0,0],
        "type": "solid",
        "created": new_part()
    },
    { # 5
        "name": "slime",
        "color": [30,200,30],
        "type": "liquid",
        "move_down_chance": 90,
        "movement_chance": 30,
        "created": new_part()
    },
    { # 6
        "name": "oil",
        "color": [200,200,0],
        "type": "liquid",
        "move_down_chance": 90,
        "movement_chance": 60,
        "update_func": flammable,
        "created": new_part()
    },
    { # 7
        "name": "???",
        "color": [200, 0, 200],
        "type": "liquid",
        "move_down_chance": 0,
        "movement_chance":30,
        "created": new_part(),
        "update_func": corrode
    },
    { # 8
        "name": "virus",
        "color": [200,10,10],
        "type": "liquid",
        "update_func": flammable_infect,
        "created": new_part()
    },
    { # 9
        "name": "bomb",
        "color": [20,200,20],
        "type": "powder",
        "update_func": bomb,
        "created": new_part(5)
    },
    { # 10
        "name": "ember",
        "color": [255,255,200],
        "type": "powder",
        "update_func": expire,
        "created": new_part(4)
    },
    { # 11
        "name": "strange",
        "color": [100,255,100],
        "type": "solid",
        "update_func": infect,
        "created": new_part()
    },
    { # 12
        "name": "lithium",
        "color": [240,240,255],
        "type": "solid",
        "update_func": lithium,
        "created": new_part()
    },
    { # 13
        "name": "fuse",
        "color": [200,200,50],
        "type": "solid",
        "update_func": fuse,
        "created": new_part()
    },
    { # 14
        "name": "wood",
        "color": [139,69,19],
        "type": "solid",
        "update_func": flammable,
        "created": new_part()
    },
    { # 15
        "name": "ice",
        "color": [150,200,255],
        "type": "solid",
        "update_func": meltable,
        "created": new_part()
    },
    { # 16
        "name": "metal",
        "color": [100,100,150],
        "type": "solid",
        "created": new_part()
    },
    { # 17
        "name": "lava",
        "color": [255,255,200],
        "type": "liquid",
        "movement_chance": 30,
        "update_func": melt,
        "created": new_part()
    },
    { # 18
        "name": "rock",
        "color": [60,60,60],
        "type": "powder",
        "movement_chance": 0,
        "render": "powder",
        "created": new_part()
    },
]