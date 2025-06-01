import pygame
import sys
import math
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dart Throwing Game")

# Colors - Modern Vibrant Palette
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BACKGROUND = (22, 26, 54)     # Dark navy blue background #161a36
UI_ACCENT = (255, 107, 107)   # Coral red for UI elements #ff6b6b
UI_SECONDARY = (58, 134, 255) # Bright blue for secondary UI #3a86ff
DARTBOARD_OUTER = (240, 147, 43)  # Amber orange #f0932b
DARTBOARD_MIDDLE = (72, 219, 251) # Bright cyan #48dbfb
DARTBOARD_CENTER = (235, 77, 75)  # Tomato red #eb4d4b
BUTTON_GREEN = (85, 239, 196)  # Mint green #55efc4
BUTTON_HOVER = (129, 236, 236) # Light cyan #81ecec
TEXT_HIGHLIGHT = (253, 203, 110) # Light orange #fdcb6e

# Game state
current_level = 1
throws_left = 3
score = 0
game_over = False
show_helper = True
helper_timer = 180
game_started = False  # Track if the game has started

# Celebration variables
celebration_active = False
celebration_start_time = 0

# Level 3 timer variables
level3_time_limit = 20 * 1000  # 20 seconds in milliseconds
level3_start_time = 0
level3_time_remaining = level3_time_limit
# Level 1 specific variables
level1_center_x = WIDTH - 180
level1_center_y = HEIGHT // 2
level1_outer_radius = 100
level1_middle_radius = 55
level1_bullseye_radius = 20

# Level 2 specific variables
level2_center_x = WIDTH - 180
level2_center_y = HEIGHT // 2
level2_outer_radius = 100
level2_middle_radius = 55
level2_bullseye_radius = 20
level2_move_speed = 3
level2_move_direction = 1
level2_y_min = 150
level2_y_max = HEIGHT - 150

# Level 3 specific variables
level3_center_x = WIDTH - 180
level3_center_y = HEIGHT // 2
level3_outer_radius = 100
level3_middle_radius = 55
level3_bullseye_radius = 20
level3_move_speed = 3
level3_move_direction = 1
level3_y_min = 150
level3_y_max = HEIGHT - 150

# Obstacle properties
obstacle_width = 35  # Slightly wider obstacles
obstacle_height = 160  # Taller obstacles
obstacle_count = 2  # Two obstacles
obstacle_min_y = 100  # Minimum y position
obstacle_max_y = HEIGHT - 100 - obstacle_height  # Maximum y position

# Current level properties (will be set based on level)
center_x = level1_center_x
center_y = level1_center_y
outer_radius = level1_outer_radius
middle_radius = level1_middle_radius
bullseye_radius = level1_bullseye_radius

# Dart properties
dart_x = 150
dart_y = HEIGHT // 2
dart_size = 8  # Increased from 6
dart_angle = 270  # Initial angle to 270 degrees (facing up/north)
angle_min = -30
angle_max = 30
angle_change_speed = 1

# Dart motion properties
dart_speed = 8.8  # Optimized dart speed
dart_in_motion = False
dart_pos_x = dart_x
dart_pos_y = dart_y

# Store previous throws' trajectories
previous_trajectories = []  # Each element is (angle, hit_x, hit_y, hit_center_y)

# Button properties
throw_button = pygame.Rect(50, HEIGHT - 80, 120, 50)

# Clock for controlling frame rate
clock = pygame.time.Clock()
FPS = 60

# Obstacle list
obstacles = []
# Basic drawing functions
def draw_rounded_rect(surface, color, rect, radius=15):
    """Draw a rounded rectangle"""
    rect = pygame.Rect(rect)
    color = pygame.Color(*color)
    alpha = color.a
    color.a = 0
    pos = rect.topleft
    rect.topleft = 0, 0
    rectangle = pygame.Surface(rect.size, pygame.SRCALPHA)

    circle = pygame.Surface([min(rect.size) * 3] * 2, pygame.SRCALPHA)
    pygame.draw.ellipse(circle, (0, 0, 0), circle.get_rect(), 0)
    circle = pygame.transform.smoothscale(circle, [int(min(rect.size) * radius * 2)] * 2)

    radius = rectangle.blit(circle, (0, 0))
    radius.bottomright = rect.bottomright
    rectangle.blit(circle, radius)
    radius.topright = rect.topright
    rectangle.blit(circle, radius)
    radius.bottomleft = rect.bottomleft
    rectangle.blit(circle, radius)

    rectangle.fill((0, 0, 0), rect.inflate(-radius.w, 0))
    rectangle.fill((0, 0, 0), rect.inflate(0, -radius.h))

    rectangle.fill(color, special_flags=pygame.BLEND_RGBA_MAX)
    rectangle.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MIN)

    surface.blit(rectangle, pos)

def draw_hit_effect(hit_x, hit_y, points):
    """Draw a more visible visual effect when the dart hits the dartboard"""
    effect_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    
    if points == 50:
        # Bullseye hit - bright white/yellow flash
        color = (255, 255, 200, 220)
        max_radius = 50
        rings = 8
    elif points == 30:
        # Middle ring hit - cyan flash
        color = (100, 255, 255, 200)
        max_radius = 40
        rings = 6
    elif points == 10:
        # Outer ring hit - orange flash
        color = (255, 180, 100, 180)
        max_radius = 30
        rings = 5
    else:
        # Miss or obstacle hit - red flash
        color = (255, 80, 80, 180)
        max_radius = 25
        rings = 4
    
    # Draw multiple rings for a more dramatic effect
    for i in range(rings):
        r = max_radius * (1 - i/rings)
        ring_width = max(2, int(r/5))
        alpha = int(200 * (1 - i/rings))
        pygame.draw.circle(effect_surface, (color[0], color[1], color[2], alpha), 
                          (int(hit_x), int(hit_y)), int(r), ring_width)
    
    # Add a bright center flash
    center_radius = max_radius // 4
    pygame.draw.circle(effect_surface, (255, 255, 255, 200), 
                      (int(hit_x), int(hit_y)), center_radius)
    
    return effect_surface

