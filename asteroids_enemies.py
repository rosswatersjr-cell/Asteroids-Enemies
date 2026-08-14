from ursina import *
import time
import ctypes
from tkinter.simpledialog import askinteger
import random
import math

version = '2026.08.14'
def random_not_zero(min_val=-10.0, max_val=10.0, avoid_range=6.0):
    val = random.uniform(min_val, max_val)
    if -avoid_range < val < avoid_range:
        val += avoid_range
    return val
bullets = []
Enemies = []
Asteroids = []
def init_game():
    player_guns = interface.num_player_guns
    global PlayerShip
    PlayerShip = Player_Ship(player_guns)
    enemy_guns = interface.num_enemy_guns
    for e in range(int(interface.num_enemy_ships.text)):
        enemyship = Enemy_Ships(enemy_guns)
        Enemies.append(enemyship)
        interface.num_targets += 1
    for a in range(int(interface.num_asteroids.text)):
        asteroid = Asteroid()
        Asteroids.append(asteroid)
        interface.num_targets += 1
    interface.game_initialize = True
class MenuDropdown(Button):
    def __init__(self, text='', options=None, on_select=None, **kwargs):
        super().__init__(text=text, **kwargs)
        self.options = options or []
        self.on_select = on_select
        self.menu_open = False
        self.menu_buttons = []
        for i, opt in enumerate(self.options):
            b = Button(
                text=opt,
                text_size=1.3,
                parent=self,
                y = -(i+1),
                enabled=False,
                ignore_paused=True,
                scale=(0.15, 1.5),
                origin=(-.5, 0),
                eternal=True,
                on_click=lambda opt=opt: self.select(opt))
            b.is_ui = True
            self.menu_buttons.append(b)
    def select(self, value):
        if self.on_select:
            self.on_select(value)
        self.close_menu()
    def open_menu(self):
        self.menu_open = True
        for b in self.menu_buttons:
            b.enabled = True
    def close_menu(self):
        self.menu_open = False
        for b in self.menu_buttons:
            b.enabled = False
    def on_click(self):
        if self.menu_open:
            self.close_menu()
        else:
            self.open_menu()
    def input(self, key):
        if key == 'left mouse down':
            if not mouse.hovered_entity or not mouse.hovered_entity.has_ancestor(self):
                self.close_menu()
