from pygame import *
import pickle, math, mouse_extras, tower_manager, enemy_manager
import global_functions as gfunc

def run(level, window_size):

    # Set up
    window = display.set_mode(window_size, RESIZABLE)
    clock = time.Clock()

    # Get level info
    level_info = pickle.load(open('levels.dat', 'rb'))[level]

    # Scale window correctly
    message_height = 1
    game_grid = level_info['grid_size']
    scale = min(window_size[0] / game_grid[0], window_size[1] / (game_grid[1] + message_height))
    game_size = scale * game_grid[0], scale * game_grid[1]
    game_window = Surface(game_size)

    # Make message surface
    message_surf = Surface((game_size[0], math.ceil(scale)))

    # Start up handlers
    tower_handler = tower_manager.Tower_Handler()
    enemy_handler = enemy_manager.Enemy_Handler()

    # Fancy hitbox things
    def show_dev_things():

        if key.get_pressed()[K_F2]:

            # Enemies
            for enemy in enemy_handler.enemies:
                rect = enemy.get_rect(game_scale)

                if rect:
                    draw.rect(game_window, (255, 100, 100), rect, 2)

            # Towers
            for tower in tower_handler.towers:
                draw.rect(game_window, (100, 255, 100), (tower.pos[0] * game_scale, tower.pos[1] * game_scale, game_scale, game_scale), 2)

                # Projectiles
                for obj in tower.projectiles:
                    draw.rect(game_window, (100, 100, 255), obj.get_rect(game_scale), 2)



    # Work out tower selection size
    num = len(tower_handler.usable_towers)
    rows = math.ceil(num / game_grid[0])
    playing_grid = list(game_grid)
    playing_grid[1] += rows
    tower_select_rows = rows

    # Make background functions (just for ease later)
    def show_background_image(background): game_window.blit(background, (0,0))
    def show_background_colour(background): game_window.fill(background)

    def resize(window_size, window, game_window, game_size):

        # Size and offset the game correctly
        new = gfunc.event_loop()
        scale = min(window_size[0] / playing_grid[0], window_size[1] / (playing_grid[1] + message_height))
        game_size = playing_grid[0] * scale, playing_grid[1] * scale
        game_window = Surface(game_size)
        offset = (window_size[0] - game_size[0]) / 2, math.ceil((window_size[1] - game_size[1] + scale) / 2)

        if new: clock.tick()

        if new: window_size = new; window = display.set_mode(window_size, RESIZABLE)
        return offset, window, window_size, game_window, game_size, scale

    # Set background functions
    if type(level_info['background']) == tuple: show_background = show_background_colour; background = level_info['background']
    else: show_background = show_background_image; background = image.load(level_info['background'])

    # Path message
    red_value = 255
    last_red_change = -1

    enemy_handler.load_enemies(level_info['enemies'])

    # Game loop (loop through the stages)
    while True:

        # Set up loop (game)
        enemy_handler.load_enemies(level_info['enemies'])
        while True:

            # Must be at start
            offset, window, window_size, game_window, game_size, game_scale = resize(window_size, window, game_window, game_size)
            mouse_extras.update(game_scale, playing_grid, offset)
            message_surf = Surface((game_size[0], math.ceil(game_scale)))

            # Does the game need to progress to the next stage?
            k = key.get_pressed()
            if k[K_RETURN] and enemy_handler.path: break

            # Does the game grid need to be cleared?
            if k[K_c]: tower_handler.clear_towers()

            # Clear window(s)
            show_background(background)
            message_surf.fill((150, 150, 150))

            # Do important things
            dt = clock.tick() / 1000

            # Update towers
            tower_handler.tower_selection(game_window, game_scale, game_grid, tower_select_rows)

            # Update path
            enemy_handler.update_path(game_window, game_scale, game_grid, tower_handler.blocks, dt)

            # Show message

            if enemy_handler.path:
                gfunc.show_message('Build stage!', message_surf, size = game_scale * 0.7, pos = ('mid', 'top'))
                gfunc.show_message('Press enter to start the wave!', message_surf, size = game_scale * 0.5, pos = ('mid', 'low'), colour = (90, 90, 90))
            else:
                gfunc.show_message('It must be possible for the enemies to get through!', message_surf, colour = (red_value, 50, 0), boarder = 0.3)

                # Make the error message change colour for a cool animation
                red_value += last_red_change * dt * 500
                red_value = max(min(255, red_value), 150)
                if red_value >= 255 or red_value <= 150: last_red_change = -last_red_change

            # Must be at end
            window.fill((30, 30, 30))
            window.blit(game_window, offset)
            window.blit(message_surf, (offset[0], offset[1] - game_scale))

            display.update()


        enemy_handler.set_enemy_path()

        # Fight!
        restart = False
        tower_handler.reset()

        while not restart:

            # Must be at start
            offset, window, window_size, game_window, game_size, game_scale = resize(window_size, window, game_window, game_size)
            mouse_extras.update(game_scale, playing_grid, offset)
            message_surf = Surface((game_size[0], math.ceil(game_scale)))

             # Clear/set up window(s)
            show_background(background)
            message_surf.fill((150, 150, 150))

            # Do we want to restart the game?
            if key.get_pressed()[K_r]:
                enemy_handler.load_enemies(level_info['enemies'])
                restart = True
                break

            tower_handler.draw_selection_block(game_window, game_scale, game_grid, tower_select_rows)

            # Do important things
            dt = clock.tick() / 1000

            # Update enemies
            if enemy_handler.update_enemies(game_window, game_scale, game_grid, dt):
                state = 0
                break

            if enemy_handler.enemies == []:
                state = 1
                break

            # Do the damage
            enemy_handler.enemies = tower_handler.do_damage(enemy_handler.enemies, game_scale)

            # Update towers
            tower_handler.update_towers(game_window, game_scale, game_grid, dt)

            # Fancy
            show_dev_things()

            # Must be at end
            window.fill((30, 30, 30))
            window.blit(game_window, offset)
            window.blit(message_surf, (offset[0], offset[1] - game_scale))

            display.update()


        # Death screen

        window_y = window_size[1]
        while not restart:

            # Must be at start
            offset, window, window_size, game_window, game_size, game_scale = resize(window_size, window, game_window, game_size)
            mouse_extras.update(game_scale, playing_grid, offset)
            message_surf = Surface((game_size[0], math.ceil(game_scale)))

             # Clear/set up window(s)
            show_background(background)
            message_surf.fill((150, 150, 150))

            # Do we want to restart the game?
            if key.get_pressed()[K_r]:
                enemy_handler.load_enemies(level_info['enemies'])
                restart = True
                break

            # Show tower selection thing
            tower_handler.draw_selection_block(game_window, game_scale, game_grid, tower_select_rows)

            # Do important things
            dt = clock.tick() / 1000

            # Show towers
            tower_handler.show_towers(game_window, game_scale)

            # Update enemies
            enemy_handler.update_enemies(game_window, game_scale, game_grid, dt)

            # Show death window
            if death_window(game_window, game_size, offset, (0, window_y)): break

            # Move death window
            max_height = -game_scale * tower_select_rows / 2
            window_y -= dt * max((window_y - max_height) * 10, 1)

            window_y = max(window_y, max_height)

            # Must be at end
            window.fill((30, 30, 30))
            window.blit(game_window, offset)
            window.blit(message_surf, (offset[0], offset[1] - game_scale))

            display.update()


