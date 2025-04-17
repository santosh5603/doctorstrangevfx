import cv2
import mediapipe as mp
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
import pygame
from pygame.locals import *
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Mediapipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Initialize Pygame and OpenGL
pygame.init()
display = (1280, 720)
pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
glTranslatef(0.0, 0.0, -5)

# Video Capture
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, display[0])
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, display[1])

# Effect parameters
particles = []
texture_id = None
last_finger_positions = {}

def init_gl():
    global texture_id
    try:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # Additive blending for glow
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_TEXTURE_2D)
        glPointSize(15.0)
        glLineWidth(4.0)  # Increased for bolder lines
        texture_id = glGenTextures(1)
        logging.info("OpenGL initialized successfully")
    except Exception as e:
        logging.error(f"OpenGL initialization failed: {e}")

def load_video_texture(frame):
    try:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = np.flipud(frame)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, frame.shape[1], frame.shape[0], 
                    0, GL_RGB, GL_UNSIGNED_BYTE, frame)
    except Exception as e:
        logging.error(f"Texture loading failed: {e}")

def draw_background():
    try:
        glDisable(GL_BLEND)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-3.5, -2.5, -1)
        glTexCoord2f(1, 0); glVertex3f(3.5, -2.5, -1)
        glTexCoord2f(1, 1); glVertex3f(3.5, 2.5, -1)
        glTexCoord2f(0, 1); glVertex3f(-3.5, 2.5, -1)
        glEnd()
        glEnable(GL_BLEND)
    except Exception as e:
        logging.error(f"Background drawing failed: {e}")

def add_particle(x, y, z):
    particles.append({
        'pos': [x, y, z],
        'vel': [np.random.uniform(-0.01, 0.01), 
                np.random.uniform(-0.01, 0.01), 
                0],
        'life': 1.0,
        'initial_size': np.random.uniform(10.0, 20.0)
    })

def draw_small_circle(x, y, z, radius=0.1, time=0):
    try:
        glPushMatrix()
        glTranslatef(x, y, z)
        glRotatef(time * 60, 0, 0, 1)
        
        # Extra glow layer for shininess
        glLineWidth(6.0)  # Thicker for glow
        glBegin(GL_LINE_LOOP)
        glColor4f(1.0, 0.843, 0.0, 0.4)  # Brighter, more transparent glow
        for i in range(360):
            angle = np.radians(i)
            glVertex3f(np.cos(angle) * (radius + 0.06), 
                      np.sin(angle) * (radius + 0.06), 0)
        glEnd()
        
        # Outer glow
        glLineWidth(4.0)
        glBegin(GL_LINE_LOOP)
        glColor4f(1.0, 0.843, 0.0, 0.7)
        for i in range(360):
            angle = np.radians(i)
            glVertex3f(np.cos(angle) * (radius + 0.03), 
                      np.sin(angle) * (radius + 0.03), 0)
        glEnd()
        
        # Main circle
        glLineWidth(4.0)  # Bolder main line
        glBegin(GL_LINE_LOOP)
        glColor4f(1.0, 0.843, 0.0, 1.0)
        for i in range(360):
            angle = np.radians(i)
            glVertex3f(np.cos(angle) * radius, 
                      np.sin(angle) * radius, 0)
        glEnd()
        glPopMatrix()
    except Exception as e:
        logging.error(f"Small circle drawing failed: {e}")