class Interface():
    def __init__(self):
        super().__init__()
        Text.size=0.015
        self.num_enemy_guns = 0
        self.num_player_guns = 0
        self.game_initialize = False
        self.num_targets = 0
        self.exit_button = Button(text='Quit', scale_x=0.08, scale_y=0.03, position=(0.85, 0.485), color="#00ffff", text_size=1.0, text_color=color.black, eternal=True)
        self.score_lbl = Text(text="Score", x=0.84, y=0.40, origin=(0, 0), scale=1.5, color=color.cyan, text_size=0.7, eternal=True)
        self.score_txt = Text(text="0.0", x=0.84, y=0.37, origin=(0, 0), scale=1.5, color=color.cyan, text_size=0.7, eternal=True)
        self.exit_button.on_click = self.exit
        self.enemy_guns = MenuDropdown(
            'Select Enemy Guns',
            options=['1', '2', '3'],
            on_select=self.select_enemy_guns,
            ignore_paused=True,
            scale=(0.17, 0.027),
            position=(0.71, 0.485),
            color=color.cyan,
            text_size=1.0,
            text_color=color.black,
            enabled=True,
            eternal=True)
        self.enemy_guns.is_ui = True
        self.num_guns = MenuDropdown(
            'Select Player Guns',
            options=['1', '2', '3'],
            on_select=self.select_player_guns,
            ignore_paused=True,
            scale=(0.17, 0.027),
            position=(0.524, 0.485),
            color=color.cyan,
            text_size=1.0,
            text_color=color.black,
            enabled=True,
            eternal=True)
        self.num_guns.is_ui = True
        self.space = Entity(name="space", model='cube', texture='stars', double_sided=True,  scale=(camera.fov * window.aspect_ratio, camera.fov), z=10,     # move it behind everything
                            render_order=-1, eternal=True)
        self.game_over = Text(text="", origin=(0, 0), color=color.cyan, scale=7, text_size=7, eternal=True)
        self.asteroids_lbl = Text(text="Enter Number Of Asteroids", x=0.325, y=0.49, origin=(0, 0), color=color.cyan, text_size=0.7, eternal=True)
        self.num_asteroids = InputField(x=0.325, y=0.47, scale=(0.2, 0.03), origin=(0, 0.1), color="#1c0a47", text_size=0.7, 
                                        limit_content_to="0123456789", eternal=True, ignore_paused=True)
        self.num_asteroids.on_value_changed = lambda: self.clamp_input(self.num_asteroids)
        self.num_asteroids.is_ui = True
        self.enemy_lbl = Text(text="Enter Number Of Enemies", x=0.11, y=0.49, origin=(0, 0), color=color.cyan, text_size=0.7, eternal=True)
        self.num_enemy_ships = InputField(x=0.11, y=0.47, scale=(0.2, 0.03), origin=(0, 0.1), color="#1c0a47", text_size=0.7, 
                                          limit_content_to="0123456789", eternal=True, ignore_paused=True)
        self.num_enemy_ships.on_value_changed = lambda: self.clamp_input(self.num_enemy_ships)
        self.num_enemy_ships.is_ui = True
        self.start_stop_button = Button(text='Start', scale_x=0.085, scale_y=0.025, position=(-0.05, 0.485), color=color.cyan, 
                                        text_size=1.0, text_color=color.black, eternal=True, ignore_paused=True)
        self.start_stop_button.is_ui = True
        self.pause_handler = Entity(ignore_paused=True, eternal=True)        
        self.pause_menu = Entity(enabled=True, ignore_paused=True, eternal=True) # Initially hidden
        self.start_stop_button._on_click = lambda: self.toggle_run_pause("key", 'toggle')
        self.pause_handler.input = self.toggle_run_pause
        self.set_defaults()    
    def clamp_input(self, widget):
        text = widget.text
        if text == '':# Allow Empty Input While Typing
            return
        if not text.isdigit():# Reject Non‑Numeric Characters
            widget.text = ''.join([c for c in text if c.isdigit()])
            return
        value = int(widget.text)
        if value > 30:# Clamp to Maximum = 30
            widget.text = str(30)
    def select_enemy_guns(self, txt):
        self.num_enemy_guns = int(txt)
    def select_player_guns(self, txt):
        self.num_player_guns = int(txt)
    def set_defaults(self):
        self.num_asteroids.text = '10'
        self.num_enemy_ships.text = '5'
        self.num_player_guns = 1
        self.num_enemy_guns = 1
    def toggle_run_pause(self, key, arg=None):
        if key == 'escape' or arg == "toggle":
            if self.game_over.text == 'Game Over':
                for e in scene.entities:
                    if not e.eternal:
                        destroy(e)
                self.game_over.text = ''
                bullets.clear()
                Enemies.clear()
                Asteroids.clear()
                self.start_stop_button.text = 'Start'
                self.score_txt.text = '0'
                self.num_targets = 0        
                init_game()
            if application.paused:
                self.start_stop_button.text = 'Pause'
                if not interface.game_initialize:
                    init_game()
            else:
                self.start_stop_button.text = 'Start'
            application.paused = not application.paused
            self.pause_menu.enabled = application.paused # Toggle visibility of the entire pause menu
    def exit(self):# Destroy all Entities Including eternal=True
        application.pause()
        for e in scene.entities:
            destroy(e)
        application.quit()
