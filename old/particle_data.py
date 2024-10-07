def infect(pos:tuple[int,int], part_data:list, neighbors:list, simstate):
    for pos, data in neighbors:
        if data[0] == part_data[0]:
            continue
        simstate.set(pos, part_data)

    return part_data, True

def corrode(pos:tuple[int,int], part_data:list, neighbors:list, simstate):
    powder = particle_data[1]["created"].copy()
    powder[0] = 1
    for pos, data in neighbors:
        if particle_data[data[0]]["type"] == "solid":
            simstate.set(pos, powder.copy())

    return part_data, True

type_behaviours = {
    "solid": [],
    "powder":  [
        [0,-1],
        [1,-1],
        [-1,-1]
    ],
    "liquid": [
        [0,-1],
        [1,-1],
        [-1,-1],
        [1,0],
        [-1,0]
    ]
}
PART = "PART"
particle_data = [
    {
        "name": "rock",
        "color": [90,90,90],
        "type": "solid",
        "created": [PART,0]
    },
    {
        "name": "sand",
        "color": [255,255,100],
        "type": "powder",
        "move_down_chance": 80,
        "created": [PART,0]
    },
    {
        "name": "crystal",
        "color": [100,255,255],
        "type": "powder",
        "movement_chance": 0,
        "created": [PART,0]
    },
    {
        "name": "water",
        "color": [0,0,255],
        "type": "liquid",
        "move_down_chance": 60,
        "created": [PART,0]
    },
    {
        "name": "void",
        "color": [200,0,0],
        "type": "solid",
        "created": [PART,0]
    },
    {
        "name": "slime",
        "color": [30,200,30],
        "type": "liquid",
        "move_down_chance": 90,
        "movement_chance": 30,
        "created": [PART,0]
    },
    {
        "name": "oil",
        "color": [200,200,0],
        "type": "liquid",
        "move_down_chance": 90,
        "movement_chance": 60,
        "created": [PART,0]
    },
    {
        "name": "???",
        "color": [200, 0, 200],
        "type": "liquid",
        "move_down_chance": 0,
        "movement_chance":30,
        "created": [PART,0],
        "update_func": corrode
    },
    {
        "name": "virus",
        "color": [200,10,10],
        "type": "liquid",
        "update_func": infect,
        "created": [PART,0]
    }
]