def draw_score_popup(hit_x, hit_y, points):
    """Draw a more visible score popup at the hit location"""
    if points > 0:
        # Create a larger, more visible font
        font = pygame.font.SysFont(None, 48)
        
        # Choose color based on points
        if points == 50:
            color = (255, 255, 150)  # Bright yellow for bullseye
            outline_color = (200, 100, 0)
        elif points == 30:
            color = (150, 255, 255)  # Bright cyan for middle ring
            outline_color = (0, 100, 200)
        else:  # 10 points
            color = (255, 200, 100)  # Orange for outer ring
            outline_color = (200, 100, 0)
        
        # Create the text with a point sign
        text = font.render(f"+{points}", True, color)
        
        # Create a slightly larger text for the outline effect
        outline = font.render(f"+{points}", True, outline_color)
        
        # Position the text above the hit point
        text_rect = text.get_rect(center=(hit_x, hit_y - 40))
        
        # Create a surface that will hold both the outline and the text
        combined_surface = pygame.Surface((text_rect.width + 4, text_rect.height + 4), pygame.SRCALPHA)
        
        # Blit the outline text at slightly offset positions for a shadow effect
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            combined_surface.blit(outline, (dx + 2, dy + 2))
        
        # Blit the main text on top
        combined_surface.blit(text, (2, 2))
        
        return (combined_surface, text_rect)
    return None
# Background and obstacle functions
def draw_background():
    """Draw a dark navy background with subtle gradient"""
    # Create a subtle gradient from darker to slightly lighter navy
    for y in range(0, HEIGHT, 2):
        # Calculate gradient color - slightly lighter at the top
        progress = y / HEIGHT
        r = int(22 + 5 * (1 - progress))
        g = int(26 + 8 * (1 - progress))
        b = int(54 + 15 * (1 - progress))
        color = (r, g, b)
        
        # Draw horizontal line for gradient
        pygame.draw.line(screen, color, (0, y), (WIDTH, y), 2)

def create_obstacles():
    """Create obstacles for level 3"""
    global obstacles
    
    obstacles = []
    
    # Calculate positions for obstacles
    # We want them between the dart and the dartboard
    dart_to_board_distance = center_x - dart_x
    
    # Create two fixed obstacles - one in middle, one near dartboard
    # First obstacle - middle position, moved up by 7px
    x_pos1 = dart_x + dart_to_board_distance * 0.48  # 48% of the way from dart to board
    y_pos1 = HEIGHT // 2 - 17  # Positioned 7px higher
    
    # Second obstacle - near dartboard
    x_pos2 = dart_x + dart_to_board_distance * 0.65  # 65% of the way from dart to board
    y_pos2 = 30  # Positioned with only 30px margin from the top
    
    obstacles.append(pygame.Rect(x_pos1, y_pos1, obstacle_width, obstacle_height))
    obstacles.append(pygame.Rect(x_pos2, y_pos2, obstacle_width, obstacle_height))

def update_obstacles():
    """Update obstacle positions for level 3"""
    # Obstacles are now fixed, so no need to update positions
    pass

def draw_obstacles():
    """Draw obstacles for level 3"""
    if current_level == 3:
        for obstacle in obstacles:
            # Draw obstacle with uniform color
            pygame.draw.rect(screen, (200, 50, 50), obstacle)  # Solid red color
            
            # Draw outline
            pygame.draw.rect(screen, (255, 100, 100), obstacle, 2)

def check_obstacle_collision(x1, y1, x2, y2):
    """Check if a line from (x1,y1) to (x2,y2) intersects with any obstacle"""
    if current_level != 3:
        return False
        
    for obstacle in obstacles:
        # Check if line intersects with obstacle rectangle
        # Using the Cohen-Sutherland line clipping algorithm for better accuracy
        
        # Define rectangle edges
        left = obstacle.x
        right = obstacle.x + obstacle.width
        top = obstacle.y
        bottom = obstacle.y + obstacle.height
        
        # Define region codes
        INSIDE = 0  # 0000
        LEFT = 1    # 0001
        RIGHT = 2   # 0010
        BOTTOM = 4  # 0100
        TOP = 8     # 1000
        
        # Function to compute region code
        def compute_code(x, y):
            code = INSIDE
            if x < left:
                code |= LEFT
            elif x > right:
                code |= RIGHT
            if y < top:
                code |= TOP
            elif y > bottom:
                code |= BOTTOM
            return code
        
        # Compute region codes for the endpoints
        code1 = compute_code(x1, y1)
        code2 = compute_code(x2, y2)
        
        # If both endpoints are outside the same region, line doesn't intersect
        while True:
            # Both endpoints inside the rectangle
            if code1 == 0 and code2 == 0:
                return True
                
            # Line is completely outside the rectangle
            if (code1 & code2) != 0:
                break
                
            # Line may cross the rectangle, compute intersection
            code_out = code1 if code1 != 0 else code2
            
            # Find intersection point
            if code_out & TOP:
                x = x1 + (x2 - x1) * (top - y1) / (y2 - y1)
                y = top
            elif code_out & BOTTOM:
                x = x1 + (x2 - x1) * (bottom - y1) / (y2 - y1)
                y = bottom
            elif code_out & RIGHT:
                y = y1 + (y2 - y1) * (right - x1) / (x2 - x1)
                x = right
            elif code_out & LEFT:
                y = y1 + (y2 - y1) * (left - x1) / (x2 - x1)
                x = left
                
            # Update endpoint and region code
            if code_out == code1:
                x1, y1 = x, y
                code1 = compute_code(x1, y1)
            else:
                x2, y2 = x, y
                code2 = compute_code(x2, y2)
    
    return False