class Asteroid(Entity):
    def __init__(self):
        rocks = ['asteroid_1.png', 'asteroid_2.png', 'asteroid_3.png', 'asteroid_4.png', 'asteroid_5.png']
        random_texture = random.choice(rocks)
        avoid_x = half_scale_width  * 0.5# Create Asteroids Away From Player Ship 
        avoid_y  = half_scale_height  * 0.5
        position_x = random_not_zero(-half_scale_width, half_scale_width, avoid_x)
        position_y = random_not_zero(-half_scale_height, half_scale_height, avoid_y)  
        super().__init__(model='quad', texture=random_texture, scale=random.uniform(0.1, 0.8), 
                         position=(position_x, position_y, 0), collider='sphere')
        angle = random.uniform(0, 360)
        self.direction = Vec2(math.sin(math.radians(angle)), math.cos(math.radians(angle)))
        self.speed = random.uniform(1, 3)
        self.rotation_speed = random.uniform(-50, 50)
        self.explosion = None
    def wrap(self):
        if self.x > half_scale_width: self.x = -half_scale_width
        if self.x < -half_scale_width: self.x = half_scale_width
        if self.y > half_scale_height: self.y = -half_scale_height
        if self.y < -half_scale_height: self.y = half_scale_height
    def update(self):
        if not application.paused:    
            self.position += Vec2(self.direction.x, self.direction.y) * time.dt * self.speed
            self.rotation_z += self.rotation_speed * time.dt
            self.wrap()
            if self.intersects(PlayerShip).hit:
                ship_radius = PlayerShip.scale_x / 3
                asteroid_radius = self.scale_x / 3
                if abs(distance(PlayerShip, self)) < ship_radius + asteroid_radius:
                    self.color = color.red
                    PlayerShip.color = color.red
                    interface.game_over.text = "Game Over"
                    interface.start_stop_button.text = "Start"
                    application.pause()        
class Player_Bullets(Entity):
    def __init__(self, position, direction, speed=20, life_time=1.5):
        super().__init__(model='sphere', position=position, scale=(0.05, 0.05, 0.05), collider='sphere', color=color.yellow)
        self.direction = direction.normalized()
        self.speed = speed
        self.life_time = life_time
