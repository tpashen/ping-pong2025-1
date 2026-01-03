from pygame import *
import socket
import json
from threading import Thread
from menu import ConnectWindow

# Ініціалізація вікна підключення
win = ConnectWindow()
win.mainloop()
name = win.name
port = win.port
host = win.host

# --- НАЛАШТУВАННЯ ---
WIDTH, HEIGHT = 800, 600
init()
screen = display.set_mode((WIDTH, HEIGHT))
clock = time.Clock()
display.set_caption("Пінг-Понг")

# --- СЕРВЕР ---
def connect_to_server():
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))
            
            # Відправляємо наше ім'я серверу відразу після підключення
            client.send(name.encode()) 
            
            buffer = ""
            game_state = {}
            # Отримуємо ID гравця
            my_id = int(client.recv(24).decode())
            return my_id, game_state, buffer, client
        except:
            pass

def receive():
    global buffer, game_state, game_over
    while not game_over:
        try:
            data = client.recv(1024).decode()
            if not data:
                break
            buffer += data
            while "\n" in buffer:
                packet, buffer = buffer.split("\n", 1)
                if packet.strip():
                    game_state = json.loads(packet)
        except:
            if "game_state" in globals():
                game_state["winner"] = -1
            break

# --- ШРИФТИ ---
font_win = font.Font("DoorsContinued-Regular.otf", 72)
font_main = font.Font("DoorsContinued-Regular.otf", 36)
font_name = font.Font("DoorsContinued-Regular.otf", 24) # Шрифт для імен над ракетками

# --- ЗОБРАЖЕННЯ ----
# Додано перевірку наявності файлів, щоб уникнути помилок
try:
    background = transform.scale(image.load('fon.jpg'), (WIDTH, HEIGHT))
    background_start = transform.scale(image.load('fon_start.jpg'), (WIDTH, HEIGHT))
    background_end = transform.scale(image.load('game_over.png'), (WIDTH, HEIGHT))
except:
    background = Surface((WIDTH, HEIGHT))
    background.fill((30, 30, 30))
    background_start = Surface((WIDTH, HEIGHT))
    background_start.fill((0, 0, 0))

# --- ЗВУКИ ---
mixer.init()
try:
    mixer.music.load("song18.mp3")
    mixer.music.play(-1)
    kick = mixer.Sound('click.wav')
except:
    print("Звукові файли не знайдено")
    kick = None

# --- ГРА ---
game_over = False
you_winner = None
my_id, game_state, buffer, client = connect_to_server()
Thread(target=receive, daemon=True).start()

while True:
    for e in event.get():
        if e.type == QUIT:
            game_over = True
            exit()

    # Стан очікування або відліку
    if "countdown" in game_state and game_state["countdown"] > 0:
        screen.blit(background_start, (0, 0))
        countdown_text = font_win.render(str(game_state["countdown"]), True, (255, 255, 255))
        screen.blit(countdown_text, (WIDTH // 2 - 20, HEIGHT // 2 - 30))
        display.update()
        continue

    # Стан завершення гри
    if "winner" in game_state and game_state["winner"] is not None:
        screen.blit(background_end, (0, 0))
        
        if you_winner is None:
            you_winner = (game_state["winner"] == my_id)

        text = "Ти переміг!" if you_winner else "Пощастить наступним разом!"
        win_text = font_win.render(text, True, (255, 215, 0))
        screen.blit(win_text, win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        restart_text = font_main.render('К - рестарт (не реалізовано)', True, (200, 200, 200))
        screen.blit(restart_text, restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100)))

        display.update()
        continue

    # Основний процес гри
    if game_state and 'paddles' in game_state:
        screen.blit(background, (0, 0))
        
        # Малюємо ракетки
        p1_y = game_state['paddles']['0']
        p2_y = game_state['paddles']['1']
        draw.rect(screen, (0, 255, 0), (20, p1_y, 20, 100))
        draw.rect(screen, (255, 0, 255), (WIDTH - 40, p2_y, 20, 100))
        
        # --- ВІДОБРАЖЕННЯ ІМЕН ---
        # Отримуємо імена з game_state (припускаємо, що сервер їх надсилає в списку 'names')
        names = game_state.get('names', ["Гравець 1", "Гравець 2"])
        
        name1_surf = font_name.render(names[0], True, (255, 255, 255))
        name2_surf = font_name.render(names[1], True, (255, 255, 255))
        
        # Відображення імен над ракетками
        screen.blit(name1_surf, (20, p1_y - 25))
        screen.blit(name2_surf, (WIDTH - 40 - name2_surf.get_width() + 20, p2_y - 25))

        # Малюємо м'яч та рахунок
        draw.circle(screen, (255, 255, 255), (game_state['ball']['x'], game_state['ball']['y']), 10)
        score_text = font_main.render(f"{game_state['scores'][0]} : {game_state['scores'][1]}", True, (255, 255, 255))
        screen.blit(score_text, (WIDTH // 2 - 25, 20))

        # Обробка звуків
        if game_state.get('sound_event') == 'platform_hit' and kick:
            kick.play()

    else:
        # Стан очікування підключення другого гравця
        screen.blit(background_start, (0, 0))
        waiting_text = font_main.render("Очікування гравців...", True, (255, 255, 255))
        screen.blit(waiting_text, (WIDTH // 2 - 100, HEIGHT // 2))

    display.update()
    clock.tick(60)

    # Управління
    keys = key.get_pressed()
    if keys[K_w] or keys[K_UP]:
        client.send(b"UP")
    elif keys[K_s] or keys[K_DOWN]:
        client.send(b"DOWN")