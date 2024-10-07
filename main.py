import math
import pygame
import time
import random

from particle_data import particle_data, type_behaviours
from boilerplate import quicksin, quickrand, neighbor_cords

class SparseGrid:
    def __init__(self, data:dict={}):
        self.data = data.copy()

    def get(self, pos:tuple[int,int]):
        return self.data.get(pos, None)
    
    def set(self, pos:tuple[int,int], data):
        if data == None:
            if pos in self.data:
                self.data.pop(pos)
            return
        self.data[pos] = data

    def get_all(self):
        return self.data.items()

    def copy(self):
        return SparseGrid(self.data)

class ChunkedGrid:
    def __init__(self, chunk_size:tuple[int,int]=(16,16), data:dict={}):
        self.data = SparseGrid(data)
        self.chunk_size = chunk_size

    def _get_chunk_cords(self,pos:tuple[int,int]):
        x, y = pos
        chunk_cords = math.floor(x / self.chunk_size[0]), math.floor(y / self.chunk_size[1])
        subchunk_cords = (x % self.chunk_size[0]), (y % self.chunk_size[1])
        return chunk_cords, subchunk_cords

    def get(self,pos:tuple[int,int]):
        chunk_cords, subchunk_cords = self._get_chunk_cords(pos)
        chunk = self.data.get(chunk_cords)
        if chunk:
            return chunk.get(subchunk_cords)
        return None

    def get_chunk(self, pos:tuple[int,int]):
        return self.data.get(pos)

    def set(self,pos:tuple[int,int], data):
        chunk_cords, subchunk_cords = self._get_chunk_cords(pos)
        chunk = self.data.get(chunk_cords)
        if not chunk:
            chunk = SparseGrid()
            chunk.set(subchunk_cords, data)
            self.data.set(chunk_cords,chunk)
        else:
            chunk.set(subchunk_cords, data)

        if not chunk.data:
            self.data.set(chunk_cords, None)
    
    def copy(self):
        chunks_copy_data = {}
        for pos, chunk in self.data.get_all():
            chunks_copy_data[pos] = chunk.copy()

        return ChunkedGrid(self.chunk_size, chunks_copy_data)