class Player_Ship(Entity):
    def __init__(self, guns):
        self.num_guns = guns
        self.player_ships = ['player_ship_1.png', 'player_ship_2.png', 'player_ship_3.png']
        if self.num_guns == 1:self.texture = self.player_ships[0]
        elif self.num_guns == 2:self.texture = self.player_ships[1]
        else:self.texture = self.player_ships[2]
        super().__init__(model='quad', texture=self.texture, scale=(0.8, 0.8, 0.8), collider='box', position=(0, 0, 0))
        self.speed = 0
        self.max_speed = 5
        self.bullets = []
        self.num_bullets_fired = 0
        self.hits = 0
        self.mouse_x = 0
        if self.num_guns == 1:
            self.guns = [Entity(parent=self, model='cube', color=color.black, position=Vec3(0, -0.2, 1), scale=(0.001, 0.001, 0.001))]
        elif self.num_guns == 2:
            self.guns = [Entity(parent=self, model='cube', color=color.black, position=Vec3(-0.15, -0.2, 1), scale=(0.001, 0.001, 0.001)),
                                Entity(parent=self, model='cube', color=color.black, position=Vec3(0.15, -0.2, 1), scale=(0.001, 0.001, 0.001))]
        else:# 3 Guns
            self.guns = [Entity(parent=self, model='cube', color=color.black, position=Vec3(-0.45, -0.2, 1), scale=(0.001, 0.001, 0.001)),
                                Entity(parent=self, model='cube', color=color.black, position=Vec3(0, -0.2, 1), scale=(0.001, 0.001, 0.001)),
                                Entity(parent=self, model='cube', color=color.black, position=Vec3(0.45, -0.2, 1), scale=(0.001, 0.001, 0.001))]
    def wrap(self):
        if self.x > half_scale_width: self.x = -half_scale_width
        if self.x < -half_scale_width: self.x = half_scale_width
        if self.y > half_scale_height: self.y = -half_scale_height
        if self.y < -half_scale_height: self.y = half_scale_height
    def shoot(self):# 2D Firing
        for gun in self.guns:
            world_pos = gun.world_position
            # 2D forward direction based on rotation_z
            angle = math.radians(PlayerShip.rotation_z)
            direction = Vec3(math.sin(angle), math.cos(angle), 0)
            bullet = Player_Bullets(world_pos, direction)
            bullet.z = 0
            bullets.append(bullet)
            self.num_bullets_fired += 1
    def update(self):
        if not application.paused:    
            dt = time.dt
                # ************** Update Player Ship **************
            if held_keys['right mouse']:# Rotation
                if self.mouse_x != mouse.delta.x:
                    if mouse.delta.x > self.mouse_x:
                        self.rotation_z += 3
                    else:    
                        self.rotation_z -= 3
                    self.mouse_x = mouse.delta.x
            if held_keys['right arrow']:# Rotation
                self.rotation_z += 2
            if held_keys['left arrow']:# Rotation
                self.rotation_z -= 2
            if held_keys['up arrow']:# Forwards Thrust
                angle_rad = math.radians(self.rotation_z)
                self.speed += 0.1
                self.speed = min(self.speed, self.max_speed)
                self.x += math.sin(angle_rad) * 0.1 * self.speed
                self.y += math.cos(angle_rad) * 0.1 * self.speed
            if held_keys['down arrow']:# Reverse Thrust
                angle_rad = math.radians(self.rotation_z)
                self.speed -= 0.1
                self.speed = min(self.speed, self.max_speed)
                self.x += math.sin(angle_rad) * 0.1 * self.speed
                self.y += math.cos(angle_rad) * 0.1 * self.speed
            else:
                self.speed *= 0.98
            # self After Thrust Drift
            angle_rad = math.radians(self.rotation_z)
            self.x += math.sin(angle_rad) * 0.02 * self.speed
            self.y += math.cos(angle_rad) * 0.02 * self.speed
            self.wrap()
            for bullet in bullets[:]:
                if not bullet.enabled:
                    bullets.remove(bullet)
                    continue
                bullet.position += bullet.direction * bullet.speed * time.dt# Update Bullet Movement
                bullet.z = 0
                # Raycast Once Per Bullet
                hit = raycast(
                    bullet.world_position,
                    bullet.direction,
                    distance=bullet.speed * time.dt,
                    ignore=[bullet, self])
                if hit.hit and hit.entity and hit.entity.enabled:# If Bullet Hit Asteroid Or Enemy
                    if hit.entity in Asteroids:# Asteroid Hits
                        hit.entity.collider = None
                        Asteroids.remove(hit.entity)
                        destroy(hit.entity)
                        destroy(bullet)
                        bullets.remove(bullet)
                        self.hits += 1
                        continue
                    if hit.entity in Enemies:# Enemy Hits
                        hit.entity.collider = None
                        Enemies.remove(hit.entity)
                        destroy(hit.entity)
                        destroy(bullet)
                        bullets.remove(bullet)
                        self.hits += 1
                        continue
                bullet.life_time -= time.dt
                if bullet.life_time <= 0:# No Hit, Reduce Bullet Lifetime
                    destroy(bullet)
                    bullets.remove(bullet)
        targets_missed = self.num_bullets_fired - self.hits             
        interface.score_txt.text = str(round(((self.hits / interface.num_targets) * 100) - (0.5 * targets_missed), 1))# 0 - 100
        if self.hits == interface.num_targets:
            interface.game_over.text = "Game Over"
            interface.start_stop_button.text = 'Start'
            application.pause()
    def input(self, key):
        if key == 'space':
            self.shoot()
        elif key == 'left mouse down':
            # Only Shoot If Mouse is NOT Over UI element (Interface Widgets)
            if mouse.hovered_entity is None or not hasattr(mouse.hovered_entity, 'is_ui'):
                self.shoot()
        elif key == 'scroll up':
            angle_rad = math.radians(self.rotation_z)
            self.speed += 0.5
            self.speed = min(self.speed, self.max_speed)
            self.x += math.sin(angle_rad) * 0.1 * self.speed
            self.y += math.cos(angle_rad) * 0.1 * self.speed
        elif key == 'scroll down':
            angle_rad = math.radians(self.rotation_z)
            self.speed -= 0.5
            self.speed = min(self.speed, self.max_speed)
            self.x += math.sin(angle_rad) * 0.1 * self.speed
            self.y += math.cos(angle_rad) * 0.1 * self.speed
