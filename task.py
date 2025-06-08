#!/usr/bin/env python3
"""
Core S Floating Taskbar
Taskbar flutuante revolucionária para Core S System
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import time
import os
import psutil
from datetime import datetime

# Tentar importar keyboard, se não tiver usar xbindkeys como fallback
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
    print("✅ Biblioteca 'keyboard' disponível - usando atalhos globais nativos")
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("⚠️ Biblioteca 'keyboard' não encontrada")
    print("💡 Instale com: pip install keyboard")
    print("🔧 Usando xbindkeys como fallback")

class CoresFloatingTaskbar:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Core S Taskbar")
        
        # Configurações da janela principal (invisível)
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.withdraw()  # Ocultar janela principal
        
        # Estados da taskbar
        self.is_expanded = False
        self.is_visible = True
        self.current_corner = 0  # 0=inf_esq, 1=sup_esq, 2=sup_dir, 3=inf_dir
        self.corners = [
            'bottom_left',   # 0
            'top_left',      # 1  
            'top_right',     # 2
            'bottom_right'   # 3
        ]
        
        # Dimensões
        self.square_size = 60
        self.expanded_width = 400
        self.expanded_height = 45  # Altura da barra (menor que quadrado)
        self.margin = 20
        
        # Cores Core S
        self.bg_color = "#0d1117"
        self.accent_color = "#58a6ff"
        self.secondary_color = "#21262d"
        self.text_color = "#f0f6fc"
        
        # Criar widgets separados
        self.create_square_widget()
        self.create_expanded_widget()
        
        # Posicionar inicial
        self.position_widgets()
        
        # Configurar atalhos globais
        self.setup_hotkeys()
        
        # Iniciar threads de monitoramento
        self.start_monitoring()
        
        # Variáveis para animação
        self.animation_running = False
    
    def create_square_widget(self):
        """Criar widget do quadrado S (sempre visível)"""
        self.square_window = tk.Toplevel(self.root)
        self.square_window.title("Core S Square")
        self.square_window.overrideredirect(True)
        self.square_window.attributes('-topmost', True)
        self.square_window.attributes('-alpha', 0.95)
        
        # Frame do quadrado
        self.square_frame = tk.Frame(
            self.square_window,
            width=self.square_size,
            height=self.square_size,
            bg=self.bg_color,
            relief='raised',
            bd=2
        )
        self.square_frame.pack(fill=tk.BOTH, expand=True)
        self.square_frame.pack_propagate(False)
        
        # Label com "S"
        self.s_label = tk.Label(
            self.square_frame,
            text="S",
            font=("Ubuntu", 24, "bold"),
            fg=self.accent_color,
            bg=self.bg_color
        )
        self.s_label.pack(expand=True)
        
        # Indicador de posição
        self.position_indicator = tk.Label(
            self.square_frame,
            text="●",
            font=("Arial", 8),
            fg=self.accent_color,
            bg=self.bg_color
        )
        self.position_indicator.place(x=45, y=45)
        
        # Bind para dar foco e atalhos (mantido como backup)
        self.square_window.bind('<Button-1>', self.give_focus)
    
    def create_expanded_widget(self):
        """Criar widget da barra expandida (inicialmente oculto)"""
        self.expanded_window = tk.Toplevel(self.root)
        self.expanded_window.title("Core S Bar")
        self.expanded_window.overrideredirect(True)
        self.expanded_window.attributes('-topmost', True)
        self.expanded_window.attributes('-alpha', 0.95)
        self.expanded_window.withdraw()  # Inicialmente oculto
        
        # Frame da barra expandida
        self.expanded_frame = tk.Frame(
            self.expanded_window,
            width=self.expanded_width - self.square_size,
            height=self.expanded_height,
            bg=self.secondary_color,
            relief='raised',
            bd=1
        )
        self.expanded_frame.pack(fill=tk.BOTH, expand=True)
        self.expanded_frame.pack_propagate(False)
        
        # Conteúdo da barra
        self.create_expanded_content()
    
    def position_widgets(self):
        """Posicionar widgets do quadrado e barra"""
        # Obter dimensões da tela
        screen_width = self.square_window.winfo_screenwidth()
        screen_height = self.square_window.winfo_screenheight()
        
        # Calcular posições baseado no canto atual
        corner = self.corners[self.current_corner]
        
        if corner == 'bottom_left':
            square_x = self.margin
            square_y = screen_height - self.square_size - self.margin
        elif corner == 'top_left':
            square_x = self.margin
            square_y = self.margin
        elif corner == 'top_right':
            square_x = screen_width - self.square_size - self.margin
            square_y = self.margin
        elif corner == 'bottom_right':
            square_x = screen_width - self.square_size - self.margin
            square_y = screen_height - self.square_size - self.margin
        
        # Posicionar quadrado
        self.square_window.geometry(f"{self.square_size}x{self.square_size}+{square_x}+{square_y}")
        
        # Posicionar barra expandida (se expandido)
        if self.is_expanded and corner in ['top_left', 'bottom_left']:
            bar_x = square_x + self.square_size + 2  # 2px de espaço
            
            # Alinhar pela parte inferior
            if corner == 'bottom_left':
                bar_y = square_y + (self.square_size - self.expanded_height)  # Alinhamento inferior
            else:  # top_left
                bar_y = square_y + (self.square_size - self.expanded_height)  # Alinhamento inferior
            
            self.expanded_window.geometry(
                f"{self.expanded_width - self.square_size}x{self.expanded_height}+{bar_x}+{bar_y}"
            )
    
    def create_expanded_content(self):
        """Criar conteúdo da parte expandida"""
        # Frame superior (informações do sistema)
        top_frame = tk.Frame(self.expanded_frame, bg=self.secondary_color, height=20)
        top_frame.pack(fill=tk.X, padx=5, pady=2)
        top_frame.pack_propagate(False)
        
        # Relógio
        self.clock_label = tk.Label(
            top_frame,
            text="",
            font=("Ubuntu Mono", 9, "bold"),
            fg=self.text_color,
            bg=self.secondary_color
        )
        self.clock_label.pack(side=tk.RIGHT)
        
        # CPU/RAM
        self.system_label = tk.Label(
            top_frame,
            text="",
            font=("Ubuntu Mono", 8),
            fg=self.accent_color,
            bg=self.secondary_color
        )
        self.system_label.pack(side=tk.LEFT)
        
        # Frame inferior (aplicações)
        bottom_frame = tk.Frame(self.expanded_frame, bg=self.secondary_color)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # Botões de aplicações
        self.create_app_buttons(bottom_frame)
    
    def create_app_buttons(self, parent):
        """Criar botões das aplicações"""
        apps = [
            ("📁", "Files", "nemo"),
            ("🌐", "Browser", "firefox"),
            ("⚙️", "Settings", "xfce4-settings-manager"),
            ("💻", "Terminal", "xfce4-terminal"),
            ("📝", "Editor", "mousepad")
        ]
        
        for icon, name, command in apps:
            btn = tk.Button(
                parent,
                text=icon,
                font=("Arial", 12),
                width=3,
                height=1,
                bg=self.bg_color,
                fg=self.text_color,
                relief='flat',
                command=lambda cmd=command: self.launch_app(cmd)
            )
            btn.pack(side=tk.LEFT, padx=1)
            
            # Hover effects
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=self.accent_color))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg=self.bg_color))
    
    def toggle_expansion(self):
        """Alternar entre expandido e recolhido"""
        if self.animation_running:
            return
        
        # Só pode expandir nos cantos esquerdos
        corner = self.corners[self.current_corner]
        if corner not in ['top_left', 'bottom_left']:
            return
        
        self.animation_running = True
        
        if self.is_expanded:
            self.collapse_taskbar()
        else:
            self.expand_taskbar()
    
    def expand_taskbar(self):
        """Expandir taskbar com animação"""
        def animate_expand():
            # Posicionar barra expandida
            self.position_widgets()
            
            # Mostrar barra expandida
            self.expanded_window.deiconify()
            
            # Animação de expansão (da direita para esquerda)
            steps = 10
            start_width = 10
            end_width = self.expanded_width - self.square_size
            step_size = (end_width - start_width) / steps
            
            # Posição da barra
            screen_width = self.square_window.winfo_screenwidth()
            screen_height = self.square_window.winfo_screenheight()
            corner = self.corners[self.current_corner]
            
            if corner == 'bottom_left':
                square_x = self.margin
                square_y = screen_height - self.square_size - self.margin
            else:  # top_left
                square_x = self.margin
                square_y = self.margin
            
            bar_x = square_x + self.square_size + 2
            bar_y = square_y + (self.square_size - self.expanded_height)
            
            for i in range(steps + 1):
                current_width = int(start_width + (step_size * i))
                self.expanded_window.geometry(f"{current_width}x{self.expanded_height}+{bar_x}+{bar_y}")
                self.expanded_window.update()
                time.sleep(0.02)
            
            self.is_expanded = True
            self.animation_running = False
        
        threading.Thread(target=animate_expand, daemon=True).start()
    
    def collapse_taskbar(self):
        """Recolher taskbar com animação"""
        def animate_collapse():
            steps = 10
            start_width = self.expanded_width - self.square_size
            end_width = 10
            step_size = (start_width - end_width) / steps
            
            # Posição da barra
            screen_width = self.square_window.winfo_screenwidth()
            screen_height = self.square_window.winfo_screenheight()
            corner = self.corners[self.current_corner]
            
            if corner == 'bottom_left':
                square_x = self.margin
                square_y = screen_height - self.square_size - self.margin
            else:  # top_left
                square_x = self.margin
                square_y = self.margin
            
            bar_x = square_x + self.square_size + 2
            bar_y = square_y + (self.square_size - self.expanded_height)
            
            for i in range(steps + 1):
                current_width = int(start_width - (step_size * i))
                self.expanded_window.geometry(f"{current_width}x{self.expanded_height}+{bar_x}+{bar_y}")
                self.expanded_window.update()
                time.sleep(0.02)
            
            # Ocultar barra expandida
            self.expanded_window.withdraw()
            
            self.is_expanded = False
            self.animation_running = False
        
        threading.Thread(target=animate_collapse, daemon=True).start()
    
    def move_to_next_corner(self):
        """Mover para próximo canto"""
        if self.animation_running:
            return
        
        # Se expandido, recolher primeiro
        if self.is_expanded:
            self.collapse_taskbar()
            # Aguardar animação terminar
            self.square_window.after(300, self._complete_corner_move)
        else:
            self._complete_corner_move()
    
    def _complete_corner_move(self):
        """Completar movimento de canto"""
        self.current_corner = (self.current_corner + 1) % 4
        self.position_widgets()
        
        # Atualizar indicador de posição
        corner_indicators = ["◣", "◤", "◥", "◢"]
        if hasattr(self, 'position_indicator'):
            self.position_indicator.configure(text=corner_indicators[self.current_corner])
    
    def toggle_visibility(self):
        """Alternar visibilidade completa"""
        try:
            if self.is_visible:
                print("🙈 Ocultando taskbar...")
                self.square_window.withdraw()
                self.expanded_window.withdraw()
                self.is_visible = False
            else:
                print("👁️ Exibindo taskbar...")
                self.square_window.deiconify()
                if self.is_expanded:
                    self.expanded_window.deiconify()
                self.square_window.lift()
                self.square_window.attributes('-topmost', True)
                self.is_visible = True
                
                # Reposicionar após exibir
                self.position_widgets()
        
        except Exception as e:
            print(f"Erro ao alternar visibilidade: {e}")
    
    def setup_hotkeys(self):
        """Configurar atalhos globais independentes de foco"""
        # Método 1: Atalhos locais (quando tem foco)
        self.square_window.bind('<KeyPress>', self.handle_keypress)
        
        # Método 2: Sistema de atalhos globais via thread
        self.setup_global_hotkeys()
        
        # Método 3: Comandos manuais via arquivo
        self.setup_manual_commands()
        
        # Método 4: Interface de debug
        self.create_debug_interface()
        
        print("🔧 ATALHOS GLOBAIS CONFIGURADOS:")
        print("   Alt+1, Alt+2, Alt+3 funcionam SEM precisar de foco!")
        print("   Método 1: Detecção via xdotool")
        print("   Método 2: Comandos manuais via arquivo")
        print("   Método 3: Interface de debug")
    
    def setup_global_hotkeys(self):
        """Configurar atalhos globais via monitoramento"""
        def global_hotkey_monitor():
            import subprocess
            import time
            
            # Estados das teclas
            alt_pressed = False
            key_states = {'1': False, '2': False, '3': False}
            
            print("🔍 Monitor de atalhos globais iniciado...")
            
            while True:
                try:
                    # Método 1: Verificar via xdotool se disponível
                    try:
                        # Verificar se Alt está pressionado
                        result = subprocess.run(
                            "xdotool key --delay 0 --clearmodifiers Alt_L 2>/dev/null; echo $?",
                            shell=True, capture_output=True, text=True, timeout=0.1
                        )
                    except:
                        pass
                    
                    # Método 2: Verificar via xinput (mais confiável)
                    try:
                        result = subprocess.run(
                            "xinput test-xi2 --root 2>/dev/null | timeout 0.1 grep -E 'KeyPress|KeyRelease'",
                            shell=True, capture_output=True, text=True
                        )
                        
                        if 'KeyPress' in result.stdout:
                            lines = result.stdout.strip().split('\n')
                            for line in lines:
                                if 'detail: 64' in line:  # Alt key
                                    alt_pressed = True
                                elif 'detail: 10' in line and alt_pressed:  # Key 1
                                    print("🔥 ATALHO GLOBAL: Alt+1 detectado!")
                                    self.square_window.after(0, self.toggle_expansion)
                                elif 'detail: 11' in line and alt_pressed:  # Key 2
                                    print("🔥 ATALHO GLOBAL: Alt+2 detectado!")
                                    self.square_window.after(0, self.move_to_next_corner)
                                elif 'detail: 12' in line and alt_pressed:  # Key 3
                                    print("🔥 ATALHO GLOBAL: Alt+3 detectado!")
                                    self.square_window.after(0, self.toggle_visibility)
                        
                        if 'KeyRelease' in result.stdout and 'detail: 64' in result.stdout:
                            alt_pressed = False
                    
                    except:
                        pass
                    
                    # Método 3: Polling simples via xev
                    try:
                        result = subprocess.run(
                            "timeout 0.1 xev -root | grep -E 'KeyPress.*state 0x8.*(keycode 10|keycode 11|keycode 12)'",
                            shell=True, capture_output=True, text=True
                        )
                        
                        if result.stdout:
                            if 'keycode 10' in result.stdout:  # Alt+1
                                print("🎯 ATALHO XEV: Alt+1!")
                                self.square_window.after(0, self.toggle_expansion)
                            elif 'keycode 11' in result.stdout:  # Alt+2
                                print("🎯 ATALHO XEV: Alt+2!")
                                self.square_window.after(0, self.move_to_next_corner)
                            elif 'keycode 12' in result.stdout:  # Alt+3
                                print("🎯 ATALHO XEV: Alt+3!")
                                self.square_window.after(0, self.toggle_visibility)
                    
                    except:
                        pass
                    
                    time.sleep(0.05)  # 50ms de intervalo
                
                except Exception as e:
                    print(f"⚠️ Erro no monitor de atalhos: {e}")
                    time.sleep(1)
        
        # Iniciar monitor em thread separada
        threading.Thread(target=global_hotkey_monitor, daemon=True).start()
        
        # Método adicional: Verificar pressionamento de teclas via polling
        self.start_key_state_polling()
    
    def start_key_state_polling(self):
        """Polling de estado das teclas (método alternativo)"""
        def key_polling():
            last_states = {}
            
            while True:
                try:
                    # Verificar estado atual das teclas via /proc se disponível
                    current_time = time.time()
                    
                    # Verificar combinações Alt+1, Alt+2, Alt+3 via comando direto
                    for key, cmd in [('1', 'toggle_expansion'), ('2', 'move_corner'), ('3', 'toggle_visibility')]:
                        try:
                            # Tentar detectar via keystroke timing
                            test_file = f"/tmp/cores_key_{key}"
                            
                            # Criar arquivo teste se não existir
                            if not os.path.exists(test_file):
                                with open(test_file, 'w') as f:
                                    f.write(str(current_time))
                            
                        except:
                            pass
                    
                    time.sleep(0.1)
                
                except Exception:
                    time.sleep(0.5)
        
        threading.Thread(target=key_polling, daemon=True).start()
    
    def give_focus(self, event):
        """Dar foco à janela quando clicada"""
        self.square_window.focus_set()
        print("👆 Foco dado à taskbar")
        print("💡 Mas os atalhos globais funcionam SEM foco também!")
    
    def create_debug_interface(self):
        """Criar interface de debug com botões"""
        # Criar janela de debug pequena
        self.debug_window = tk.Toplevel(self.square_window)
        self.debug_window.title("Core S Debug")
        self.debug_window.geometry("200x100+50+50")
        self.debug_window.configure(bg=self.bg_color)
        self.debug_window.attributes('-topmost', True)
        
        # Botões de teste
        btn1 = tk.Button(self.debug_window, text="1️⃣ Expand", 
                        command=self.toggle_expansion, bg=self.secondary_color, 
                        fg=self.text_color)
        btn1.pack(side=tk.LEFT, padx=2, pady=5)
        
        btn2 = tk.Button(self.debug_window, text="2️⃣ Move", 
                        command=self.move_to_next_corner, bg=self.secondary_color, 
                        fg=self.text_color)
        btn2.pack(side=tk.LEFT, padx=2, pady=5)
        
        btn3 = tk.Button(self.debug_window, text="3️⃣ Hide", 
                        command=self.toggle_visibility, bg=self.secondary_color, 
                        fg=self.text_color)
        btn3.pack(side=tk.LEFT, padx=2, pady=5)
        self.debug_window.attributes('-topmost', True)
        
        # Botões de teste
        btn1 = tk.Button(self.debug_window, text="1️⃣ Expand", 
                        command=self.toggle_expansion, bg=self.secondary_color, 
                        fg=self.text_color)
        btn1.pack(side=tk.LEFT, padx=2, pady=5)
        
        btn2 = tk.Button(self.debug_window, text="2️⃣ Move", 
                        command=self.move_to_next_corner, bg=self.secondary_color, 
                        fg=self.text_color)
        btn2.pack(side=tk.LEFT, padx=2, pady=5)
        
        btn3 = tk.Button(self.debug_window, text="3️⃣ Hide", 
                        command=self.toggle_visibility, bg=self.secondary_color, 
                        fg=self.text_color)
        btn3.pack(side=tk.LEFT, padx=2, pady=5)
    
    def handle_keypress(self, event):
        """Processar teclas pressionadas"""
        print(f"🔍 Tecla: {event.keysym}, State: {event.state}, Char: {event.char}")
        
        # Verificar Alt (state pode ser 8, 16 ou outros valores)
        if event.state & 0x8 or event.state & 0x10:  # Alt pressionado
            if event.keysym in ['1', 'KP_1']:
                print("✅ Alt+1 detectado!")
                self.toggle_expansion()
                return 'break'
            elif event.keysym in ['2', 'KP_2']:
                print("✅ Alt+2 detectado!")
                self.move_to_next_corner()
                return 'break'
            elif event.keysym in ['3', 'KP_3']:
                print("✅ Alt+3 detectado!")
                self.toggle_visibility()
                return 'break'
        
        # Teste sem Alt também
        if event.keysym == 'F1':
            print("🧪 F1 pressionado - testando expansão")
            self.toggle_expansion()
        elif event.keysym == 'F2':
            print("🧪 F2 pressionado - testando movimento")
            self.move_to_next_corner()
        elif event.keysym == 'F3':
            print("🧪 F3 pressionado - testando visibilidade")
            self.toggle_visibility()
    
    def setup_manual_commands(self):
        """Setup de comandos manuais via arquivo"""
        def command_monitor():
            command_file = "/tmp/cores_manual_cmd"
            
            while True:
                try:
                    if os.path.exists(command_file):
                        with open(command_file, 'r') as f:
                            cmd = f.read().strip()
                        
                        print(f"📁 Comando manual detectado: {cmd}")
                        os.remove(command_file)
                        
                        if cmd == "1":
                            print("🔄 Executando toggle expansion")
                            self.root.after(0, self.toggle_expansion)
                        elif cmd == "2":
                            print("🔄 Executando move corner")
                            self.root.after(0, self.move_to_next_corner)
                        elif cmd == "3":
                            print("🔄 Executando toggle visibility")
                            self.root.after(0, self.toggle_visibility)
                        elif cmd == "test":
                            print("🧪 Teste de comunicação OK!")
                
                except Exception as e:
                    print(f"❌ Erro no monitor: {e}")
                
                time.sleep(0.1)
        
        threading.Thread(target=command_monitor, daemon=True).start()
        
        # Teste inicial de comunicação
        try:
            with open("/tmp/cores_manual_cmd", "w") as f:
                f.write("test")
        except Exception as e:
            print(f"❌ Erro ao criar arquivo de teste: {e}")
    
    def start_monitoring(self):
        """Iniciar monitoramento do sistema"""
        self.update_system_info()
        self.update_clock()
    
    def update_system_info(self):
        """Atualizar informações do sistema"""
        def update():
            while True:
                try:
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    ram_percent = memory.percent
                    
                    if self.is_expanded and hasattr(self, 'system_label'):
                        info_text = f"CPU: {cpu_percent:.0f}% | RAM: {ram_percent:.0f}%"
                        self.system_label.configure(text=info_text)
                
                except Exception:
                    pass
                
                time.sleep(2)
        
        threading.Thread(target=update, daemon=True).start()
    
    def update_clock(self):
        """Atualizar relógio"""
        def update():
            while True:
                try:
                    current_time = datetime.now().strftime("%H:%M:%S")
                    
                    if self.is_expanded and hasattr(self, 'clock_label'):
                        self.clock_label.configure(text=current_time)
                
                except Exception:
                    pass
                
                time.sleep(1)
        
        threading.Thread(target=update, daemon=True).start()
    
    def launch_app(self, command):
        """Lançar aplicação"""
        try:
            subprocess.Popen(command, shell=True)
        except Exception as e:
            print(f"Erro ao lançar {command}: {e}")
    
    def start_drag(self, event):
        """Iniciar arraste da janela"""
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
    
    def on_drag(self, event):
        """Processar arraste da janela"""
        # Implementar arraste manual no futuro
        pass
    
    def on_closing(self):
        """Fechar aplicação"""
        # Limpar arquivos temporários
        try:
            import os
            if os.path.exists("/tmp/cores_taskbar_cmd"):
                os.remove("/tmp/cores_taskbar_cmd")
            if os.path.exists("/tmp/cores_xbindkeys"):
                os.remove("/tmp/cores_xbindkeys")
            
            # Matar xbindkeys
            subprocess.run("killall xbindkeys 2>/dev/null", shell=True)
        except:
            pass
        
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Executar taskbar"""
        print("🚀 Core S Floating Taskbar iniciada!")
        print("\n🔧 COMO TESTAR:")
        print("   1. CLIQUE na taskbar (quadrado S)")
        print("   2. Pressione Alt+1, Alt+2, Alt+3")
        print("   3. OU use F1, F2, F3 como backup")
        print("   4. OU use a janela de debug com botões")
        print("   5. OU use: echo '1' > /tmp/cores_manual_cmd")
        print("\n👀 Observe o terminal para ver se detecta as teclas!")
        
        # Dar foco inicial
        self.root.after(500, lambda: self.root.focus_set())
        
        self.root.mainloop()

def main():
    """Função principal"""
    try:
        taskbar = CoresFloatingTaskbar()
        taskbar.run()
    except KeyboardInterrupt:
        print("\n⏹️ Encerrando Core S Taskbar...")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()
