import pygame
import numpy as np
import sys
from pygame.locals import *

# Inicializar pygame
pygame.init()

# Configuración de la pantalla
WIDTH, HEIGHT = 1150, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulación de Tubo de Rayos Catódicos (CRT)")

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (150, 150, 150)
BLUE = (0, 100, 255)
RED = (255, 50, 50)
GREEN = (0, 255, 0)
BUTTON_COLOR = (0, 180, 255)

# Parámetros físicos fijos
SCREEN_SIZE = 0.3 # Se normaliza adelante
# area de las placas ????
PLATE_SEPARATION = 0.02
DIST_V_TO_H_PLATES = 0.05
DIST_CANNON_TO_V_PLATES = 0.05
DIST_H_PLATES_TO_SCREEN = 0.15
ELECTRON_CHARGE = -1.6e-19
ELECTRON_MASS = 9.11e-31

# Variables controlables
acceleration_voltage = 1000 # se traduce al brillo del punto
vertical_voltage = 0
horizontal_voltage = 0
sine_mode = False
persistence_time = 2.0 # latencia del rastro de puntos
# Parámetros de onda sinusoidal
v_frequency = 1.0
h_frequency = 1.0
v_phase = 0.0
h_phase = 0.0

# Puntos en pantalla
screen_points = []
point_times = []

# Fuente
font = pygame.font.SysFont('Arial', 16)
title_font = pygame.font.SysFont('Arial', 20, bold=True)

# Manejo de tiempo
clock = pygame.time.Clock()
FPS = 60
simulation_time = 0.0

# ---------------- FUNCIONES ---------------- #
def calculate_electron_position(acc_v, v_v, h_v):
    # acc_v: voltaje de aceleración (V)
    # v_v: voltaje en placas verticales (V)
    # h_v: voltaje en placas horizontales (V)
    """Calcula la posición final de un electrón en la pantalla"""
    v0 = np.sqrt(2 * np.abs(acc_v) * np.abs(ELECTRON_CHARGE) / ELECTRON_MASS)

    # Campos eléctricos
    # E = V/d
    # V= diferencia de Voltaje
    # d= distancia entre placas
    E_vertical = v_v / PLATE_SEPARATION
    E_horizontal = h_v / PLATE_SEPARATION
    a_vertical = (ELECTRON_CHARGE * E_vertical) / ELECTRON_MASS
    a_horizontal = (ELECTRON_CHARGE * E_horizontal) / ELECTRON_MASS

    # Tiempos de vuelo
    t1 = DIST_CANNON_TO_V_PLATES / v0
    t2 = DIST_V_TO_H_PLATES / v0
    t3 = DIST_H_PLATES_TO_SCREEN / v0

    # Deflexiones
    # y = y0 + v0*t + 0.5*a*t^2
    y_def = 0.5 * a_vertical * t1**2 + a_vertical * t1 * (t2 + t3)
    x_def = 0.5 * a_horizontal * t2**2 + a_horizontal * t2 * t3

    return x_def, y_def