class Simulation:
    def __init__(self, chunk_size:tuple[int,int], lazy:bool=True, lazy_range:int=2) -> None:
        self.lazy = lazy
        self.lazy_range = lazy_range

        self.chunk_size = chunk_size
        self.sim = ChunkedGrid(self.chunk_size)
        
        self.active = {}
        self.default_life = 6
    
    def set_pos(self, pos:tuple[int,int], part_id:int):
        chunk_cords, subchunk_cords = self.sim._get_chunk_cords(pos)

        self.activate_around(chunk_cords)

        if part_id == None:
            part_dat = None
        else:
            part_dat:list = particle_data[part_id]["created"].copy()
            part_dat[0] = part_id
        self.sim.set(pos, part_dat)

    def get_chunks(self):
        return self.sim.data.get_all()

    def update(self):
        new_state = self.sim.copy()

        old_active = self.active.copy()
        for chunk_pos in old_active.keys():
            self.update_chunk(chunk_pos, new_state)

        self.sim = new_state

    def get_real(self, pos:tuple, chunk_cords:tuple):
        return (
            pos[0] + chunk_cords[0] * self.chunk_size[0],
            pos[1] + chunk_cords[1] * self.chunk_size[1]
        )
    
    def activate_around(self, pos:tuple):
        x, y = pos
        neighbors = [
            (x,y),
            (x - 1, y),  # West
            (x + 1, y),  # East
            (x, y - 1),  # North
            (x, y + 1),  # South
            (x - 1, y - 1),  # Northwest
            (x + 1, y - 1),  # Northeast
            (x - 1, y + 1),  # Southwest
            (x + 1, y + 1),  # Southeast
        ]

        for neighbor in neighbors:
            self.active[neighbor] = self.default_life

    def update_chunk(self, chunk_cords:tuple[int,int], simstate:ChunkedGrid):
        chunk:SparseGrid = simstate.get_chunk(chunk_cords)
        if not chunk:
            self.active.pop(chunk_cords)
            return

        moved = False

        old = chunk.copy()
        for pos, part_data in old.get_all():
            part_type = part_data[0]
            particle_type_data:dict = particle_data[part_type]

            movements = type_behaviours[particle_type_data["type"]]
            move_down_chance = particle_type_data.get("move_down_chance",100)
            movement_chance = particle_type_data.get("movement_chance",100)
            
            old_pos = self.get_real(pos, chunk_cords)
            new_pos = old_pos

            neighbors = {}
            for relpos in neighbor_cords:
                real_pos = (new_pos[0] + relpos[0], new_pos[1] + relpos[1])
                part_at_pos = simstate.get(real_pos)
                if part_at_pos:
                    neighbors[real_pos] = part_at_pos

            possible_movements = []
            move_down = None
            for movement in movements:
                movement_pos = (new_pos[0] + movement[0], new_pos[1] + movement[1])
                if movement_pos[1] < 1:
                    continue
                part_at_pos = neighbors.get(movement_pos, None)
                if (not part_at_pos) or (part_at_pos[0] == 4):
                    deleted = False
                    if part_at_pos and part_at_pos[0] == 4:
                        deleted = True

                    movement_data = (movement_pos, deleted)
                    possible_movements.append(movement_data)
                    if movement == (0, -1):
                        move_down = movement_data

            deleted_self = False
            if "update_func" in particle_type_data:
                update_func = particle_type_data["update_func"]
                part_data, exists, active = update_func(old_pos, part_data, list(neighbors.items()), simstate)
                deleted_self = not exists

                if active:
                    moved = True
            
            # set new_pos to one of the possible movements
            # set deleted
            
            deleted = False
            if possible_movements:
                p_m_count = len(possible_movements)
                if move_down and (quickrand(100) <= move_down_chance - 1):
                    new_pos, deleted = move_down
                    moved = True
                else:
                    if not move_down:
                        if (quickrand(100) >= movement_chance - 1):
                            continue
                    moved = True
                    if p_m_count == 1:
                        new_pos, deleted = possible_movements[0]
                    else:
                        new_pos, deleted = possible_movements[quickrand(len(possible_movements))]
            
            if deleted_self:
                deleted = True

            # Movement logic
            if possible_movements or deleted:
                simstate.set(old_pos, None)

            if not deleted:
                simstate.set(new_pos, part_data)
        
        if not simstate.get_chunk(chunk_cords):
            self.active.pop(chunk_cords)
        elif not moved:
            self.active[chunk_cords] -= 1
            if self.active[chunk_cords] <= 0:
                self.active.pop(chunk_cords)
        elif moved:
            self.active[chunk_cords] = self.default_life
            self.activate_around(chunk_cords)
        