# Timer function for Level 3
def draw_timer():
    """Draw the timer for Level 3"""
    global game_over, level3_start_time
    
    if current_level == 3 and not game_over:
        # Calculate remaining time
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - level3_start_time
        remaining_time = max(0, level3_time_limit - elapsed_time)
        
        # Convert to seconds
        seconds_left = remaining_time // 1000
        
        # Create timer display
        font = pygame.font.SysFont(None, 36)
        
        # Change color based on time remaining
        if seconds_left > 10:
            color = WHITE
        elif seconds_left > 5:
            color = TEXT_HIGHLIGHT
        else:
            color = UI_ACCENT
            
        timer_text = font.render(f"Time: {seconds_left}s", True, color)
        timer_rect = timer_text.get_rect(topright=(WIDTH - 20, 20))
        
        # Draw background for better visibility
        bg_rect = timer_rect.copy()
        bg_rect.inflate_ip(20, 10)
        draw_rounded_rect(screen, (40, 45, 75, 200), bg_rect)
        
        # Draw timer text
        screen.blit(timer_text, timer_rect)
        
        # Check if time is up
        if remaining_time <= 0 and not game_over:
            return True  # Time's up
            
    return False  # Time still remaining or not Level 3
# Drawing functions for game elements
def draw_dart(x, y, angle):
    """Draw the dart at the specified position and angle with increased size"""
    angle_rad = math.radians(angle)
    length = 20  # Increased from 15
    width = 7    # Increased from 5
    
    base_x = x
    base_y = y
    tip_x = x + length * 2 * math.cos(angle_rad)
    tip_y = y + length * 2 * math.sin(angle_rad)
    top_x = x - width * math.sin(angle_rad)
    top_y = y + width * math.cos(angle_rad)
    bottom_x = x + width * math.sin(angle_rad)
    bottom_y = y - width * math.cos(angle_rad)
    mid_top_x = x + length * math.cos(angle_rad) - width/2 * math.sin(angle_rad)
    mid_top_y = y + length * math.sin(angle_rad) + width/2 * math.cos(angle_rad)
    mid_bottom_x = x + length * math.cos(angle_rad) + width/2 * math.sin(angle_rad)
    mid_bottom_y = y + length * math.sin(angle_rad) - width/2 * math.cos(angle_rad)
    
    dart_body_color = (240, 240, 240)  # Changed to white
    pygame.draw.polygon(screen, dart_body_color, [
        (base_x, base_y), (top_x, top_y), (mid_top_x, mid_top_y),
        (tip_x, tip_y), (mid_bottom_x, mid_bottom_y), (bottom_x, bottom_y)
    ])
    
    pygame.draw.polygon(screen, BLACK, [
        (base_x, base_y), (top_x, top_y), (mid_top_x, mid_top_y),
        (tip_x, tip_y), (mid_bottom_x, mid_bottom_y), (bottom_x, bottom_y)
    ], 1)
    
    fin_length = width * 1.2
    pygame.draw.polygon(screen, UI_ACCENT, [  # Changed to UI_ACCENT (coral red)
        (base_x, base_y), 
        (base_x - fin_length * math.cos(angle_rad), base_y - fin_length * math.sin(angle_rad)),
        (top_x, top_y)
    ])
    pygame.draw.polygon(screen, UI_ACCENT, [  # Changed to UI_ACCENT (coral red)
        (base_x, base_y), 
        (base_x - fin_length * math.cos(angle_rad), base_y - fin_length * math.sin(angle_rad)),
        (bottom_x, bottom_y)
    ])