def draw_crt(x_norm, y_norm):
    """Dibuja las vistas del CRT con haz dinámico"""

    # -------- Vista lateral (trayectoria vertical) --------
    pygame.draw.rect(screen, GRAY, (50, 50, 300, 200), 2)
    center_y = 150
    # Graficar rastro vertical
    if screen_points:
        for i in range(1, len(screen_points)):
            y1 = int(center_y - screen_points[i-1][1] * 90)
            y2 = int(center_y - screen_points[i][1] * 90)
            x1 = 50 + int((i-1)/len(screen_points)*300)
            x2 = 50 + int(i/len(screen_points)*300)
            alpha = max(30, int(255 * (1 - (pygame.time.get_ticks()/1000.0 - point_times[i]) / persistence_time)))
            color = (0, 255, 0, alpha)
            s = pygame.Surface((300,200), pygame.SRCALPHA)
            pygame.draw.line(s, color, (x1-50, y1-50), (x2-50, y2-50), 3)
            screen.blit(s, (50, 50))
    # Elementos fijos
    pygame.draw.rect(screen, GRAY, (50, 140, 20, 20))  
    pygame.draw.rect(screen, BLUE, (100, 100, 10, 100))
    pygame.draw.rect(screen, BLUE, (120, 100, 10, 100))
    pygame.draw.rect(screen, RED, (180, 130, 10, 40))
    pygame.draw.rect(screen, RED, (200, 130, 10, 40))
    pygame.draw.rect(screen, GRAY, (280, 50, 70, 200), 2)

    # -------- Vista superior (solo desplazamiento horizontal, punto grande y brillante) --------
    pygame.draw.rect(screen, GRAY, (50, 300, 300, 150), 2)
    center_x = 200
    center_y = 375
    scale_x = 140  # Más amplio
    if screen_points:
        x = screen_points[-1][0]
        px = int(center_x + x * scale_x)
        py = center_y
        s = pygame.Surface((30,30), pygame.SRCALPHA)
        pygame.draw.circle(s, (0,255,0,220), (15,15), 13)
        screen.blit(s, (px-15, py-15))
    # Elementos fijos
    pygame.draw.rect(screen, GRAY, (50, 365, 20, 20))
    pygame.draw.rect(screen, BLUE, (100, 340, 10, 70))
    pygame.draw.rect(screen, BLUE, (120, 340, 10, 70))
    pygame.draw.rect(screen, RED, (180, 320, 10, 110))
    pygame.draw.rect(screen, RED, (200, 320, 10, 110))
    pygame.draw.rect(screen, GRAY, (280, 300, 70, 150), 2)

    # -------- Pantalla frontal (con rastro) --------
    # Pantalla principal compacta
    pantalla_x, pantalla_y, pantalla_w, pantalla_h = 420, 60, 400, 400
    pygame.draw.rect(screen, GRAY, (pantalla_x, pantalla_y, pantalla_w, pantalla_h), 3)

    zoom_factor = 0.95
    current_time = pygame.time.get_ticks() / 1000.0

    # Dibujar puntos con rastro (fade)
    for i, (x, y, color) in enumerate(screen_points):
        age = current_time - point_times[i]
        if age < persistence_time:
            alpha = max(30, int(255 * (1 - age / persistence_time)))
            px = int(pantalla_x + pantalla_w/2 + x * (pantalla_w/2 * zoom_factor))
            py = int(pantalla_y + pantalla_h/2 - y * (pantalla_h/2 * zoom_factor))
            s = pygame.Surface((8,8), pygame.SRCALPHA)
            pygame.draw.circle(s, (color[0], color[1], color[2], alpha), (4,4), 3)
            screen.blit(s, (px-4, py-4))

def draw_ui():
    """Dibuja los controles en la interfaz"""
    screen.blit(title_font.render("Vista Lateral", True, WHITE), (150, 20))
    screen.blit(title_font.render("Vista Superior", True, WHITE), (150, 270))
    screen.blit(title_font.render("Pantalla", True, WHITE), (680, 20))

    # Botones en dos filas debajo de la pantalla principal
    button_w, button_h = 32, 32
    text_color = WHITE
    start_x = 120
    start_y1 = 500
    start_y2 = 570  # Más espacio entre filas
    spacing = 160
    label_y1 = start_y1 - 18  # Más cerca de los botones
    label_y2 = start_y2 - 18
    params = [
        {"label": "Aceleración", "value": f"{acceleration_voltage} V", "id": "acc"},
        {"label": "Vertical", "value": f"{vertical_voltage:.2f} V", "id": "vert"},
        {"label": "Horizontal", "value": f"{horizontal_voltage:.2f} V", "id": "hor"},
        {"label": "Persistencia", "value": f"{persistence_time:.1f} s", "id": "pers"},
    ]
    extra_params = []
    if sine_mode:
        extra_params = [
            {"label": "Frec. Vert.", "value": f"{v_frequency:.2f} Hz", "id": "vfreq"},
            {"label": "Frec. Hor.", "value": f"{h_frequency:.2f} Hz", "id": "hfreq"},
            {"label": "Fase Vert.", "value": f"{v_phase:.2f} rad", "id": "vph"},
            {"label": "Fase Hor.", "value": f"{h_phase:.2f} rad", "id": "hph"},
        ]
    global button_rects
    button_rects = {}
    # Primera fila
    for i, p in enumerate(params):
        x = start_x + i * spacing
        screen.blit(font.render(f"{p['label']}: {p['value']}", True, text_color), (x, label_y1))
        rect_minus = pygame.Rect(x, start_y1, button_w, button_h)
        pygame.draw.rect(screen, BUTTON_COLOR, rect_minus)
        screen.blit(font.render("-", True, WHITE), (x+8, start_y1+6))
        button_rects[p['id']+"_minus"] = rect_minus
        rect_plus = pygame.Rect(x+button_w+8, start_y1, button_w, button_h)
        pygame.draw.rect(screen, BUTTON_COLOR, rect_plus)
        screen.blit(font.render("+", True, WHITE), (x+button_w+16, start_y1+6))
        button_rects[p['id']+"_plus"] = rect_plus
    # Segunda fila
    for i, p in enumerate(extra_params):
        x = start_x + i * spacing
        screen.blit(font.render(f"{p['label']}: {p['value']}", True, text_color), (x, label_y2))
        rect_minus = pygame.Rect(x, start_y2, button_w, button_h)
        pygame.draw.rect(screen, BUTTON_COLOR, rect_minus)
        screen.blit(font.render("-", True, WHITE), (x+8, start_y2+6))
        button_rects[p['id']+"_minus"] = rect_minus
        rect_plus = pygame.Rect(x+button_w+8, start_y2, button_w, button_h)
        pygame.draw.rect(screen, BUTTON_COLOR, rect_plus)
        screen.blit(font.render("+", True, WHITE), (x+button_w+16, start_y2+6))
        button_rects[p['id']+"_plus"] = rect_plus
    # Botón de modo
    mode_text = "Modo: Sinusoidal" if sine_mode else "Modo: Manual"
    mode_x = start_x + max(len(params), len(extra_params)) * spacing
    screen.blit(font.render(mode_text, True, WHITE), (mode_x, label_y1))
    rect_mode = pygame.Rect(mode_x, start_y1, 80, button_h)
    pygame.draw.rect(screen, (0,255,100), rect_mode)
    screen.blit(font.render("Cambiar", True, WHITE), (mode_x + 8, start_y1+6))
    button_rects["mode_btn"] = rect_mode