class Enemy_Bullets(Entity):
    def __init__(self, position, direction, speed=20, life_time=1.5):
        super().__init__(model='sphere', position=position, scale=(0.05, 0.05, 0.05), collider='sphere', color=color.yellow)
        self.direction = direction.normalized()
        self.speed = speed
        self.life_time = life_time
class Enemy_Ships(Entity):
    def __init__(self, guns):
        self.num_guns = guns
        enemy_ships = ['enemy_ship_1.png', 'enemy_ship_2.png', 'enemy_ship_3.png']
        if self.num_guns == 1:self.texture = enemy_ships[0]
        elif self.num_guns == 2:self.texture = enemy_ships[1]
        else:self.texture = enemy_ships[2]
        avoid_x = half_scale_width  * 0.5# Create Enemy Ships Away From Player Ship 
        avoid_y  = half_scale_height  * 0.5  
        position_x = random_not_zero(-half_scale_width, half_scale_width, avoid_x)
        position_y = random_not_zero(-half_scale_height, half_scale_height, avoid_y)  
        super().__init__(model='quad', texture=self.texture, scale=(0.8, 0.8, 0.8), 
                         position=(position_x, position_y, 0), collider='sphere')
        angle = random.uniform(0, 360)
        self.direction = Vec2(math.sin(math.radians(angle)), math.cos(math.radians(angle)))
        self.num_guns = guns
        self.speed = random.uniform(1, 3)
        self.rotation_speed = 0
        self.rotation_z = angle
        self.enemy_bullets = []
        self.num_enemy_bullets = 0
        self.fire_range_x = half_scale_width * 0.55 # Keep Same aspect_ratio For Firing Range (1.779) 
        self.fire_range_y = self.fire_range_x / window.aspect_ratio
        self.fire_angle = 3
        if self.num_guns == 1:
            self.guns = [Entity(parent=self, model='cube', color=color.black, position=Vec3(0, -0.2, 1), scale=(0.001, 0.001, 0.001))]
        elif self.num_guns == 2:
            self.guns = [Entity(parent=self, model='cube', color=color.black, position=Vec3(-0.15, -0.2, 1), scale=(0.001, 0.001, 0.001)),
                                Entity(parent=self, model='cube', color=color.black, position=Vec3(0.15, -0.2, 1), scale=(0.001, 0.001, 0.001))]
        else:# 3 Guns
            self.guns = [Entity(parent=self, model='cube', color=color.black, position=Vec3(-0.40, -0.2, 1), scale=(0.001, 0.001, 0.001)),
                                Entity(parent=self, model='cube', color=color.black, position=Vec3(0, -0.2, 1), scale=(0.001, 0.001, 0.001)),
                                Entity(parent=self, model='cube', color=color.black, position=Vec3(0.40, -0.2, 1), scale=(0.001, 0.001, 0.001))]
    def wrap(self):
        if self.x > half_scale_width: self.x = -half_scale_width
        if self.x < -half_scale_width: self.x = half_scale_width
        if self.y > half_scale_height: self.y = -half_scale_height
        if self.y < -half_scale_height: self.y = half_scale_height
    def shoot(self):
        for gun in self.guns:
            angle = math.radians(self.rotation_z)
            direction = Vec3(math.sin(angle), math.cos(angle), 0)
            world_pos = gun.world_position + direction * 0.8
            bullet = Enemy_Bullets(world_pos, direction)
            bullet.z = 0
            bullets.append(bullet)
    def update(self):
        if not application.paused:    
            self.position += Vec2(self.direction.x, self.direction.y) * time.dt * self.speed
            self.rotation_z += self.rotation_speed * time.dt
            self.wrap()
            # Check For Enemy Ships Aligned And In Range With Player Ship.
            # If Angle Aligned And In Range Then Shoot
            target_dir_center = Vec2(PlayerShip.position.x - self.position.x,
                            PlayerShip.position.y - self.position.y).normalized()
            facing_dir_center = Vec2(self.direction.x,
                            self.direction.y).normalized()
            angle_target = math.degrees(math.atan2(target_dir_center.y, target_dir_center.x))
            angle_facing = math.degrees(math.atan2(facing_dir_center.y, facing_dir_center.x))
            angle_diff = abs(angle_target - angle_facing)
            distance_x = abs(self.position.x - PlayerShip.position.x)
            distance_y = abs(self.position.y - PlayerShip.position.y)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            if abs(angle_diff) <= self.fire_angle:# Angle Aligned
                if distance_x <= self.fire_range_x and distance_y <= self.fire_range_y:# Inside firing Range
                    self.shoot()
                    for bullet in bullets[:]:
                        if not bullet.enabled:
                            bullets.remove(bullet)
                            continue
                        bullet.position += bullet.direction * bullet.speed * time.dt# Update Bullet Movement
                        bullet.z = 0
                        # Raycast Once Per Bullet
                        hit = raycast(
                            bullet.world_position,
                            bullet.direction,
                            distance=bullet.speed * time.dt,
                            debug=False,
                            ignore=[bullet, self])
                        if hit.hit and hit.entity and hit.entity.enabled:# If bullet hit PlayerShip Or Asteroid
                            if hit.entity in Asteroids:# Asteroid Hit
                                hit.entity.collider = None
                                Asteroids.remove(hit.entity)
                                destroy(hit.entity)
                                destroy(bullet)
                                bullets.remove(bullet)
                                continue
                            if hit.entity is PlayerShip:# PlayerShip Hit
                                hit.entity.collider = None
                                PlayerShip.color = color.red
                                interface.game_over.text = "Game Over"
                                interface.start_stop_button.text = "Start"
                                application.pause()        
                        bullet.life_time -= time.dt
                        if bullet.life_time <= 0:# No Hit, Reduce Bullet Lifetime
                            destroy(bullet)
                            bullets.remove(bullet)
            elif self.intersects(PlayerShip).hit:
                ship_radius = PlayerShip.scale_x / 3
                enemy_radius = self.scale_x / 3
                if abs(distance(PlayerShip, self)) < ship_radius + enemy_radius:
                    self.color = color.red
                    PlayerShip.color = color.red
                    interface.game_over.text = "Game Over"
                    interface.start_stop_button.text = "Start"
                    application.pause()        
