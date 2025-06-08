#!/usr/bin/env python3
"""
Core S Floating Taskbar
Taskbar flutuante revolucionária para Core S System
"""

import tkinter as tk
import os
from tkinter import ttk
import subprocess
import threading
import time
import psutil
from datetime import datetime

class CoresFloatingTaskbar:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Core S Taskbar")
        
        # Configurações da janela
        self.root.overrideredirect(True)  # Remove borda da janela
        self.root.attributes('-topmost', True)  # Sempre no topo
        self.root.attributes('-alpha', 0.95)  # Leve transparência
        
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
        self.square_size = 70
        self.expanded_width = 400
        self.expanded_height = 30  # Menor que o quadrado
        self.margin = 20
        
        # Cores Core S
        self.bg_color = "#3F0808"
        self.accent_color = "#ffffff"
        self.secondary_color = "#2F0808"
        self.text_color = "#f0f6fc"
        
        # Configurar janela
        self.setup_window()
        
        # Criar interface
        self.create_square_interface()
        
        # Posicionar inicial
        self.position_taskbar()
        
        # Configurar atalhos globais
        self.setup_hotkeys()
        
        # Iniciar threads de monitoramento
        self.start_monitoring()
        
        # Variáveis para animação
        self.animation_running = False
    
    def setup_window(self):
        """Configurar janela principal"""
        self.root.configure(bg=self.bg_color)
        
        # Configurar protocolo de fechamento
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Bind para arrastar (futuro)
        self.root.bind('<Button-1>', self.start_drag)
        self.root.bind('<B1-Motion>', self.on_drag)
    
    def create_square_interface(self):
        """Criar interface do quadrado recolhido"""
        # Frame principal do quadrado
        self.square_frame = tk.Frame(
            self.root,
            width=self.square_size,
            height=self.square_size,
            bg=self.bg_color,
            relief='raised',
            bd=0
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
        
        # Indicador de posição (pequeno ponto)
        self.position_indicator = tk.Label(
            self.square_frame,
            text="●",
            font=("Arial", 8),
            fg=self.accent_color,
            bg=self.bg_color
        )
        self.position_indicator.place(x=45, y=45)
    
    def create_expanded_interface(self):
        """Criar interface expandida"""
        # Limpar frame atual
        for widget in self.square_frame.winfo_children():
            widget.destroy()
        
        # Redimensionar para expansão
        self.square_frame.configure(
            width=self.expanded_width,
            height=self.square_size
        )
        
        # Frame do quadrado S (esquerda)
        self.s_section = tk.Frame(
            self.square_frame,
            width=self.square_size,
            height=self.square_size,
            bg=self.bg_color,
            relief='raised',
            bd=0
        )
        self.s_section.pack(side=tk.LEFT, fill=tk.Y)
        self.s_section.pack_propagate(False)
        
        # Label S
        self.s_label = tk.Label(
            self.s_section,
            text="S",
            font=("Ubuntu", 24, "bold"),
            fg=self.accent_color,
            bg=self.bg_color
        )
        self.s_label.pack(expand=True)
        
        # Frame expandido (direita) - menor altura
        self.expanded_section = tk.Frame(
            self.square_frame,
            width=self.expanded_width - self.square_size,
            height=self.expanded_height,
            bg=self.secondary_color,
            relief='raised',
            bd=0
        )
        self.expanded_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(2, 0))
        self.expanded_section.pack_propagate(False)
        
        # Conteúdo da expansão
        self.create_expanded_content()
    
    def create_expanded_content(self):
        """Criar conteúdo da parte expandida"""
        # Frame superior (informações do sistema)
        top_frame = tk.Frame(self.expanded_section, bg=self.secondary_color, height=20)
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
        bottom_frame = tk.Frame(self.expanded_section, bg=self.secondary_color)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # Botões de aplicações
        self.create_app_buttons(bottom_frame)
    
    def create_app_buttons(self, parent):
        """Criar botões das aplicações"""
        apps = [
            ("📁", "Files", "thunar"),
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
    
    def position_taskbar(self):
        """Posicionar taskbar no canto atual"""
        # Obter dimensões da tela
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calcular posições baseado no canto atual
        corner = self.corners[self.current_corner]
        
        if corner == 'bottom_left':
            x = self.margin
            y = screen_height - self.square_size - self.margin
        elif corner == 'top_left':
            x = self.margin
            y = self.margin
        elif corner == 'top_right':
            x = screen_width - self.square_size - self.margin
            y = self.margin
        elif corner == 'bottom_right':
            x = screen_width - self.square_size - self.margin
            y = screen_height - self.square_size - self.margin
        
        # Se expandido, ajustar posição para expansão
        if self.is_expanded:
            if corner in ['top_left', 'bottom_left']:
                # Não precisa ajustar X, expansão vai para direita
                pass
        
        # Atualizar geometria da janela
        if self.is_expanded and corner in ['top_left', 'bottom_left']:
            self.root.geometry(f"{self.expanded_width}x{self.square_size}+{x}+{y}")
        else:
            self.root.geometry(f"{self.square_size}x{self.square_size}+{x}+{y}")
    
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
            steps = 10
            start_width = self.square_size
            end_width = self.expanded_width
            step_size = (end_width - start_width) / steps
            
            for i in range(steps + 1):
                current_width = int(start_width + (step_size * i))
                
                # Atualizar geometria
                screen_height = self.root.winfo_screenheight()
                corner = self.corners[self.current_corner]
                
                if corner == 'bottom_left':
                    y = screen_height - self.square_size - self.margin
                else:  # top_left
                    y = self.margin
                
                self.root.geometry(f"{current_width}x{self.square_size}+{self.margin}+{y}")
                self.root.update()
                time.sleep(0.02)
            
            # Criar interface expandida
            self.create_expanded_interface()
            self.is_expanded = True
            self.animation_running = False
        
        threading.Thread(target=animate_expand, daemon=True).start()
    
    def collapse_taskbar(self):
        """Recolher taskbar com animação"""
        def animate_collapse():
            # Voltar para interface quadrada
            self.create_square_interface()
            
            steps = 10
            start_width = self.expanded_width
            end_width = self.square_size
            step_size = (start_width - end_width) / steps
            
            for i in range(steps + 1):
                current_width = int(start_width - (step_size * i))
                
                # Atualizar geometria
                screen_height = self.root.winfo_screenheight()
                corner = self.corners[self.current_corner]
                
                if corner == 'bottom_left':
                    y = screen_height - self.square_size - self.margin
                else:  # top_left
                    y = self.margin
                
                self.root.geometry(f"{current_width}x{self.square_size}+{self.margin}+{y}")
                self.root.update()
                time.sleep(0.02)
            
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
            self.root.after(300, self._complete_corner_move)
        else:
            self._complete_corner_move()
    
    def _complete_corner_move(self):
        """Completar movimento de canto"""
        self.current_corner = (self.current_corner + 1) % 4
        self.position_taskbar()
        
        # Atualizar indicador de posição
        corner_indicators = ["◣", "◤", "◥", "◢"]
        if hasattr(self, 'position_indicator'):
            self.position_indicator.configure(text=corner_indicators[self.current_corner])
    
    def toggle_visibility(self):
        """Alternar visibilidade completa"""
        try:
            if self.is_visible:
                print("🙈 Ocultando taskbar...")
                self.root.withdraw()  # Ocultar
                self.is_visible = False
            else:
                print("👁️ Exibindo taskbar...")
                self.root.deiconify()  # Exibir
                self.root.lift()  # Trazer para frente
                self.root.attributes('-topmost', True)  # Garantir que fique no topo
                self.is_visible = True
                
                # Reposicionar após exibir
                self.position_taskbar()
        
        except Exception as e:
            print(f"Erro ao alternar visibilidade: {e}")
    
    def setup_hotkeys(self):
        """Configurar atalhos de teclado globais"""
        import threading
        import subprocess
        import os
        
        # Criar arquivo temporário para comunicação
        self.hotkey_file = "/tmp/cores_taskbar_hotkeys"
        
        # Iniciar daemon de atalhos globais
        self.start_global_hotkey_daemon()
        
        # Também manter binds locais para quando a janela estiver visível
        self.root.bind_all('<Alt-Key-1>', lambda e: self.toggle_expansion())
        self.root.bind_all('<Alt-Key-2>', lambda e: self.move_to_next_corner())
        self.root.bind_all('<Alt-Key-3>', lambda e: self.toggle_visibility())
    
    def start_global_hotkey_daemon(self):
        """Iniciar daemon para capturar atalhos globais"""
        def hotkey_daemon():
            import time
            import subprocess
            
            # Criar script temporário para xbindkeys
            xbindkeys_config = """
"echo 'toggle_expansion' > /tmp/cores_taskbar_cmd"
    Alt + 1

"echo 'move_corner' > /tmp/cores_taskbar_cmd"
    Alt + 2

"echo 'toggle_visibility' > /tmp/cores_taskbar_cmd"
    Alt + 3
"""
            
            # Salvar configuração
            with open("/tmp/cores_xbindkeys", "w") as f:
                f.write(xbindkeys_config)
            
            try:
                # Matar xbindkeys existente
                subprocess.run("killall xbindkeys 2>/dev/null", shell=True)
                
                # Iniciar xbindkeys
                subprocess.Popen(["xbindkeys", "-f", "/tmp/cores_xbindkeys"], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Monitor de comandos
                while True:
                    try:
                        if os.path.exists("/tmp/cores_taskbar_cmd"):
                            with open("/tmp/cores_taskbar_cmd", "r") as f:
                                cmd = f.read().strip()
                            
                            os.remove("/tmp/cores_taskbar_cmd")
                            
                            # Executar comando correspondente
                            if cmd == "toggle_expansion":
                                self.root.after(0, self.toggle_expansion)
                            elif cmd == "move_corner":
                                self.root.after(0, self.move_to_next_corner)
                            elif cmd == "toggle_visibility":
                                self.root.after(0, self.toggle_visibility)
                    
                    except Exception:
                        pass
                    
                    time.sleep(0.1)
            
            except Exception as e:
                print(f"Erro no daemon de atalhos: {e}")
                # Fallback: usar método alternativo
                self.setup_fallback_hotkeys()
        
        threading.Thread(target=hotkey_daemon, daemon=True).start()
    
    def setup_fallback_hotkeys(self):
        """Método alternativo para atalhos globais"""
        def check_hotkeys():
            import time
            import subprocess
            
            while True:
                try:
                    # Verificar se Alt+3 foi pressionado via xdotool
                    result = subprocess.run(
                        "timeout 0.1 xev -root | grep -c 'keycode 11.*state 0x8'",
                        shell=True, capture_output=True, text=True
                    )
                    
                    if result.stdout.strip() and int(result.stdout.strip()) > 0:
                        self.root.after(0, self.toggle_visibility)
                
                except Exception:
                    pass
                
                time.sleep(0.2)
        
        threading.Thread(target=check_hotkeys, daemon=True).start()
    
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
        print("⌨️ Atalhos:")
        print("   Alt+1: Expandir/Recolher (só cantos esquerdos)")
        print("   Alt+2: Mover entre cantos")
        print("   Alt+3: Ocultar/Exibir")
        
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
    os.system("python3 /opt/cores-system/scripts/manager.py &")
    main()