base_font = font.SysFont(None, 100)
def death_window(window, window_size, window_offset, offset):

    background_colour = (150, 150, 150)
    text_colour = (255, 255, 255)

    scale = min(window_size)
    margin_x = scale / 8
    margin_y = scale / 15

    width = scale / 16 * 16
    height = scale / 16 * 9

    window_rect = [(window_size[0] - width) / 2 + offset[0], (window_size[1] - height) / 2 + offset[1], width, height]
    draw.rect(window, background_colour, window_rect)


    # Show header and get scale etc
    header = 'You Suck!'

    max_width = width - margin_x * 2
    max_height = height - margin_y * 2

    test = base_font.render(header, 0, (0, 0, 0))
    test_rect = test.get_rect()

    width_scale = max_width / test_rect.width
    height_scale = max_height / test_rect.height

    scale = min(width_scale, height_scale)

    new_font = font.SysFont(None, int(100 * scale))
    header_message = new_font.render(header, 0, text_colour)

    window.blit(header_message, (window_rect[0] + margin_x, window_rect[1] + margin_y))


    # Buttons
    width, height = 175 * scale, 75 * scale
    restart = gfunc.text_button(window, window_size, window_offset, 'Restart', text_colour + (200,), (window_rect[0] + (window_rect[2] - width) / 2, window_rect[1] + window_rect[3] * 0.6, width, height))

    return restart