def draw_large_circle_with_star(finger_positions, time=0):
    try:
        if len(finger_positions) < 2:
            return
        
        # Calculate centroid
        centroid_x = sum(pos[0] for pos in finger_positions.values()) / len(finger_positions)
        centroid_y = sum(pos[1] for pos in finger_positions.values()) / len(finger_positions)
        
        # Calculate maximum distance for radius
        distances = [np.sqrt((pos[0] - centroid_x)**2 + (pos[1] - centroid_y)**2) 
                    for pos in finger_positions.values()]
        radius = max(distances) if distances else 1.0
        
        glPushMatrix()
        glTranslatef(centroid_x, centroid_y, 0)
        glRotatef(time * 30, 0, 0, 1)
        
        # Extra glow layer for shininess
        glLineWidth(8.0)  # Thicker for glow
        glBegin(GL_LINE_LOOP)
        glColor4f(1.0, 0.843, 0.0, 0.3)  # Brighter, more transparent glow
        for i in range(360):
            angle = np.radians(i)
            glVertex3f(np.cos(angle) * (radius + 0.4), 
                      np.sin(angle) * (radius + 0.4), 0)
        glEnd()
        
        # Outer glow circle
        glLineWidth(6.0)
        glBegin(GL_LINE_LOOP)
        glColor4f(1.0, 0.843, 0.0, 0.5)
        for i in range(360):
            angle = np.radians(i)
            glVertex3f(np.cos(angle) * (radius + 0.2), 
                      np.sin(angle) * (radius + 0.2), 0)
        glEnd()
        
        # Main circle
        glLineWidth(4.0)  # Bolder main line
        glBegin(GL_LINE_LOOP)
        glColor4f(1.0, 0.843, 0.0, 1.0)
        for i in range(360):
            angle = np.radians(i)
            glVertex3f(np.cos(angle) * radius, 
                      np.sin(angle) * radius, 0)
        glEnd()
        
        # Star shape with endpoints touching the circle
        star_radius = radius
        glLineWidth(6.0)  # Thicker for glow
        glBegin(GL_LINE_LOOP)
        glColor4f(1.0, 0.843, 0.0, 0.4)  # Glow layer
        for i in range(5):
            outer_angle = np.radians(i * 144)
            inner_angle = np.radians(i * 144 + 72)
            glVertex3f(np.cos(outer_angle) * (star_radius + 0.2), np.sin(outer_angle) * (star_radius + 0.2), 0)
            glVertex3f(np.cos(inner_angle) * (star_radius * 0.4 + 0.1), np.sin(inner_angle) * (star_radius * 0.4 + 0.1), 0)
        glEnd()
        
        glLineWidth(4.0)  # Bolder main star
        glBegin(GL_LINE_LOOP)
        glColor4f(1.0, 0.843, 0.0, 0.8)
        for i in range(5):
            outer_angle = np.radians(i * 144)
            inner_angle = np.radians(i * 144 + 72)
            glVertex3f(np.cos(outer_angle) * star_radius, np.sin(outer_angle) * star_radius, 0)
            glVertex3f(np.cos(inner_angle) * star_radius * 0.4, np.sin(inner_angle) * star_radius * 0.4, 0)
        glEnd()
        
        glPopMatrix()
        
        logging.debug(f"Centroid: ({centroid_x}, {centroid_y}), Radius: {radius}, Distances: {distances}")
    except Exception as e:
        logging.error(f"Large circle with star drawing failed: {e}")

def draw_particles():
    try:
        glBegin(GL_POINTS)
        for particle in particles.copy():
            alpha = particle['life'] / 1.0
            size = particle['initial_size'] * alpha
            glColor4f(1.0, 0.843, 0.0, alpha * 1.2)
            glPointSize(size)
            glVertex3f(*particle['pos'])
            
            particle['pos'][0] += particle['vel'][0]
            particle['pos'][1] += particle['vel'][1]
            particle['life'] -= 1/60
            
            if particle['life'] <= 0 and particle in particles:
                particles.remove(particle)
        glEnd()
    except Exception as e:
        logging.error(f"Particle drawing failed: {e}")

def map_coordinates(x, y, width, height):
    return ((x / width) * 7 - 3.5), -((y / height) * 5 - 2.5), 0

# Main loop
init_gl()
clock = pygame.time.Clock()
running = True
time = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
            running = False

    # Capture frame
    success, frame = cap.read()
    if not success:
        logging.error("Failed to capture frame from camera")
        break
    
    frame = cv2.flip(frame, 1)
    height, width = frame.shape[:2]
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Process hand detection
    try:
        results = hands.process(rgb_frame)
    except Exception as e:
        logging.error(f"Hand detection failed: {e}")
        continue
    
    # Clear OpenGL buffer
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # Load and draw video feed as background
    load_video_texture(frame)
    draw_background()
    
    if results.multi_hand_landmarks:
        try:
            current_finger_positions = {}
            for hand_landmarks in results.multi_hand_landmarks:
                fingertip_indices = [4, 8, 12, 16, 20]
                for idx in fingertip_indices:
                    finger_tip = hand_landmarks.landmark[idx]
                    x, y = finger_tip.x * width, finger_tip.y * height
                    gl_x, gl_y, gl_z = map_coordinates(x, y, width, height)
                    
                    # Detect finger movement
                    current_pos = (gl_x, gl_y)
                    finger_id = f"hand_{id(hand_landmarks)}_{idx}"
                    
                    if finger_id in last_finger_positions:
                        last_pos = last_finger_positions[finger_id]
                        dist = np.sqrt((current_pos[0] - last_pos[0])**2 + 
                                     (current_pos[1] - last_pos[1])**2)
                        if dist > 0.05:
                            add_particle(gl_x, gl_y, gl_z)
                    
                    current_finger_positions[finger_id] = current_pos
                    draw_small_circle(gl_x, gl_y, gl_z, time=time)
            
            # Draw large circle with star
            draw_large_circle_with_star(current_finger_positions, time)
            last_finger_positions = current_finger_positions
            
        except Exception as e:
            logging.error(f"Hand processing failed: {e}")
    
    draw_particles()
    
    # Update display
    pygame.display.flip()
    time += 0.05
    clock.tick(60)

# Cleanup
cap.release()
pygame.quit()
logging.info("Program terminated successfully")
