#!/usr/bin/env python3
"""
Core S Floating Taskbar - VERSÃO OTIMIZADA
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
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.95)
        
        # Estados da taskbar
        self.is_expanded = False
        self.is_visible = True
        self.current_corner = 0
        self.corners = ['bottom_left', 'top_left', 'top_right', 'bottom_right']
        
        # Dimensões
        self.square_size = 70
        self.expanded_width = 400
        self.expanded_height = 30
        self.margin = 20
        
        # Cores Core S
        self.bg_color = "#3F0808"
        self.accent_color = "#ffffff"
        self.secondary_color = "#2F0808"
        self.text_color = "#f0f6fc"
        
        # Controle de recursos - OTIMIZAÇÃO
        self.update_running = False
        self.clock_running = False
        self.system_running = False
        self.hotkey_running = False
        
        # Cache para evitar atualizações desnecessárias
        self.last_time = ""
        self.last_cpu = 0
        self.last_ram = 0
        
        # Configurar janela
        self.setup_window()
        
        # Criar interface
        self.create_square_interface()
        
        # Posicionar inicial
        self.position_taskbar()
        
        # Configurar atalhos globais
        self.setup_hotkeys()
        
        # Iniciar monitoramento otimizado
        self.start_monitoring()
        
        # Variáveis para animação
        self.animation_running = False
    
    def setup_window(self):
        """Configurar janela principal"""
        self.root.configure(bg=self.bg_color)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind('<Button-1>', self.start_drag)
        self.root.bind('<B1-Motion>', self.on_drag)
    
    def create_square_interface(self):
        """Criar interface do quadrado recolhido"""
        # Limpar frame se existir
        if hasattr(self, 'square_frame'):
            self.square_frame.destroy()
        
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
        corner_indicators = ["◣", "◤", "◥", "◢"]
        self.position_indicator = tk.Label(
            self.square_frame,
            text=corner_indicators[self.current_corner],
            font=("Arial", 8),
            fg=self.accent_color,
            bg=self.bg_color
        )
        self.position_indicator.place(x=45, y=45)
        
        # Limpar referências de widgets expandidos
        self.clear_expanded_refs()
    
    def clear_expanded_refs(self):
        """Limpar referências de widgets expandidos para liberar memória"""
        self.clock_label = None
        self.system_label = None
        self.expanded_section = None
        self.s_section = None
    
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
        
        # Frame expandido (direita)
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
            text=self.last_time if self.last_time else "00:00:00",
            font=("Ubuntu Mono", 9, "bold"),
            fg=self.text_color,
            bg=self.secondary_color
        )
        self.clock_label.pack(side=tk.RIGHT)
        
        # CPU/RAM
        self.system_label = tk.Label(
            top_frame,
            text=f"CPU: {self.last_cpu:.0f}% | RAM: {self.last_ram:.0f}%",
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
                command=lambda cmd=command: self.launch_app_safe(cmd)
            )
            btn.pack(side=tk.LEFT, padx=1)
            
            # Hover effects
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=self.accent_color))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg=self.bg_color))
    
    def launch_app_safe(self, command):
        """Lançar aplicação de forma segura sem travar a GUI"""
        def launch_in_thread():
            try:
                # Usar Popen com DEVNULL para não bloquear
                subprocess.Popen(
                    command, 
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL
                )
                print(f"✅ Aplicativo {command} iniciado")
            except Exception as e:
                print(f"❌ Erro ao lançar {command}: {e}")
        
        # Executar em thread separada para não travar GUI
        threading.Thread(target=launch_in_thread, daemon=True).start()
    
    def position_taskbar(self):
        """Posicionar taskbar no canto atual"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
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
        
        # Atualizar geometria da janela
        if self.is_expanded and corner in ['top_left', 'bottom_left']:
            self.root.geometry(f"{self.expanded_width}x{self.square_size}+{x}+{y}")
        else:
            self.root.geometry(f"{self.square_size}x{self.square_size}+{x}+{y}")
    
    def toggle_expansion(self):
        """Alternar entre expandido e recolhido"""
        if self.animation_running:
            return
        
        corner = self.corners[self.current_corner]
        if corner not in ['top_left', 'bottom_left']:
            return
        
        self.animation_running = True
        
        if self.is_expanded:
            self.collapse_taskbar()
        else:
            self.expand_taskbar()
    
    def expand_taskbar(self):
        """Expandir taskbar com animação otimizada"""
        def animate_expand():
            steps = 8  # Reduzido para melhor performance
            start_width = self.square_size
            end_width = self.expanded_width
            step_size = (end_width - start_width) / steps
            
            for i in range(steps + 1):
                current_width = int(start_width + (step_size * i))
                
                screen_height = self.root.winfo_screenheight()
                corner = self.corners[self.current_corner]
                
                if corner == 'bottom_left':
                    y = screen_height - self.square_size - self.margin
                else:
                    y = self.margin
                
                self.root.geometry(f"{current_width}x{self.square_size}+{self.margin}+{y}")
                self.root.update_idletasks()  # Mais eficiente que update()
                time.sleep(0.025)
            
            self.create_expanded_interface()
            self.is_expanded = True
            self.animation_running = False
        
        threading.Thread(target=animate_expand, daemon=True).start()
    
    def collapse_taskbar(self):
        """Recolher taskbar com animação otimizada"""
        def animate_collapse():
            self.create_square_interface()
            
            steps = 8  # Reduzido para melhor performance
            start_width = self.expanded_width
            end_width = self.square_size
            step_size = (start_width - end_width) / steps
            
            for i in range(steps + 1):
                current_width = int(start_width - (step_size * i))
                
                screen_height = self.root.winfo_screenheight()
                corner = self.corners[self.current_corner]
                
                if corner == 'bottom_left':
                    y = screen_height - self.square_size - self.margin
                else:
                    y = self.margin
                
                self.root.geometry(f"{current_width}x{self.square_size}+{self.margin}+{y}")
                self.root.update_idletasks()
                time.sleep(0.025)
            
            self.is_expanded = False
            self.animation_running = False
        
        threading.Thread(target=animate_collapse, daemon=True).start()
    
    def move_to_next_corner(self):
        """Mover para próximo canto"""
        if self.animation_running:
            return
        
        if self.is_expanded:
            self.collapse_taskbar()
            self.root.after(300, self._complete_corner_move)
        else:
            self._complete_corner_move()
    
    def _complete_corner_move(self):
        """Completar movimento de canto"""
        self.current_corner = (self.current_corner + 1) % 4
        self.position_taskbar()
        
        # Atualizar indicador de posição
        corner_indicators = ["◣", "◤", "◥", "◢"]
        if hasattr(self, 'position_indicator') and self.position_indicator:
            self.position_indicator.configure(text=corner_indicators[self.current_corner])
    
    def toggle_visibility(self):
        """Alternar visibilidade completa"""
        try:
            if self.is_visible:
                print("🙈 Ocultando taskbar...")
                self.root.withdraw()
                self.is_visible = False
            else:
                print("👁️ Exibindo taskbar...")
                self.root.deiconify()
                self.root.lift()
                self.root.attributes('-topmost', True)
                self.is_visible = True
                self.position_taskbar()
        except Exception as e:
            print(f"Erro ao alternar visibilidade: {e}")
    
    def setup_hotkeys(self):
        """Configurar atalhos de teclado globais otimizado"""
        if self.hotkey_running:
            return
        
        self.hotkey_running = True
        self.start_global_hotkey_daemon()
        
        # Binds locais otimizados
        self.root.bind_all('<Alt-Key-1>', lambda e: self.toggle_expansion())
        self.root.bind_all('<Alt-Key-2>', lambda e: self.move_to_next_corner())
        self.root.bind_all('<Alt-Key-3>', lambda e: self.toggle_visibility())
    
    def start_global_hotkey_daemon(self):
        """Daemon otimizado para atalhos globais"""
        def hotkey_daemon():
            xbindkeys_config = """
"echo 'toggle_expansion' > /tmp/cores_taskbar_cmd"
    Alt + 1

"echo 'move_corner' > /tmp/cores_taskbar_cmd"
    Alt + 2

"echo 'toggle_visibility' > /tmp/cores_taskbar_cmd"
    Alt + 3
"""
            
            try:
                with open("/tmp/cores_xbindkeys", "w") as f:
                    f.write(xbindkeys_config)
                
                subprocess.run("killall xbindkeys 2>/dev/null", shell=True)
                subprocess.Popen(
                    ["xbindkeys", "-f", "/tmp/cores_xbindkeys"], 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
                
                while self.hotkey_running:
                    try:
                        if os.path.exists("/tmp/cores_taskbar_cmd"):
                            with open("/tmp/cores_taskbar_cmd", "r") as f:
                                cmd = f.read().strip()
                            
                            os.remove("/tmp/cores_taskbar_cmd")
                            
                            if cmd == "toggle_expansion":
                                self.root.after_idle(self.toggle_expansion)
                            elif cmd == "move_corner":
                                self.root.after_idle(self.move_to_next_corner)
                            elif cmd == "toggle_visibility":
                                self.root.after_idle(self.toggle_visibility)
                    
                    except Exception:
                        pass
                    
                    time.sleep(0.2)  # Aumentado para economizar CPU
            
            except Exception as e:
                print(f"Erro no daemon de atalhos: {e}")
        
        threading.Thread(target=hotkey_daemon, daemon=True).start()
    
    def start_monitoring(self):
        """Iniciar monitoramento otimizado do sistema"""
        if not self.update_running:
            self.update_running = True
            self.start_optimized_updates()
    
    def start_optimized_updates(self):
        """Sistema de atualizações otimizado usando tkinter.after"""
        def update_system_safe():
            if not self.update_running:
                return
            
            try:
                # Só atualizar se expandido e widgets existem
                if self.is_expanded and self.system_label and self.clock_label:
                    
                    # Atualizar hora (mais frequente)
                    current_time = datetime.now().strftime("%H:%M:%S")
                    if current_time != self.last_time:
                        self.last_time = current_time
                        if self.clock_label.winfo_exists():
                            self.clock_label.configure(text=current_time)
                    
                    # Atualizar sistema (menos frequente) - só a cada 3 segundos
                    current_seconds = int(time.time())
                    if current_seconds % 3 == 0:
                        try:
                            cpu_percent = psutil.cpu_percent(interval=None)  # Non-blocking
                            memory = psutil.virtual_memory()
                            ram_percent = memory.percent
                            
                            # Só atualizar se mudou significativamente
                            if (abs(cpu_percent - self.last_cpu) > 1 or 
                                abs(ram_percent - self.last_ram) > 1):
                                
                                self.last_cpu = cpu_percent
                                self.last_ram = ram_percent
                                
                                if self.system_label and self.system_label.winfo_exists():
                                    info_text = f"CPU: {cpu_percent:.0f}% | RAM: {ram_percent:.0f}%"
                                    self.system_label.configure(text=info_text)
                        
                        except Exception:
                            pass
                
                else:
                    # Se não expandido, só atualizar cache
                    current_time = datetime.now().strftime("%H:%M:%S")
                    self.last_time = current_time
                    
                    try:
                        self.last_cpu = psutil.cpu_percent(interval=None)
                        self.last_ram = psutil.virtual_memory().percent
                    except Exception:
                        pass
                        
            except Exception:
                pass
            
            # Reagendar próxima atualização
            if self.update_running:
                self.root.after(1000, update_system_safe)
        
        # Iniciar ciclo de atualizações
        self.root.after(100, update_system_safe)
    
    def start_drag(self, event):
        """Iniciar arraste da janela"""
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
    
    def on_drag(self, event):
        """Processar arraste da janela"""
        pass  # Implementação futura
    
    def on_closing(self):
        """Fechar aplicação liberando recursos"""
        print("🔄 Encerrando Core S Taskbar...")
        
        # Parar todos os threads
        self.update_running = False
        self.hotkey_running = False
        
        # Limpar arquivos temporários
        try:
            files_to_clean = [
                "/tmp/cores_taskbar_cmd",
                "/tmp/cores_xbindkeys"
            ]
            for file in files_to_clean:
                if os.path.exists(file):
                    os.remove(file)
            
            subprocess.run("killall xbindkeys 2>/dev/null", shell=True)
        except Exception:
            pass
        
        # Destruir janela
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass
    
    def run(self):
        """Executar taskbar"""
        print("🚀 Core S Floating Taskbar iniciada!")
        print("⌨️ Atalhos:")
        print("   Alt+1: Expandir/Recolher (só cantos esquerdos)")
        print("   Alt+2: Mover entre cantos")
        print("   Alt+3: Ocultar/Exibir")
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()

def main():
    """Função principal otimizada"""
    try:
        # Verificar se manager.py já está rodando
        result = subprocess.run("pgrep -f manager.py", shell=True, capture_output=True)
        if not result.stdout:
            # Só iniciar se não estiver rodando
            subprocess.Popen("python3 /opt/cores-system/scripts/manager.py", 
                           shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        taskbar = CoresFloatingTaskbar()
        taskbar.run()
    except KeyboardInterrupt:
        print("\n⏹️ Encerrando Core S Taskbar...")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    os.system('python3 /opt/cores-system/scripts/manager.py &')
    main()
