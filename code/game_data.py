project_name = "pygame library"
version = "1.0.0"  # TODO not currently in use, purely placeholder

tile_size = 16  # keep to prevent errors, even if game doesn't need tiles
screen_width = 80 * tile_size  # arbitrary
screen_height = 50 * tile_size  # arbitrary
# MUST BE INT
scaling_factor = 1  # how much the screen is scaled up before blitting on display

game_speed = 60  # fps

controller_map = {'square': 0, 'X': 1, 'circle': 2, 'triangle': 3, 'L1': 4, 'R1': 5, 'L2': 6, 'R2': 7, 'share': 8,
                  'options': 9, 'left_analog_press': 10, 'right_analog_press': 11, 'PS': 12, 'touchpad': 13,
                  'left_analog_x': 0,  'left_analog_y': 1, 'right_analog_x': 2,  'right_analog_y': 5}

fonts = {'small_font': '../assets/fonts/small_font.png',
         'large_font': '../assets/fonts/large_font.png'}
