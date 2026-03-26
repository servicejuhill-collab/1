import curses
import os
import shutil
import sys
import time
import json
import psutil
import platform
from datetime import datetime, timedelta
import subprocess

# --- SYSTEM-CHECK ---
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

def boot_animation(stdscr):
    try:
        h, w = stdscr.getmaxyx()
        boot_msg = "BOOTING JUST-OS..."
        x = max(0, (w - len(boot_msg))//2)
        y = max(0, h//2)
        stdscr.addstr(y, x, boot_msg, curses.color_pair(1))
        stdscr.refresh()
        time.sleep(2)
    except:
        pass

# --- CONFIG & PERSISTENCE ---
DATA_FILE = "just_os_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                if "cfg" not in data: data["cfg"] = {}
                if "padding" not in data["cfg"]: data["cfg"]["padding"] = 6
                if "sidebar_width" not in data["cfg"]: data["cfg"]["sidebar_width"] = 30
                if "notes" not in data: data["notes"] = []
                if "games_v2" not in data: data["games_v2"] = []
                if "hack_tools_v2" not in data: data["hack_tools_v2"] = []
                if "username" not in data["cfg"]: data["cfg"]["username"] = "User"
                if "theme" not in data["cfg"]: data["cfg"]["theme"] = "default"
                keys = ["border", "text", "logo", "bg", "sel_bg", "sel_txt", "taskbar_bg", "taskbar_txt"]
                defaults = [curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_BLUE,
                            curses.COLOR_BLACK, curses.COLOR_CYAN, curses.COLOR_BLACK,
                            curses.COLOR_BLACK, curses.COLOR_WHITE]
                for k, d in zip(keys, defaults):
                    if k not in data["cfg"]: data["cfg"][k] = d
                return data
        except:
            pass
    return {
        "notes": [], 
        "games_v2": [],
        "hack_tools_v2": [],
        "cfg": {
            "border": curses.COLOR_BLUE, "text": curses.COLOR_CYAN, "logo": curses.COLOR_BLUE,
            "bg": curses.COLOR_BLACK, "sel_bg": curses.COLOR_CYAN, "sel_txt": curses.COLOR_BLACK,
            "taskbar_bg": curses.COLOR_BLACK, "taskbar_txt": curses.COLOR_WHITE,
            "padding": 6,
            "sidebar_width": 30,
            "username": "User",
            "theme": "default"
        }
    }

user_data = load_data()
cfg = user_data["cfg"]

def save_data():
    user_data["cfg"] = cfg
    with open(DATA_FILE, 'w') as f:
        json.dump(user_data, f, indent=4)

# --- THEMES ---
themes = {
    "default": {
        "border": curses.COLOR_BLUE, "text": curses.COLOR_CYAN, "logo": curses.COLOR_BLUE,
        "bg": curses.COLOR_BLACK, "sel_bg": curses.COLOR_CYAN, "sel_txt": curses.COLOR_BLACK,
        "taskbar_bg": curses.COLOR_BLACK, "taskbar_txt": curses.COLOR_WHITE
    },
    "dark_green": {
        "border": curses.COLOR_GREEN, "text": curses.COLOR_WHITE, "logo": curses.COLOR_GREEN,
        "bg": curses.COLOR_BLACK, "sel_bg": curses.COLOR_GREEN, "sel_txt": curses.COLOR_BLACK,
        "taskbar_bg": curses.COLOR_BLACK, "taskbar_txt": curses.COLOR_GREEN
    },
    "light_blue": {
        "border": curses.COLOR_CYAN, "text": curses.COLOR_BLACK, "logo": curses.COLOR_BLUE,
        "bg": curses.COLOR_WHITE, "sel_bg": curses.COLOR_BLUE, "sel_txt": curses.COLOR_WHITE,
        "taskbar_bg": curses.COLOR_BLUE, "taskbar_txt": curses.COLOR_WHITE
    }
}

def apply_theme(theme_name):
    if theme_name in themes:
        for key, value in themes[theme_name].items():
            cfg[key] = value
    apply_colors()

# --- MASSIVE BEFEHLSDATENBANK ---
CMD_LIST = [
    ("ls -la", "Linux: Alle Dateien inkl. versteckter anzeigen"),
    ("dir /attr", "Windows: Verzeichnisinhalt mit Attributen"),
    ("cd ..", "Universal: Ein Verzeichnis nach oben wechseln"),
    ("chmod +x", "Linux: Datei ausführbar machen"),
    ("sudo su", "Linux: Zum Root-Benutzer wechseln"),
    ("ip a", "Linux: IP-Adressen & Interfaces anzeigen"),
    ("ipconfig /all", "Windows: Komplette Netzwerk-Konfiguration"),
    ("rm -rf", "Linux: Löscht Verzeichnisse rekursiv (Vorsicht!)"),
    ("del /f /s", "Windows: Dateien erzwingen zu löschen"),
    ("mkdir -p", "Universal: Ganze Ordner-Pfade erstellen"),
    ("touch", "Universal: Neue leere Datei anlegen"),
    ("cat", "Linux: Dateiinhalt im Terminal ausgeben"),
    ("type", "Windows: Dateiinhalt im Terminal ausgeben"),
    ("nano", "Linux: Beliebter Terminal-Texteditor"),
    ("notepad", "Windows: Standard Editor öffnen"),
    ("top", "Linux: Systemprozesse in Echtzeit"),
    ("htop", "Linux: Verbesserter bunter Taskmanager"),
    ("tasklist", "Windows: Alle laufenden Prozesse auflisten"),
    ("df -h", "Linux: Festplattenplatz (menschlich lesbar)"),
    ("free -m", "Linux: RAM-Auslastung in Megabyte"),
    ("ping -c 4", "Linux: Verbindung prüfen (4 Pakete)"),
    ("ping -n 4", "Windows: Verbindung prüfen (4 Pakete)"),
    ("nmap -sV", "Netzwerk-Scan: Dienste & Versionen finden"),
    ("airmon-ng", "Linux: WLAN-Monitor-Mode aktivieren"),
    ("airodump-ng", "Linux: WLAN-Netzwerke in der Nähe scannen"),
    ("iwconfig", "Linux: WLAN-Schnittstellen konfigurieren"),
    ("wget -c", "Universal: Download fortsetzen"),
    ("curl -I", "HTTP-Header einer Webseite prüfen"),
    ("apt update", "Linux: Paketlisten aktualisieren"),
    ("apt upgrade", "Linux: Alle Programme aktualisieren"),
    ("winget search", "Windows: Nach Software suchen"),
    ("whoami", "Aktuellen Benutzernamen anzeigen"),
    ("uptime -p", "System-Laufzeit schön anzeigen"),
    ("history -c", "Befehlsverlauf im Terminal löschen"),
    ("reboot", "System sofort neu starten"),
    ("shutdown -h now", "System sofort herunterfahren"),
    ("grep -ri", "Linux: Text in Dateien suchen (case-insensitive)"),
    ("findstr /s", "Windows: Text in Unterverzeichnissen suchen"),
    ("tar -xzvf", "Linux: .tar.gz Archiv entpacken"),
    ("zip -r", "Universal: Dateien in ZIP komprimieren"),
    ("unzip", "Universal: ZIP-Dateien entpacken"),
    ("ssh user@host", "Sichere Remote-Verbindung herstellen"),
    ("scp file user@host:", "Dateien sicher über SSH kopieren"),
    ("systemctl start", "Linux: System-Dienst starten"),
    ("systemctl status", "Linux: Status eines Dienstes prüfen"),
    ("journalctl -xe", "Linux: Letzte Systemfehler anzeigen"),
    ("lsblk", "Linux: Alle Festplatten & Partitionen"),
    ("ps aux", "Linux: Detaillierte Prozessliste"),
    ("kill -9 [PID]", "Linux: Prozess sofort abschießen"),
    ("taskkill /F /PID", "Windows: Prozess sofort beenden"),
    ("netstat -tuln", "Linux: Alle hörenden Ports anzeigen"),
    ("nslookup", "DNS-Einträge einer Domain prüfen"),
    ("chown", "Linux: Dateibesitzer ändern"),
    ("passwd", "Passwort des aktuellen Users ändern")
]

# Vordefinierte Hack-Tools (Nur als Referenz, falls benötigt)
HACK_PAGES = [
    {"n": "WIRELESS", "t": ["aircrack-ng", "wifite", "reaver", "bully", "fluxion", "wifipumpkin3", "eaphammer"]},
    {"n": "PASSWORDS", "t": ["hashcat", "john", "hydra", "medusa", "crunch", "cupp", "hash-id"]},
    {"n": "NETWORK", "t": ["nmap", "bettercap", "wireshark", "netdiscover", "fping", "hping3", "masscan"]},
    {"n": "EXPLOIT", "t": ["msfconsole", "sqlmap", "commix", "searchsploit", "beef-xss", "metasploit"]},
    {"n": "SNIFFING", "t": ["tcpdump", "ettercap", "mitmproxy", "responser", "evil-trust"]}
]

# --- UI LOGIK & FARBEN ---

def apply_colors():
    curses.start_color()
    curses.init_pair(1, cfg["logo"], cfg["bg"])
    curses.init_pair(2, cfg["border"], cfg["bg"])
    curses.init_pair(3, cfg["text"], cfg["bg"])
    curses.init_pair(4, curses.COLOR_GREEN, cfg["bg"])
    curses.init_pair(5, curses.COLOR_RED, cfg["bg"])
    curses.init_pair(6, curses.COLOR_YELLOW, cfg["bg"])
    curses.init_pair(7, cfg["sel_txt"], cfg["sel_bg"])
    curses.init_pair(8, cfg["taskbar_txt"], cfg["taskbar_bg"])

def draw_frame(stdscr, title, sidebar_width=0, taskbar_height=0):
    try:
        h, w = stdscr.getmaxyx()
        if h < 3 or w < 10:
            return
        
        stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
        try:
            stdscr.border(0, 0, 0, 0, 0, 0, 0, 0)
        except:
            pass
        
        if sidebar_width > 0 and sidebar_width < w - 5:
            try:
                stdscr.vline(0, sidebar_width, curses.ACS_VLINE, h - taskbar_height)
                stdscr.addch(0, sidebar_width, curses.ACS_TTEE)
                if taskbar_height > 0 and h - taskbar_height - 1 > 0:
                    stdscr.addch(h - taskbar_height - 1, sidebar_width, curses.ACS_BTEE)
                else:
                    if h - 1 > 0:
                        stdscr.addch(h - 1, sidebar_width, curses.ACS_BTEE)
            except:
                pass

        if taskbar_height > 0 and h - taskbar_height - 1 > 0:
            try:
                stdscr.hline(h - taskbar_height - 1, 0, curses.ACS_HLINE, w)
                stdscr.addch(h - taskbar_height - 1, 0, curses.ACS_LTEE)
                stdscr.addch(h - taskbar_height - 1, w - 1, curses.ACS_RTEE)
                if sidebar_width > 0:
                    stdscr.addch(h - taskbar_height - 1, sidebar_width, curses.ACS_PLUS)
            except:
                pass

        title_str = f" [ {title.upper()} ] "
        x_pos = max(sidebar_width + 1, (w + sidebar_width)//2 - len(title_str)//2)
        if x_pos >= 0 and x_pos < w - len(title_str):
            stdscr.addstr(0, x_pos, title_str)
        
        stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
    except:
        pass

def get_network_info():
    info = {"ssid": "N/A", "ip": "N/A", "signal": "N/A", "error": ""}
    if IS_LINUX:
        try:
            cmd = "nmcli -t -f active,ssid,signal,ip4.address device wifi list"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith("yes"):
                        parts = line.split(":")
                        if len(parts) > 1:
                            info["ssid"] = parts[1]
                        if len(parts) > 2:
                            info["signal"] = parts[2]
                        if len(parts) > 3:
                            ip_address_full = parts[3]
                            if '/' in ip_address_full:
                                info["ip"] = ip_address_full.split('/')[0]
                            else:
                                info["ip"] = ip_address_full
                        break
        except:
            pass
    return info

def draw_sidebar(stdscr, width, taskbar_height):
    try:
        h, w = stdscr.getmaxyx()
        if width <= 0 or width >= w: return
        
        # Sidebar-Inhalt
        stdscr.addstr(2, 2, "SYSTEM INFO", curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(4, 2, f"USER: {cfg['username']}", curses.color_pair(3))
        stdscr.addstr(5, 2, f"OS: JUST-OS V21", curses.color_pair(3))
        
        # CPU/RAM Mini-Anzeige
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        stdscr.addstr(7, 2, f"CPU: {cpu}%", curses.color_pair(4 if cpu < 80 else 5))
        stdscr.addstr(8, 2, f"RAM: {ram}%", curses.color_pair(4 if ram < 80 else 5))
        
        # Netzwerk
        net = get_network_info()
        stdscr.addstr(10, 2, "NETWORK:", curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(11, 2, f"SSID: {net['ssid'][:width-8]}", curses.color_pair(3))
        stdscr.addstr(12, 2, f"IP: {net['ip']}", curses.color_pair(3))
        
        # Uhrzeit
        now = datetime.now().strftime("%H:%M:%S")
        stdscr.addstr(h - taskbar_height - 3, 2, f"TIME: {now}", curses.color_pair(6))
    except:
        pass

def draw_taskbar(stdscr, height, sidebar_width):
    try:
        h, w = stdscr.getmaxyx()
        if height <= 0: return
        
        stdscr.attron(curses.color_pair(8))
        for i in range(height):
            stdscr.addstr(h - 1 - i, 0, " " * w)
        
        taskbar_text = " [W/S] Navigieren | [ENTER] Auswählen | [Q] Zurück "
        stdscr.addstr(h - 1, 2, taskbar_text)
        stdscr.attroff(curses.color_pair(8))
    except:
        pass

# --- UNIVERSAL LIST MENU (FOR GAMES & TOOLS) ---
def universal_list_menu(stdscr, title, data_key):
    sel = 0
    while True:
        try:
            sidebar_width = cfg.get("sidebar_width", 30)
            taskbar_height = 1
            stdscr.clear()
            draw_frame(stdscr, title, sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)

            h, w = stdscr.getmaxyx()
            pad = cfg["padding"]
            content_start_x = sidebar_width + pad
            if content_start_x >= w - 10: content_start_x = 2

            items = user_data.get(data_key, [])
            stdscr.addstr(2, content_start_x, f"{title}:", curses.color_pair(1) | curses.A_BOLD)
            
            for i, item in enumerate(items):
                attr = curses.color_pair(7) if i == sel else curses.color_pair(3)
                if 4 + i < h - taskbar_height - 6:
                    stdscr.addstr(4 + i, content_start_x, f" {i+1}. {item['name']} ", attr)
            
            menu_y = h - taskbar_height - 5
            menu_items = ["[A] HINZUFÜGEN", "[D] LÖSCHEN", "[R] UMBENENNEN", "[Q] ZURÜCK"]
            for i, m_item in enumerate(menu_items):
                attr = curses.color_pair(7) if (len(items) + i) == sel else curses.color_pair(6)
                if menu_y + i < h - taskbar_height - 1:
                    stdscr.addstr(menu_y + i, content_start_x, f" {m_item} ", attr)

            stdscr.timeout(-1)
            k = stdscr.getch()
            stdscr.timeout(1000)
            
            total_items = len(items) + len(menu_items)
            if k in [ord('w'), curses.KEY_UP] and sel > 0: sel -= 1
            elif k in [ord('s'), curses.KEY_DOWN] and sel < total_items - 1: sel += 1
            elif k == ord('a'):
                curses.echo()
                stdscr.addstr(h-3, content_start_x, "Name: ")
                name = stdscr.getstr().decode().strip()
                stdscr.addstr(h-2, content_start_x, "Befehl: ")
                cmd = stdscr.getstr().decode().strip()
                if name and cmd:
                    user_data[data_key].append({"name": name, "cmd": cmd})
                    save_data()
                curses.noecho()
            elif k == ord('d') and sel < len(items):
                user_data[data_key].pop(sel)
                save_data()
                sel = max(0, sel - 1)
            elif k == ord('r') and sel < len(items):
                curses.echo()
                stdscr.addstr(h-3, content_start_x, "Neuer Name: ")
                new_name = stdscr.getstr().decode().strip()
                if new_name:
                    user_data[data_key][sel]['name'] = new_name
                    save_data()
                curses.noecho()
            elif k in [10, 13]:
                if sel < len(items):
                    cmd = items[sel]["cmd"]
                    curses.endwin()
                    print(f"\nStarte: {items[sel]['name']}...")
                    os.system(cmd)
                    print("\nBeendet. Beliebige Taste...")
                    input()
                    stdscr.clear()
                    apply_colors()
                    curses.curs_set(0)
                elif sel == len(items) + 3: break
            elif k == ord('q'): break
        except: break

# --- TERMINAL ---
def terminal_menu(stdscr):
    curses.echo()
    curses.curs_set(1)
    while True:
        try:
            sidebar_width = cfg.get("sidebar_width", 30)
            taskbar_height = 1
            stdscr.clear()
            draw_frame(stdscr, "TERMINAL", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)
            h, w = stdscr.getmaxyx()
            content_start_x = sidebar_width + cfg["padding"]
            stdscr.addstr(2, content_start_x, "JUST-OS TERMINAL ('exit' zum Neustart, 'back' für Menü)", curses.color_pair(6))
            stdscr.addstr(4, content_start_x, f"{os.getcwd()} > ", curses.color_pair(4))
            stdscr.timeout(-1)
            cmd = stdscr.getstr().decode().strip()
            stdscr.timeout(1000)
            if cmd.lower() == "back": break
            if cmd.lower() == "exit":
                curses.endwin()
                print("\n[!] Neustart von JUST-OS...")
                os.execv(sys.executable, [sys.executable] + sys.argv)
            curses.endwin()
            print(f"\n--- Output: {cmd} ---")
            if cmd.startswith("cd "):
                try: os.chdir(cmd[3:])
                except: print("Pfad nicht gefunden.")
            else: os.system(cmd)
            print("\nBeliebige Taste...")
            input()
            stdscr.clear()
            apply_colors()
            curses.curs_set(1)
        except: break
    curses.noecho()
    curses.curs_set(0)

# --- EXPLORER ---
def explorer(stdscr):
    curr, sel, search_query = os.getcwd(), 0, ""
    clipboard = None
    clipboard_is_cut = False
    sidebar_width = cfg.get("sidebar_width", 30)
    taskbar_height = 1
    
    while True:
        try:
            stdscr.clear()
            draw_frame(stdscr, f"EXPLORER: {os.path.basename(curr)}", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)

            h, w = stdscr.getmaxyx()
            pad = cfg["padding"]
            content_start_x = sidebar_width + pad
            content_height = h - taskbar_height - 8

            try:
                all_items = [".. (ZURÜCK)"] + sorted(os.listdir(curr))
                items = [all_items[0]] + [i for i in all_items[1:] if search_query.lower() in i.lower()] if search_query else all_items
            except:
                items = [".. (ZURÜCK)"]
            
            if sel >= len(items): sel = max(0, len(items)-1)

            stdscr.addstr(2, content_start_x, f"PFAD: {curr}", curses.color_pair(1))
            if search_query:
                stdscr.addstr(3, content_start_x, f"SUCHE: {search_query}", curses.color_pair(6))

            for i, item in enumerate(items[:content_height]):
                attr = curses.color_pair(7) if i == sel else curses.color_pair(3)
                full_path = os.path.join(curr, item) if item != ".. (ZURÜCK)" else os.path.dirname(curr)
                
                prefix = "📁 " if os.path.isdir(full_path) else "📄 "
                display_name = f"{prefix}{item}"
                if len(display_name) > w - content_start_x - 5:
                    display_name = display_name[:w - content_start_x - 8] + "..."
                
                stdscr.addstr(5 + i, content_start_x, display_name, attr)

            stdscr.addstr(h - taskbar_height - 2, content_start_x, "[ENTER] Öffnen | [F] Suchen | [C] Kopieren | [X] Ausschneiden | [V] Einfügen", curses.color_pair(6))

            k = stdscr.getch()
            if k in [ord('w'), curses.KEY_UP] and sel > 0: sel -= 1
            elif k in [ord('s'), curses.KEY_DOWN] and sel < len(items)-1: sel += 1
            elif k == ord('f'):
                curses.echo()
                stdscr.addstr(h-3, content_start_x, "Suchen nach: ")
                search_query = stdscr.getstr().decode()
                curses.noecho()
            elif k in [10, 13]:
                if sel == 0:
                    curr = os.path.dirname(curr)
                    sel = 0
                else:
                    target = os.path.join(curr, items[sel])
                    if os.path.isdir(target):
                        curr = target
                        sel = 0
                    else:
                        curses.endwin()
                        os.system(f"nano {target}" if IS_LINUX else f"notepad {target}")
                        stdscr.clear()
                        apply_colors()
            elif k == ord('q'): break
        except: break

# --- COMMANDS VIEW ---
def commands_view(stdscr):
    sel, offset = 0, 0
    sidebar_width = cfg.get("sidebar_width", 30)
    taskbar_height = 1
    while True:
        try:
            stdscr.clear()
            draw_frame(stdscr, "BEFEHLSDATENBANK", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)
            h, w = stdscr.getmaxyx()
            pad = cfg["padding"]
            content_start_x = sidebar_width + pad
            max_r = h - taskbar_height - 6
            for i in range(min(max_r, len(CMD_LIST) - offset)):
                idx = i + offset
                attr = curses.color_pair(7) if idx == sel + offset else curses.color_pair(3)
                cmd, desc = CMD_LIST[idx]
                stdscr.addstr(4 + i, content_start_x, f"{cmd:<20} - {desc[:w-content_start_x-25]}", attr)
            k = stdscr.getch()
            if k in [ord('w'), curses.KEY_UP] and sel > 0: sel -= 1
            elif k in [ord('s'), curses.KEY_DOWN] and sel < min(max_r, len(CMD_LIST)-offset)-1: sel += 1
            elif k == ord('q'): break
        except: break

# --- DASHBOARD ---
def dashboard_menu(stdscr):
    sidebar_width = cfg.get("sidebar_width", 30)
    taskbar_height = 1
    while True:
        try:
            stdscr.clear()
            draw_frame(stdscr, "SYSTEM-DASHBOARD", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)
            h, w = stdscr.getmaxyx()
            pad = cfg["padding"]
            content_start_x = sidebar_width + pad
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            stdscr.addstr(4, content_start_x, f"CPU: {cpu}%", curses.color_pair(3))
            stdscr.addstr(5, content_start_x, f"RAM: {ram.percent}% ({ram.used/1024**3:.1f}GB/{ram.total/1024**3:.1f}GB)", curses.color_pair(3))
            stdscr.addstr(6, content_start_x, f"DISK: {disk.percent}% ({disk.used/1024**3:.1f}GB/{disk.total/1024**3:.1f}GB)", curses.color_pair(3))
            k = stdscr.getch()
            if k == ord('q'): break
        except: break

# --- OFFICE ---
def office_menu(stdscr):
    sidebar_width = cfg.get("sidebar_width", 30)
    taskbar_height = 1
    while True:
        try:
            stdscr.clear()
            draw_frame(stdscr, "OFFICE-SUITE", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)
            h, w = stdscr.getmaxyx()
            content_start_x = sidebar_width + cfg["padding"]
            stdscr.addstr(4, content_start_x, "OFFICE FUNKTIONEN (In Arbeit...)", curses.color_pair(6))
            k = stdscr.getch()
            if k == ord('q'): break
        except: break

# --- MEDIA ---
def media_menu(stdscr):
    sidebar_width = cfg.get("sidebar_width", 30)
    taskbar_height = 1
    while True:
        try:
            stdscr.clear()
            draw_frame(stdscr, "MEDIA-CENTER", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)
            h, w = stdscr.getmaxyx()
            content_start_x = sidebar_width + cfg["padding"]
            stdscr.addstr(4, content_start_x, "MEDIA FUNKTIONEN (In Arbeit...)", curses.color_pair(6))
            k = stdscr.getch()
            if k == ord('q'): break
        except: break

# --- WLAN MANAGER ---
def wifi_menu(stdscr):
    sidebar_width = cfg.get("sidebar_width", 30)
    taskbar_height = 1
    while True:
        try:
            stdscr.clear()
            draw_frame(stdscr, "WLAN-MANAGER", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)
            h, w = stdscr.getmaxyx()
            content_start_x = sidebar_width + cfg["padding"]
            stdscr.addstr(4, content_start_x, "WLAN FUNKTIONEN (Nur Linux)", curses.color_pair(6))
            k = stdscr.getch()
            if k == ord('q'): break
        except: break

# --- NOTIZEN ---
def notes_menu(stdscr):
    sel = 0
    sidebar_width = cfg.get("sidebar_width", 30)
    taskbar_height = 1
    while True:
        try:
            stdscr.clear()
            draw_frame(stdscr, "NOTIZEN", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)
            h, w = stdscr.getmaxyx()
            content_start_x = sidebar_width + cfg["padding"]
            notes = user_data.get("notes", [])
            display_list = notes + ["+ NEUE NOTIZ", "ZURÜCK"]
            for i, item in enumerate(display_list):
                attr = curses.color_pair(7) if i == sel else curses.color_pair(3)
                stdscr.addstr(4 + i, content_start_x, f" > {item}", attr)
            k = stdscr.getch()
            if k in [ord('w'), curses.KEY_UP] and sel > 0: sel -= 1
            elif k in [ord('s'), curses.KEY_DOWN] and sel < len(display_list)-1: sel += 1
            elif k == ord('q'): break
        except: break

# --- SETTINGS ---
def settings_menu(stdscr):
    sel = 0
    colors = [curses.COLOR_BLUE, curses.COLOR_CYAN, curses.COLOR_GREEN, curses.COLOR_RED, curses.COLOR_YELLOW, curses.COLOR_WHITE]
    names = ["BLAU", "CYAN", "GRÜN", "ROT", "GELB", "WEISS"]
    while True:
        try:
            sidebar_width = cfg.get("sidebar_width", 30)
            taskbar_height = 1
            stdscr.clear()
            draw_frame(stdscr, "EINSTELLUNGEN", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)
            h, w = stdscr.getmaxyx()
            content_start_x = sidebar_width + cfg["padding"]
            opts = [
                f"RAHMEN-FARBE: {names[colors.index(cfg['border'])]}",
                f"TEXT-FARBE  : {names[colors.index(cfg['text'])]}",
                f"RAND-ABSTAND: {cfg['padding']}px",
                f"SIDEBAR-BREITE: {cfg['sidebar_width']}px",
                f"BENUTZERNAME: {cfg['username']}",
                "KONFIGURATION SPEICHERN",
                "ZURÜCK"
            ]
            for i, o in enumerate(opts):
                attr = curses.color_pair(7) if i == sel else curses.color_pair(3)
                if 4 + i * 2 < h - 2:
                    stdscr.addstr(4 + i * 2, content_start_x, f" {o} ", attr)
            k = stdscr.getch()
            if k in [ord('w'), curses.KEY_UP] and sel > 0: sel -= 1
            elif k in [ord('s'), curses.KEY_DOWN] and sel < len(opts)-1: sel += 1
            elif k in [10, 13]:
                if sel == 0: cfg['border'] = colors[(colors.index(cfg['border'])+1)%len(colors)]
                elif sel == 1: cfg['text'] = colors[(colors.index(cfg['text'])+1)%len(colors)]
                elif sel == 2: cfg['padding'] = 2 if cfg['padding'] >= 20 else cfg['padding']+2
                elif sel == 3: cfg['sidebar_width'] = 10 if cfg['sidebar_width'] >= 50 else cfg['sidebar_width']+5
                elif sel == 4:
                    curses.echo()
                    stdscr.addstr(h-3, content_start_x, "Neuer Name: ")
                    new_name = stdscr.getstr().decode()
                    if new_name: cfg['username'] = new_name
                    curses.noecho()
                elif sel == 5: save_data()
                elif sel == 6: break
                apply_colors()
            elif k == ord('q'): break
        except: break

# --- MAIN ---
def main(stdscr):
    apply_colors()
    boot_animation(stdscr)
    menu = [
        {"n": "EXPLORER", "f": explorer},
        {"n": "COMMANDS", "f": commands_view},
        {"n": "TERMINAL", "f": terminal_menu},
        {"n": "HACK-TOOLS", "f": lambda s: universal_list_menu(s, "HACK-TOOLS", "hack_tools_v2")},
        {"n": "GAMES", "f": lambda s: universal_list_menu(s, "GAMES", "games_v2")},
        {"n": "NOTIZEN", "f": notes_menu},
        {"n": "WLAN-MANAGER", "f": wifi_menu},
        {"n": "DASHBOARD", "f": dashboard_menu},
        {"n": "OFFICE", "f": office_menu},
        {"n": "MEDIA", "f": media_menu},
        {"n": "SETTINGS", "f": settings_menu},
        {"n": "EXIT", "f": "exit"}
    ]
    sel = 0
    while True:
        try:
            sidebar_width = cfg.get("sidebar_width", 30)
            taskbar_height = 1
            stdscr.clear()
            draw_frame(stdscr, "JUST-OS V21 ULTIMATE", sidebar_width, taskbar_height)
            draw_sidebar(stdscr, sidebar_width, taskbar_height)
            draw_taskbar(stdscr, taskbar_height, sidebar_width)
            h, w = stdscr.getmaxyx()
            content_start_x = sidebar_width + cfg["padding"]
            
            logo = [
                "      ██╗██╗   ██╗███████╗████████╗",
                "      ██║██║   ██║██╔════╝╚══██╔══╝",
                "      ██║██║   ██║███████╗   ██║   ",
                " ██   ██║██║   ██║╚════██║   ██║   ",
                " ╚██████╔╝╚██████╔╝███████║   ██║   ",
                "  ╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   "
            ]
            for i, line in enumerate(logo):
                x_pos = max(content_start_x, (w + content_start_x)//2 - 20)
                if 2 + i < h - 10 and x_pos >= 0:
                    stdscr.addstr(2 + i, x_pos, line, curses.color_pair(1))

            menu_start_y = 10
            for i, item in enumerate(menu):
                attr = curses.color_pair(7) if i == sel else curses.color_pair(3)
                if menu_start_y + i*2 < h - 2:
                    stdscr.addstr(menu_start_y + i*2, content_start_x + 5, f" [ {item['n']:<12} ] ", attr)

            k = stdscr.getch()
            if k in [ord('w'), curses.KEY_UP] and sel > 0: sel -= 1
            elif k in [ord('s'), curses.KEY_DOWN] and sel < len(menu)-1: sel += 1
            elif k in [10, 13]:
                if menu[sel]["f"] == "exit": break
                menu[sel]["f"](stdscr)
            elif k == ord('q'): break
        except: continue

if __name__ == "__main__":
    try: curses.wrapper(main)
    except KeyboardInterrupt: pass
    finally:
        save_data()
        print("\n[!] JUST-OS beendet.")