class Interface:
    def get_relative(self,pos:tuple[int,int]):
        return (pos[0] - self.camera_pos[0]), ((self.ZOOM_HEIGHT - pos[1]) - self.camera_pos[1])

    def render_parts(self):
        positions = []
        for chunk_pos, chunk in self.sim.get_chunks():
            ajust = (
                chunk_pos[0] * self.sim.chunk_size[0],
                chunk_pos[1] * self.sim.chunk_size[1]
            )
            relpos = self.get_relative((ajust[0], ajust[1] + self.sim.chunk_size[1]))
            in_screen_dim = lambda i: (-(self.sim.chunk_size[i] * self.sim.lazy_range) < (relpos[i]) < ((self.ZOOM_WIDTH, self.ZOOM_HEIGHT)[i] + (self.sim.chunk_size[i] * self.sim.lazy_range)))
            if not (in_screen_dim(0) and in_screen_dim(1)): # Skip invisible chunks
                if self.sim.lazy:
                    if chunk_pos in self.sim.active:
                        self.sim.active.pop(chunk_pos)
                        self.lazy_unloaded.add(chunk_pos)
                continue
            else:
                if chunk_pos in self.lazy_unloaded:
                    self.sim.active[chunk_pos] = self.sim.default_life
                    self.lazy_unloaded.remove(chunk_pos)

            for part_pos, part in chunk.get_all():
                x = part_pos[0] + ajust[0]
                y = part_pos[1] + ajust[1]

                positions.append(((x,y),part))

            if DEBUG:
                if chunk_pos in self.sim.active:
                    chunk_color = (150, 50, 50)
                else:
                    chunk_color = (50, 50, 50)

                pygame.draw.rect(self.surf, chunk_color, (*relpos, *self.sim.chunk_size), 1)

        for pos, part in positions:
            particle_type = particle_data[part[0]]["type"]
            if "render" in particle_data[part[0]]:
                particle_type = particle_data[part[0]]["render"]
            relative_pos = self.get_relative(pos)

            part_color = particle_data[part[0]]["color"]

            brightness = 1
            if particle_type == "liquid":
                brightness = ((quicksin((self.frame_counter * 5) + (pos[0] + pos[1]) * 30) + 1) / 8) + 0.75
            elif particle_type == "powder":
                brightness = (((pos[0] + pos[1]) % 3) / 8) + 0.75
            
            part_color = (min(part_color[0] * brightness, 255),min(part_color[1] * brightness, 255),min(part_color[2] * brightness, 255))

            pygame.draw.line(self.surf, part_color, relative_pos, relative_pos)

    def render_debug_text(self, lines:list):
        for i, line in enumerate(lines):
            surf = self.font.render(line, False, (255,255,255))
            self.screen.blit(surf, (10,(10+(i*30))))

    def render_debug(self):
        brightness = ((quicksin(self.frame_counter * 2) + 1) / 4) + 0.75

        brush_color = particle_data[self.brush]["color"]
        brush_color = (min(brush_color[0] * brightness, 255),min(brush_color[1] * brightness, 255),min(brush_color[2] * brightness, 255))

        pygame.draw.rect(self.surf, brush_color, (self.resized_mouse_pos[0] - self.brush_size, self.resized_mouse_pos[1] - self.brush_size, self.brush_size * 2 + 1, self.brush_size * 2 + 1), 1)

        scaled_surf = pygame.transform.scale(self.surf, (self.WIDTH, self.HEIGHT))
        self.screen.blit(scaled_surf, (0,0))

        texts = [
            f"FPS: {int(self.clock.get_fps())}",
            f"Brush: {particle_data[self.brush]["name"]}",
            f"Zoom {self.zoom}"
        ]

        if DEBUG:
            debug_lines = [
                f"",
                f"Times:",
                f"Update: {self.times.get("update",None)}",
                f"Render: {self.times.get("render",None)}",
                f"Total: {self.times.get("total",None)}"
            ]

            for line in debug_lines:
                texts.append(line)

        at_cursor = self.sim.sim.get(self.rel_mouse_pos)
        if at_cursor:
            at_cursor = at_cursor.copy()
            at_cursor[0] = particle_data[at_cursor[0]]["name"]

            texts.append(f"")
            texts.append(f"Hover: {at_cursor}")

        self.render_debug_text(texts)

    def render_part_select(self, padding:int, height:int):
        label_size = (100, (height - (padding * 2)))

        pos = (padding, self.HEIGHT - (padding + height))
        size = (self.WIDTH - (padding * 2), height)

        fits = size[0] // (label_size[0] + padding)

        scroll = (self.brush - (fits // 2)) * (label_size[0] + padding)

        surf = pygame.Surface(size)
        surf.fill((50,50,50))

        font = pygame.font.Font(None, round(height * 0.6))

        for i, part_type_data in enumerate(self.particles):
            label_pos = (
                (padding + (i * (label_size[0] + padding))) - scroll, 
                (padding)
            )

            rect_line_width = 2
            text_color = (255,255,255)
            if i == self.brush:
                rect_line_width = 0
                text_color = (0,0,0)

            # Render label
            pygame.draw.rect(surf, part_type_data["color"], (label_pos, label_size),rect_line_width)

            # Render the text
            text = font.render(part_type_data["name"], True, text_color)
            
            # Get the rectangle for the text and center it inside the label
            text_rect = text.get_rect(center=(
                label_pos[0] + label_size[0] // 2, 
                label_pos[1] + label_size[1] // 2
            ))

            surf.blit(text, text_rect)
        
        self.screen.blit(surf, pos)

    def render(self):
        self.surf = pygame.Surface((self.WIDTH // self.zoom, self.HEIGHT // self.zoom))

        self.render_parts()
        pygame.draw.rect(self.surf, (100,100,100), ((0,self.get_relative((0,0))[1]), (self.ZOOM_WIDTH, 1)))

        self.render_debug()
        self.render_part_select(10, 50)

        pygame.display.flip()  # Update the display

    def mainloop(self):
        def add_with_brush(pos:tuple, part_id:int, brush_size:int):
            for x in range(pos[0] - brush_size, pos[0] + brush_size + 1):
                for y in range(pos[1] - brush_size, pos[1] + brush_size + 1):
                    if y < 1:
                        continue
                    if (part_id == None) or (not self.sim.sim.get((x, y))):
                        self.sim.set_pos((x, y), part_id)

        if self.mouse[1]:
            add_with_brush(self.rel_mouse_pos, self.brush, self.brush_size)
        elif self.mouse[3]:
            add_with_brush(self.rel_mouse_pos, None, self.brush_size)

        t_prev = time.perf_counter()
        self.sim.update()

        t_update = time.perf_counter()
        self.render()

        t_render = time.perf_counter()

        digits = 5
        self.times["update"] = round(t_update - t_prev, digits)
        self.times["render"] = round(t_render - t_update, digits)
        self.times["total"] = round(t_render - t_prev, digits)

        self.clock.tick(60)  # Limit the framerate to 60 FPS

    def set_zoom(self, zoom:float):
        self.true_zoom = zoom
        self.zoom = round(zoom)
        self.ZOOM_WIDTH = self.WIDTH // self.zoom
        self.ZOOM_HEIGHT = self.HEIGHT // self.zoom

    def __init__(self) -> None:
        self.WIDTH, self.HEIGHT = 1200, 800

        pygame.init()
        self.font = pygame.font.SysFont(None, 30)  # Font and size

        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))  # Set the window size
        pygame.display.set_caption("Simulation")

        self.clock = pygame.time.Clock()

        self.brush = 1
        self.brush_true = self.brush
        self.brush_size = 3

        self.particles = []
        for data in particle_data:
            self.particles.append({
                "color": data["color"],
                "name": data["name"]
            })

        self.set_zoom(18)
        self.zoom_speed = 1.01

        self.camera_pos = [0,round(self.ZOOM_HEIGHT * 0.2)]
        self.camera_speed = 1

        self.scroll_sensitivity = 3
        self.brush_size_scroll = self.brush_size * self.scroll_sensitivity

        size = 4
        self.sim = Simulation(chunk_size=(size, size))
        self.lazy_unloaded = set()

        running = True
        self.mouse = {
            1: False,
            2: False,
            3: False,
            4: False,
            5: False
        }

        self.times = {}

        self.frame_counter = 0

        while running:
            self.mouse_pos = pygame.mouse.get_pos()
            self.resized_mouse_pos = (self.mouse_pos[0] // self.zoom), (self.mouse_pos[1] // self.zoom)
            self.rel_mouse_pos = (self.resized_mouse_pos[0] + self.camera_pos[0], self.ZOOM_HEIGHT - (self.resized_mouse_pos[1] + self.camera_pos[1]))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for i in range(5):
                        i += 1
                        if event.button == i:
                            self.mouse[i] = True

                            if i == 4:
                                self.brush_size_scroll += 1
                            elif i == 5:
                                self.brush_size_scroll -= 1
                                if self.brush_size_scroll < 0:
                                    self.brush_size_scroll = 0

                    self.brush_size = self.brush_size_scroll // self.scroll_sensitivity

                elif event.type == pygame.MOUSEBUTTONUP:
                    for i in range(5):
                        if event.button == i + 1:
                            self.mouse[i + 1] = False

            pressed = pygame.key.get_pressed()      
            if pressed[pygame.K_w]:
                self.camera_pos[1] -= self.camera_speed
            if pressed[pygame.K_s]:
                self.camera_pos[1] += self.camera_speed
            if pressed[pygame.K_a]:
                self.camera_pos[0] -= self.camera_speed
            if pressed[pygame.K_d]:
                self.camera_pos[0] += self.camera_speed

            if pressed[pygame.K_LEFT]:
                self.brush_true -= 0.15
                if self.brush_true < 0:
                    self.brush_true = len(particle_data) - 1
            if pressed[pygame.K_RIGHT]:
                self.brush_true += 0.15
                if self.brush_true > len(particle_data) - 1:
                    self.brush_true = 0
            self.brush = round(self.brush_true)

            if pressed[pygame.K_MINUS]:
                if not self.zoom == 1:
                    self.set_zoom(self.true_zoom / self.zoom_speed)
            if pressed[pygame.K_EQUALS]:
                self.set_zoom(self.true_zoom * self.zoom_speed)

            self.frame_counter += 1
            if self.frame_counter >= 3600:
                self.frame_counter = 0

            self.mainloop()

        pygame.quit()

if __name__ == "__main__":
    DEBUG = False
    interface = Interface()