def draw_dartboard():
    """Draw the dartboard with 3 concentric circles"""
    pygame.draw.circle(screen, DARTBOARD_OUTER, (center_x, center_y), outer_radius)
    pygame.draw.circle(screen, BLACK, (center_x, center_y), outer_radius, 2)
    pygame.draw.circle(screen, DARTBOARD_MIDDLE, (center_x, center_y), middle_radius)
    pygame.draw.circle(screen, BLACK, (center_x, center_y), middle_radius, 2)
    pygame.draw.circle(screen, DARTBOARD_CENTER, (center_x, center_y), bullseye_radius)
    pygame.draw.circle(screen, BLACK, (center_x, center_y), bullseye_radius, 2)
    
    font = pygame.font.SysFont(None, 24)
    # Position the 10 text in the larger outer ring
    outer_text = font.render("10", True, BLACK)
    outer_rect = outer_text.get_rect(center=(center_x - (middle_radius + outer_radius) // 2, center_y))
    screen.blit(outer_text, outer_rect)
    
    # Position the 30 text in the smaller middle ring
    middle_text = font.render("30", True, BLACK)
    middle_rect = middle_text.get_rect(center=(center_x - (bullseye_radius + middle_radius) // 2, center_y))
    screen.blit(middle_text, middle_rect)
    
    bullseye_text = font.render("50", True, WHITE)
    bullseye_rect = bullseye_text.get_rect(center=(center_x, center_y))
    screen.blit(bullseye_text, bullseye_rect)

def draw_previous_trajectories():
    """Draw trajectories of previous throws with moderately bold lines"""
    # Don't draw trajectories in Level 3
    if current_level == 3:
        return
        
    for i, (angle, hit_x, hit_y, hit_center_y) in enumerate(previous_trajectories):
        # Calculate points along the trajectory
        start_x = dart_x
        start_y = dart_y
        
        # For level 2, adjust the hit position based on dartboard movement
        if current_level == 2:
            # Calculate the vertical offset from the original hit position
            y_offset = center_y - hit_center_y
            end_x = hit_x
            end_y = hit_y + y_offset
        else:
            end_x = hit_x
            end_y = hit_y
        
        # Draw a moderately bold line for the trajectory
        line_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        
        # Use a brighter white with medium opacity
        color = (255, 255, 255, 140)  # Adjusted opacity
        
        # Draw a medium thickness line (2 pixels instead of 3)
        pygame.draw.line(line_surface, color, (start_x, start_y), (end_x, end_y), 2)
        screen.blit(line_surface, (0, 0))
        
        # Draw a medium circle at the hit point
        pygame.draw.circle(line_surface, (255, 255, 255, 180), (int(end_x), int(end_y)), 4)  # Adjusted size
        screen.blit(line_surface, (0, 0))

def draw_score_box():
    """Draw the score box with rounded corners"""
    # Create a larger box to accommodate both score and throws
    box_rect = pygame.Rect(20, 20, 180, 120)
    draw_rounded_rect(screen, (40, 45, 75, 200), box_rect)
    
    font = pygame.font.SysFont(None, 28)
    
    # Level indicator
    level_text = font.render(f"Level {current_level}", True, TEXT_HIGHLIGHT)
    screen.blit(level_text, (box_rect.x + 15, box_rect.y + 15))
    
    # Score below level
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (box_rect.x + 15, box_rect.y + 45))
    
    # Level goal
    if current_level == 1:
        goal_text = font.render("Goal: 70 pts", True, BUTTON_GREEN)
        screen.blit(goal_text, (box_rect.x + 15, box_rect.y + 75))
    elif current_level == 2:
        goal_text = font.render("Goal: 60 pts", True, BUTTON_GREEN)
        screen.blit(goal_text, (box_rect.x + 15, box_rect.y + 75))
    
    # Throws text below score
    throws_text = font.render("Throws:", True, WHITE)
    screen.blit(throws_text, (box_rect.x + 15, box_rect.y + 75 if current_level == 3 else box_rect.y + 95))
    
    # Throw indicators (circles) properly aligned with the text
    throw_y = box_rect.y + 85 if current_level == 3 else box_rect.y + 105
    for i in range(3):
        color = UI_ACCENT if i < throws_left else (80, 85, 120)
        pygame.draw.circle(screen, color, (box_rect.x + 110 + i * 25, throw_y), 8)

def draw_throw_button():
    """Draw the THROW button"""
    mouse_pos = pygame.mouse.get_pos()
    button_color = BUTTON_HOVER if throw_button.collidepoint(mouse_pos) else BUTTON_GREEN
    
    draw_rounded_rect(screen, button_color, throw_button)
    
    font = pygame.font.SysFont(None, 32)  # Slightly larger font
    text = font.render("THROW", True, WHITE)  # Changed from BLACK to WHITE
    text_rect = text.get_rect(center=throw_button.center)
    screen.blit(text, text_rect)

def draw_helper_text():
    """Draw helper text with better styling"""
    global show_helper, helper_timer
    
    if show_helper and helper_timer > 0:
        # Create a semi-transparent rounded rectangle for the helper text
        helper_rect = pygame.Rect(WIDTH//2 - 210, 80, 420, 100)
        draw_rounded_rect(screen, (20, 20, 40, 180), helper_rect)
        
        helper_font = pygame.font.SysFont(None, 28)
        title_font = pygame.font.SysFont(None, 32)
        
        # Title and instructions based on current level
        if current_level == 1:
            title_text = title_font.render("CONTROLS", True, (255, 220, 100))
            screen.blit(title_text, (WIDTH//2 - 50, 90))
            
            helper_text1 = helper_font.render("Use UP/DOWN arrows to aim", True, WHITE)
            helper_text2 = helper_font.render("Press SPACE or click THROW to throw the dart", True, WHITE)
            
            screen.blit(helper_text1, (WIDTH//2 - 140, 125))
            screen.blit(helper_text2, (WIDTH//2 - 190, 155))
        elif current_level == 2:
            title_text = title_font.render("MOVING TARGET", True, (255, 220, 100))
            screen.blit(title_text, (WIDTH//2 - 80, 90))
            
            helper_text1 = helper_font.render("Time your throw carefully!", True, WHITE)
            helper_text2 = helper_font.render("The dartboard is moving up and down", True, WHITE)
            
            screen.blit(helper_text1, (WIDTH//2 - 140, 125))
            screen.blit(helper_text2, (WIDTH//2 - 190, 155))
        else:  # Level 3
            title_text = title_font.render("OBSTACLES & TIMER", True, (255, 220, 100))
            screen.blit(title_text, (WIDTH//2 - 90, 90))
            
            helper_text1 = helper_font.render("Wait for dartboard to move to the BOTTOM!", True, WHITE)
            helper_text2 = helper_font.render("You have only 20 seconds - hurry!", True, WHITE)
            
            screen.blit(helper_text1, (WIDTH//2 - 190, 125))
            screen.blit(helper_text2, (WIDTH//2 - 160, 155))
        
        helper_timer -= 1
# Game screens
def draw_start_screen():
    """Draw the start screen with game instructions"""
    # Create a panel for the title
    title_panel = pygame.Rect(WIDTH//2 - 300, 50, 600, 100)
    draw_rounded_rect(screen, (40, 40, 60, 230), title_panel)
    
    # Game title
    title_font = pygame.font.SysFont(None, 64)
    title_text = title_font.render(f"DART GAME - LEVEL {current_level}", True, (255, 220, 100))
    title_rect = title_text.get_rect(center=(WIDTH//2, 100))
    screen.blit(title_text, title_rect)
    
    # Instructions panel
    instructions_panel = pygame.Rect(WIDTH//2 - 300, 170, 600, 300)
    draw_rounded_rect(screen, (30, 30, 50, 230), instructions_panel)
    
    # Instructions header
    header_font = pygame.font.SysFont(None, 36)
    header_text = header_font.render("HOW TO PLAY", True, WHITE)
    header_rect = header_text.get_rect(center=(WIDTH//2, 200))
    screen.blit(header_text, header_rect)
    
    # Instructions text
    inst_font = pygame.font.SysFont(None, 28)
    
    if current_level == 1:
        instructions = [
            "1. Use UP/DOWN arrow keys to aim the dart",
            "2. Press SPACE or click the THROW button to throw",
            "3. Hit the bullseye (red center) for 50 points",
            "4. Hit the middle ring (cyan) for 30 points",
            "5. Hit the outer ring (amber) for 10 points",
            "6. You have 3 throws per game",
            "",
            "Score at least 70 points to unlock Level 2!"
        ]
    elif current_level == 2:
        instructions = [
            "Welcome to Level 2!",
            "",
            "The dartboard now moves up and down.",
            "This makes hitting the target more challenging.",
            "",
            "Same controls as before:",
            "- UP/DOWN arrows to aim",
            "- SPACE or THROW button to throw",
            "",
            "Score at least 60 points to unlock Level 3!"
        ]
    else:  # Level 3
        instructions = [
            "Welcome to Level 3!",
            "",
            "BEWARE OF OBSTACLES!",
            "Red blocks will block your dart's path.",
            "If your dart hits a block, it will be wasted!",
            "",
            "TIP: Wait for the dartboard to move to the BOTTOM",
            "to find a clear path between the obstacles.",
            "",
            "You have only 20 SECONDS to complete this level!",
            "Use your 3 throws wisely."
        ]
    
    for i, line in enumerate(instructions):
        text = inst_font.render(line, True, WHITE)
        screen.blit(text, (WIDTH//2 - 250, 240 + i * 32))
    
    # Start button
    start_button = pygame.Rect(WIDTH//2 - 100, 490, 200, 60)
    mouse_pos = pygame.mouse.get_pos()
    button_color = (60, 180, 80) if start_button.collidepoint(mouse_pos) else (50, 150, 70)
    draw_rounded_rect(screen, button_color, start_button)
    
    start_font = pygame.font.SysFont(None, 36)
    start_text = start_font.render("START GAME", True, WHITE)
    start_rect = start_text.get_rect(center=start_button.center)
    screen.blit(start_text, start_rect)
    
    return start_button
def draw_game_over():
    """Draw game over message with level progression options"""
    if game_over:
        # For level 3 completion, show celebration screen
        if current_level == 3:
            return draw_celebration_screen()
            
        # For levels 1 and 2, show the regular game over screen
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Larger panel with better styling
        panel_rect = pygame.Rect(WIDTH//2 - 180, HEIGHT//2 - 150, 360, 300)
        draw_rounded_rect(screen, (40, 40, 60, 230), panel_rect)
        
        # Add a decorative header
        header_rect = pygame.Rect(WIDTH//2 - 180, HEIGHT//2 - 150, 360, 60)
        draw_rounded_rect(screen, (80, 20, 20, 230), header_rect)
        
        font = pygame.font.SysFont(None, 64)
        game_over_text = font.render("LEVEL COMPLETE", True, WHITE)
        text_rect = game_over_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 110))
        screen.blit(game_over_text, text_rect)
        
        score_font = pygame.font.SysFont(None, 48)
        final_score_text = score_font.render(f"Final Score: {score}", True, WHITE)
        score_rect = final_score_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 40))
        screen.blit(final_score_text, score_rect)
        
        # Different options based on score and current level
        message_font = pygame.font.SysFont(None, 32)
        buttons = []
        
        if current_level == 1 and score >= 70:
            # Player cleared level 1 with enough points
            message_text = message_font.render("You've unlocked Level 2!", True, (150, 255, 150))
            message_rect = message_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 10))
            screen.blit(message_text, message_rect)
            
            # Next level button
            next_button = pygame.Rect(WIDTH//2 - 90, HEIGHT//2 + 50, 180, 60)
            mouse_pos = pygame.mouse.get_pos()
            button_color = (60, 180, 80) if next_button.collidepoint(mouse_pos) else (50, 150, 70)
            draw_rounded_rect(screen, button_color, next_button)
            
            next_text = pygame.font.SysFont(None, 36).render("Next Level", True, WHITE)
            next_rect = next_text.get_rect(center=next_button.center)
            screen.blit(next_text, next_rect)
            buttons.append(("next_level", next_button))
            
            # Restart button (smaller and below)
            restart_button = pygame.Rect(WIDTH//2 - 90, HEIGHT//2 + 120, 180, 40)
            button_color = (100, 100, 100) if restart_button.collidepoint(mouse_pos) else (80, 80, 80)
            draw_rounded_rect(screen, button_color, restart_button)
            
            restart_text = pygame.font.SysFont(None, 28).render("Restart Level 1", True, WHITE)
            restart_rect = restart_text.get_rect(center=restart_button.center)
            screen.blit(restart_text, restart_rect)
            buttons.append(("restart", restart_button))
            
        elif current_level == 1 and score < 70:
            # Player didn't score enough to unlock level 2
            message_text = message_font.render("Score 70+ to unlock Level 2", True, (255, 150, 150))
            message_rect = message_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 10))
            screen.blit(message_text, message_rect)
            
            # Restart button
            restart_button = pygame.Rect(WIDTH//2 - 90, HEIGHT//2 + 70, 180, 60)
            mouse_pos = pygame.mouse.get_pos()
            button_color = (60, 180, 80) if restart_button.collidepoint(mouse_pos) else (50, 150, 70)
            draw_rounded_rect(screen, button_color, restart_button)
            
            restart_text = pygame.font.SysFont(None, 36).render("Try Again", True, WHITE)
            restart_rect = restart_text.get_rect(center=restart_button.center)
            screen.blit(restart_text, restart_rect)
            buttons.append(("restart", restart_button))
            
            # Quit button
            quit_button = pygame.Rect(WIDTH//2 - 90, HEIGHT//2 + 140, 180, 40)
            button_color = (180, 60, 60) if quit_button.collidepoint(mouse_pos) else (150, 50, 50)
            draw_rounded_rect(screen, button_color, quit_button)
            
            quit_text = pygame.font.SysFont(None, 28).render("Quit Game", True, WHITE)
            quit_rect = quit_text.get_rect(center=quit_button.center)
            screen.blit(quit_text, quit_rect)
            buttons.append(("quit", quit_button))
            
        elif current_level == 2 and score >= 60:
            # Player cleared level 2 with enough points
            message_text = message_font.render("You've unlocked Level 3!", True, (150, 255, 150))
            message_rect = message_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 10))
            screen.blit(message_text, message_rect)
            
            # Next level button
            next_button = pygame.Rect(WIDTH//2 - 90, HEIGHT//2 + 50, 180, 60)
            mouse_pos = pygame.mouse.get_pos()
            button_color = (60, 180, 80) if next_button.collidepoint(mouse_pos) else (50, 150, 70)
            draw_rounded_rect(screen, button_color, next_button)
            
            next_text = pygame.font.SysFont(None, 36).render("Next Level", True, WHITE)
            next_rect = next_text.get_rect(center=next_button.center)
            screen.blit(next_text, next_rect)
            buttons.append(("next_level", next_button))
            
            # Restart button (smaller and below)
            restart_button = pygame.Rect(WIDTH//2 - 90, HEIGHT//2 + 120, 180, 40)
            button_color = (100, 100, 100) if restart_button.collidepoint(mouse_pos) else (80, 80, 80)
            draw_rounded_rect(screen, button_color, restart_button)
            
            restart_text = pygame.font.SysFont(None, 28).render("Restart Level 2", True, WHITE)
            restart_rect = restart_text.get_rect(center=restart_button.center)
            screen.blit(restart_text, restart_rect)
            buttons.append(("restart", restart_button))
            
        elif current_level == 2 and score < 60:
            # Player didn't score enough to unlock level 3
            message_text = message_font.render("Score 60+ to unlock Level 3", True, (255, 150, 150))
            message_rect = message_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 10))
            screen.blit(message_text, message_rect)
            
            # Restart button
            restart_button = pygame.Rect(WIDTH//2 - 90, HEIGHT//2 + 70, 180, 60)
            mouse_pos = pygame.mouse.get_pos()
            button_color = (60, 180, 80) if restart_button.collidepoint(mouse_pos) else (50, 150, 70)
            draw_rounded_rect(screen, button_color, restart_button)
            
            restart_text = pygame.font.SysFont(None, 36).render("Try Again", True, WHITE)
            restart_rect = restart_text.get_rect(center=restart_button.center)
            screen.blit(restart_text, restart_rect)
            buttons.append(("restart", restart_button))
            
            # Previous level button
            prev_button = pygame.Rect(WIDTH//2 - 90, HEIGHT//2 + 140, 180, 40)
            button_color = (100, 100, 180) if prev_button.collidepoint(mouse_pos) else (80, 80, 150)
            draw_rounded_rect(screen, button_color, prev_button)
            
            prev_text = pygame.font.SysFont(None, 28).render("Back to Level 1", True, WHITE)
            prev_rect = prev_text.get_rect(center=prev_button.center)
            screen.blit(prev_text, prev_rect)
            buttons.append(("prev_level", prev_button))
        
        return buttons
    return []
def draw_celebration_screen():
    """Draw a celebration screen with simple gradient background when level 3 is completed"""
    global celebration_active, celebration_start_time
    
    if not celebration_active:
        return False
    
    # Create a simple gradient background
    gradient_surface = pygame.Surface((WIDTH, HEIGHT))
    
    # Draw simple gradient rectangles
    rect_height = HEIGHT // 10
    for i in range(10):
        # Simple blue gradient from dark to slightly lighter
        color_value = 20 + (i * 10)  # Simple gradient from dark to slightly lighter blue
        color = (0, 0, color_value)
        
        rect = pygame.Rect(0, i * rect_height, WIDTH, rect_height)
        pygame.draw.rect(gradient_surface, color, rect)
    
    # Apply a dark overlay to make text more readable
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 100))  # Semi-transparent black
    gradient_surface.blit(overlay, (0, 0))
    
    screen.blit(gradient_surface, (0, 0))
    
    # Draw congratulatory text
    title_font = pygame.font.SysFont(None, 72)
    title_text = title_font.render("CONGRATULATIONS!", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 100))
    screen.blit(title_text, title_rect)
    
    # Draw final score
    score_font = pygame.font.SysFont(None, 64)
    score_text = score_font.render(f"Final Score: {score}", True, (220, 220, 255))
    score_rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2))
    screen.blit(score_text, score_rect)
    
    # Draw level completion message
    message_font = pygame.font.SysFont(None, 36)
    message_text = message_font.render("You've completed all levels!", True, (150, 255, 150))
    message_rect = message_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 80))
    screen.blit(message_text, message_rect)
    
    # Draw buttons
    buttons = []
    
    # Play again button
    restart_button = pygame.Rect(WIDTH//2 - 90, HEIGHT//2 + 150, 180, 60)
    mouse_pos = pygame.mouse.get_pos()
    button_color = (60, 180, 80) if restart_button.collidepoint(mouse_pos) else (50, 150, 70)
    draw_rounded_rect(screen, button_color, restart_button)
    
    restart_text = pygame.font.SysFont(None, 36).render("Play Again", True, WHITE)
    restart_rect = restart_text.get_rect(center=restart_button.center)
    screen.blit(restart_text, restart_rect)
    buttons.append(("restart_all", restart_button))
    
    # Quit button
    quit_button = pygame.Rect(WIDTH//2 - 90, HEIGHT//2 + 220, 180, 40)
    button_color = (180, 60, 60) if quit_button.collidepoint(mouse_pos) else (150, 50, 50)
    draw_rounded_rect(screen, button_color, quit_button)
    
    quit_text = pygame.font.SysFont(None, 28).render("Quit Game", True, WHITE)
    quit_rect = quit_text.get_rect(center=quit_button.center)
    screen.blit(quit_text, quit_rect)
    buttons.append(("quit", quit_button))
    
    return buttons
# Game mechanics functions
def update_dartboard_position():
    """Update the dartboard position for level 2 and 3"""
    global center_y, level2_move_direction
    
    if current_level >= 2:  # For both level 2 and 3
        # Move the dartboard up or down
        center_y += level2_move_speed * level2_move_direction
        
        # Reverse direction if reaching the boundaries
        if center_y <= level2_y_min:
            center_y = level2_y_min
            level2_move_direction = 1  # Start moving down
        elif center_y >= level2_y_max:
            center_y = level2_y_max
            level2_move_direction = -1  # Start moving up

def calculate_perfect_angle():
    """Calculate the perfect angle to hit the bullseye"""
    dx = center_x - dart_x
    dy = center_y - dart_y
    return math.degrees(math.atan2(dy, dx))

def throw_dart():
    """Initialize dart throwing"""
    global dart_in_motion, dart_pos_x, dart_pos_y, throws_left
    
    if not dart_in_motion and not game_over and throws_left > 0:
        dart_in_motion = True
        dart_pos_x = dart_x
        dart_pos_y = dart_y
        throws_left -= 1

def reset_dart():
    """Reset the dart to its starting position"""
    global dart_in_motion, dart_pos_x, dart_pos_y
    dart_in_motion = False
    dart_pos_x = dart_x
    dart_pos_y = dart_y

def check_game_over():
    """Check if the game is over"""
    global game_over, level3_start_time
    
    # Game is over if no throws left
    if throws_left <= 0:
        game_over = True
        return True
        
    # For Level 3, also check if time is up
    if current_level == 3 and level3_start_time > 0:
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - level3_start_time
        if elapsed_time >= level3_time_limit:
            game_over = True
            return True
            
    return game_over

def reset_game(level=1):
    """Reset the game to initial state"""
    global throws_left, score, game_over, dart_angle, dart_in_motion, previous_trajectories
    global show_helper, helper_timer, current_level, center_x, center_y, level2_move_direction
    global obstacles, level3_start_time, level3_time_remaining
    
    throws_left = 3
    score = 0
    game_over = False
    dart_angle = 270  # Keep facing up initially
    dart_in_motion = False
    previous_trajectories = []  # Clear previous trajectories
    show_helper = False
    helper_timer = 0
    
    # Set the level
    current_level = level
    
    # Set level-specific properties
    if current_level == 1:
        center_x = level1_center_x
        center_y = level1_center_y
        obstacles = []  # No obstacles in level 1
    elif current_level == 2:
        center_x = level2_center_x
        center_y = level2_center_y
        level2_move_direction = 1
        obstacles = []  # No obstacles in level 2
    elif current_level == 3:
        center_x = level3_center_x
        center_y = level3_center_y
        level2_move_direction = 1
        
        # Reset Level 3 timer
        level3_start_time = 0  # Will be set when game starts
        level3_time_remaining = level3_time_limit
        
        # Create obstacles for level 3
        create_obstacles()
    
    reset_dart()
# Main game loop
def main():
    """Main game loop"""
    global dart_angle, dart_in_motion, dart_pos_x, dart_pos_y, score, throws_left, game_over, previous_trajectories
    global show_helper, helper_timer, game_started, center_y, celebration_active, celebration_start_time
    global level3_start_time, level3_time_remaining
    
    running = True
    
    perfect_angle = calculate_perfect_angle()
    dart_angle = 270  # Start with dart facing up
    
    hit_effect = None
    hit_effect_timer = 0
    score_popup = None
    score_popup_timer = 0
    
    # Reset helper variables
    show_helper = False  # Disable initial instructions
    helper_timer = 0
    game_started = False  # Game starts with the start screen
    celebration_active = False
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    if not game_started:
                        game_started = True
                    elif not dart_in_motion and not game_over and not celebration_active:
                        throw_dart()
                        show_helper = False
                elif event.key == pygame.K_r and game_over and not celebration_active:
                    reset_game(current_level)
                    hit_effect = None
                    score_popup = None
                elif event.key == pygame.K_p and not celebration_active:
                    dart_angle = perfect_angle
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if not game_started:
                        # Check if start button was clicked
                        start_button = pygame.Rect(WIDTH//2 - 100, 490, 200, 60)
                        if start_button.collidepoint(event.pos):
                            game_started = True
                    elif not dart_in_motion and not game_over and throw_button.collidepoint(event.pos) and not celebration_active:
                        throw_dart()
                        show_helper = False
                    
                    if game_over:
                        if celebration_active:
                            buttons = draw_celebration_screen()
                        else:
                            buttons = draw_game_over()
                            
                        for action, button in buttons:
                            if button.collidepoint(event.pos):
                                if action == "next_level":
                                    # Move to next level
                                    reset_game(current_level + 1)
                                    hit_effect = None
                                    score_popup = None
                                    celebration_active = False
                                    show_helper = False  # Disable helper for new level
                                    helper_timer = 0
                                elif action == "restart":
                                    # Restart current level
                                    reset_game(current_level)
                                    hit_effect = None
                                    score_popup = None
                                    celebration_active = False
                                elif action == "restart_all":
                                    # Restart from level 1
                                    reset_game(1)
                                    hit_effect = None
                                    score_popup = None
                                    celebration_active = False
                                elif action == "prev_level":
                                    # Go back to previous level
                                    reset_game(current_level - 1)
                                    hit_effect = None
                                    score_popup = None
                                    celebration_active = False
                                elif action == "quit":
                                    running = False
        
        # If we're on the start screen, draw it and continue to next frame
        if not game_started:
            screen.fill(BACKGROUND)
            draw_background()
            draw_start_screen()
            pygame.display.flip()
            clock.tick(FPS)
            continue
            
        # If celebration is active, only draw celebration screen
        if celebration_active:
            draw_celebration_screen()
            pygame.display.flip()
            clock.tick(FPS)
            continue
            
        # For Level 3, start the timer when game starts
        if current_level == 3 and level3_start_time == 0:
            level3_start_time = pygame.time.get_ticks()
        
        # Update dartboard position for level 2 and 3
        if current_level >= 2:
            update_dartboard_position()
        
        # Update obstacles for level 3
        if current_level == 3:
            update_obstacles()
        
        # Recalculate perfect angle as dartboard may move
        perfect_angle = calculate_perfect_angle()
        
        if not dart_in_motion and not game_over:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP]:
                dart_angle = max(perfect_angle + angle_min, dart_angle - angle_change_speed)
                show_helper = False
            if keys[pygame.K_DOWN]:
                dart_angle = min(perfect_angle + angle_max, dart_angle + angle_change_speed)
                show_helper = False
        
        if dart_in_motion:
            prev_x, prev_y = dart_pos_x, dart_pos_y
            
            # Normal dart movement for all levels (no wind)
            dart_pos_x += dart_speed * math.cos(math.radians(dart_angle))
            dart_pos_y += dart_speed * math.sin(math.radians(dart_angle))
            
            # Check for obstacle collision in Level 3
            if current_level == 3 and check_obstacle_collision(prev_x, prev_y, dart_pos_x, dart_pos_y):
                # Dart hit an obstacle - create a hit effect at collision point
                hit_effect = draw_hit_effect(dart_pos_x, dart_pos_y, 0)  # 0 points = red effect
                hit_effect_timer = 15  # Reduced from 30 to make the effect briefer
                
                # Reset dart
                reset_dart()
                
                # Check if all throws are used, if so, show game over screen
                if check_game_over() and current_level == 3:
                    celebration_active = True
                    celebration_start_time = pygame.time.get_ticks()
                continue
            
            if dart_pos_x > WIDTH or dart_pos_y < 0 or dart_pos_y > HEIGHT:
                reset_dart()
                
                # Check if all throws are used, if so, show game over screen
                if check_game_over() and current_level == 3:
                    celebration_active = True
                    celebration_start_time = pygame.time.get_ticks()
            
            elif (prev_x < center_x and dart_pos_x >= center_x) or (prev_x > center_x and dart_pos_x <= center_x):
                if dart_pos_x != prev_x:
                    m = (dart_pos_y - prev_y) / (dart_pos_x - prev_x)
                    b = prev_y - m * prev_x
                    intersect_y = m * center_x + b
                else:
                    intersect_y = dart_pos_y
                
                distance = abs(intersect_y - center_y)
                
                points_earned = 0
                if distance <= outer_radius:
                    if distance <= bullseye_radius:
                        points_earned = 50
                    elif distance <= middle_radius:
                        points_earned = 30
                    else:
                        points_earned = 10
                    
                    score += points_earned
                    
                    # Store this throw's trajectory
                    # For level 2 and 3, also store the center_y position at the time of hit
                    previous_trajectories.append((dart_angle, center_x, intersect_y, center_y))
                    
                    hit_effect = draw_hit_effect(center_x, intersect_y, points_earned)
                    hit_effect_timer = 15  # Reduced from 30 to make the effect briefer
                    
                    if points_earned > 0:
                        score_popup = draw_score_popup(center_x, intersect_y, points_earned)
                        score_popup_timer = 60
                
                reset_dart()
                
                # Check if all throws are used, if so, show game over screen
                if check_game_over() and current_level == 3:
                    celebration_active = True
                    celebration_start_time = pygame.time.get_ticks()
        
        screen.fill(BACKGROUND)
        draw_background()
        
        draw_dartboard()
        
        # Draw obstacles for level 3
        if current_level == 3:
            draw_obstacles()
        
        # Draw previous trajectories (if any)
        if previous_trajectories:
            draw_previous_trajectories()
        
        if dart_in_motion:
            draw_dart(dart_pos_x, dart_pos_y, dart_angle)
        else:
            draw_dart(dart_x, dart_y, dart_angle)
        
        if hit_effect and hit_effect_timer > 0:
            screen.blit(hit_effect, (0, 0))
            hit_effect_timer -= 1
            
            # Add a screen flash effect when hit effect is active
            if hit_effect_timer > 12:  # Only during the first few frames (adjusted for shorter duration)
                flash_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                flash_alpha = int(40 * (hit_effect_timer - 12) / 3)  # Fade quickly, reduced intensity
                flash_surface.fill((255, 255, 255, flash_alpha))
                screen.blit(flash_surface, (0, 0))
        
        if score_popup and score_popup_timer > 0:
            text, rect = score_popup
            # Make the popup move upward and bounce slightly
            if score_popup_timer > 45:
                rect.y -= 2  # Move up faster initially
            elif score_popup_timer > 30:
                rect.y -= 1  # Slow down
            elif score_popup_timer > 15:
                rect.y -= 0.5  # Even slower
                
            # Add a slight horizontal bounce
            bounce_offset = math.sin(score_popup_timer * 0.2) * 3
            display_rect = rect.copy()
            display_rect.x += bounce_offset
            
            # Scale the popup for a "pop" effect
            scale = 1.0
            if score_popup_timer > 50:
                scale = 0.7 + 0.3 * ((score_popup_timer - 50) / 10)  # Grow in
            elif score_popup_timer < 15:
                scale = 0.7 + 0.3 * (score_popup_timer / 15)  # Shrink out
                
            if scale != 1.0:
                w, h = text.get_width(), text.get_height()
                scaled_text = pygame.transform.smoothscale(
                    text, 
                    (int(w * scale), int(h * scale))
                )
                # Recenter after scaling
                display_rect.x += (w - scaled_text.get_width()) // 2
                display_rect.y += (h - scaled_text.get_height()) // 2
                screen.blit(scaled_text, display_rect)
            else:
                screen.blit(text, display_rect)
                
            score_popup_timer -= 1
        
        draw_score_box()
        draw_throw_button()
        
        # Call the helper text function
        draw_helper_text()
        
        # Draw timer for Level 3
        if current_level == 3:
            if draw_timer() and not game_over:
                game_over = True
        
        # Draw game over screen if game is over
        if game_over:
            draw_game_over()
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