# ---------------- BUCLE PRINCIPAL ---------------- #
running = True
while running:
    dt = clock.tick(FPS) / 1000.0
    simulation_time += dt

    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == MOUSEBUTTONDOWN:
            mx, my = event.pos
            for key, rect in button_rects.items():
                if rect.collidepoint(mx, my):
                    if key == "acc_minus": acceleration_voltage = max(1000, acceleration_voltage - 1000)
                    elif key == "acc_plus": acceleration_voltage = min(5000, acceleration_voltage + 100)
                    elif key == "vert_minus": vertical_voltage = max(-1000, vertical_voltage - 5)
                    elif key == "vert_plus": vertical_voltage = min(1000, vertical_voltage + 5)
                    elif key == "hor_minus": horizontal_voltage = max(-1000, horizontal_voltage - 5)
                    elif key == "hor_plus": horizontal_voltage = min(1000, horizontal_voltage + 5)
                    elif key == "pers_minus": persistence_time = max(0.5, persistence_time - 0.5)
                    elif key == "pers_plus": persistence_time = min(10.0, persistence_time + 0.5)
                    elif key == "vfreq_minus": v_frequency = max(0.1, v_frequency - 0.1)
                    elif key == "vfreq_plus": v_frequency = min(10.0, v_frequency + 0.1)
                    elif key == "hfreq_minus": h_frequency = max(0.1, h_frequency - 0.1)
                    elif key == "hfreq_plus": h_frequency = min(10.0, h_frequency + 0.1)
                    elif key == "vph_minus": v_phase = max(0.0, v_phase - 0.1)
                    elif key == "vph_plus": v_phase = min(6.28, v_phase + 0.1)
                    elif key == "hph_minus": h_phase = max(0.0, h_phase - 0.1)
                    elif key == "hph_plus": h_phase = min(6.28, h_phase + 0.1)
                    elif key == "mode_btn": sine_mode = not sine_mode

    # Voltajes sinusoidales
    if sine_mode:
        vertical_voltage = 50 * np.sin(2*np.pi*v_frequency*simulation_time + v_phase)
        horizontal_voltage = 50 * np.sin(2*np.pi*h_frequency*simulation_time + h_phase)

    # Simulación de punto
    x, y = calculate_electron_position(acceleration_voltage, vertical_voltage, horizontal_voltage)

    # Normalización
    # centro en (0,0), rango [-1,1]
    x_norm = np.clip(x / (SCREEN_SIZE/2), -1, 1)
    y_norm = np.clip(y / (SCREEN_SIZE/2), -1, 1)

    # Brillo proporcional al voltaje de aceleración
    brightness = min(255, int(acceleration_voltage / 20))
    color = (0, brightness, 0)

    screen_points.append((x_norm, y_norm, color))
    point_times.append(pygame.time.get_ticks() / 1000.0)

    if len(screen_points) > 1000:
        screen_points.pop(0)
        point_times.pop(0)

    screen.fill(BLACK)
    draw_crt(x_norm, y_norm)
    draw_ui()
    pygame.display.flip()

pygame.quit()
sys.exit()