def change_screen_size(default_size):
    msg1="Do You Wish To Change The Screen Size?\n"
    msg2=f"The Default Size Is Full Screen (Width = {default_size}).\n"
    msg3="If Yes, Enter The New Screen Width Below Then Select OK.\n"
    msg4="The Screen Height Will Be Calculated Using The New Width.\n"
    msg5="If No, Select Cancel."
    msg=msg1+msg2+msg3+msg4+msg5
    min_value = int(default_size / 3)
    new_width = askinteger(title="New Screen Width", prompt=msg, initialvalue=default_size, minvalue=min_value, maxvalue=default_size)
    return new_width
if __name__ == '__main__':
    scale_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
    mon_width = ctypes.windll.user32.GetSystemMetrics(0) * scale_factor
    mon_height = ctypes.windll.user32.GetSystemMetrics(1) * scale_factor
    # Ursina Only Likes @1.778 Display Aspect Ratio
    # Convert All Resolutions To 1.778 (16:9)Aspect Ratio
    # Using Monitor Width As Baseline.
    new_width=change_screen_size(int(mon_width))
    if new_width==None:new_width=int(mon_width)
    new_width = int(new_width)
    new_height = int(new_width / (16 / 9))# Change Screen Size but Keep 16:9 Aspect Ratio 
    window_size = (new_width, new_height)
    app=Ursina(title="Enemy Ships & Asteroids", size=window_size, fullscreen=False, vsync=False, development_mode=False, icon='starship.ico')
    if new_width == int(mon_width):
        window.position = (0.0, 0.0)
        borderless = True
    else:
        borderless = False
        win_w, win_h = window_size
        center_x = (mon_width - win_w) // 2
        center_y = (mon_height - win_h) // 2
        window.position = (center_x, center_y)
    window.always_on_top = True
    window.exit_button.enabled = False 
    window.color = color.black
    camera.orthographic = True
    camera.fov = 9# world height, world width = world height * aspect ratio
    half_scale_height = camera.fov / 2# +- 5
    half_scale_width  = half_scale_height * window.aspect_ratio
    application.pause()
    interface = Interface()
    app.run()
