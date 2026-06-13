import customtkinter as ctk
from tkinter import ttk
import serial  # Requiere: pip install pyserial
import threading
import time

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AppGrabadorIntervalos(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("HMI Industrial - Control de Brazo Robótico")
        
        self.geometry("1150x710") 
        
        self.resizable(True, True) 
        
        self.arduino = None
        self.puerto_serial = 'COM6'  # Cambiar según corresponda
        self.receta_movimientos = []
        self.contador_pasos = 0
        self.reproduciendo = False
        self.indice_reproduccion = 0

        self.crear_interfaz()

        threading.Thread(target=self.conectar_serial_asincrono, daemon=True).start()

        self.escuchar_esp32()

    def crear_interfaz(self):
        # Configurar la ventana principal para que sea responsiva al ampliarse
        self.grid_columnconfigure(0, weight=1)  # Columna izquierda (Mandos)
        self.grid_columnconfigure(1, weight=1)  # Columna derecha (Tabla)
        self.grid_rowconfigure(0, weight=1)

        # ---------------------------------------------------------------------
        # CONTENEDOR PRINCIPAL CONTROL DE SERVOS
        # ---------------------------------------------------------------------
        self.frame_izquierdo = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_izquierdo.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        
        # Hacer que los elementos internos del frame izquierdo también puedan expandirse verticalmente
        self.frame_izquierdo.grid_rowconfigure(2, weight=1) # El bloque de sliders tendrá prioridad de expansión
        
        self.lbl_titulo = ctk.CTkLabel(self.frame_izquierdo, text="TELEMETRÍA DE MOTORES", font=("Arial", 14, "bold"))
        self.lbl_titulo.pack(pady=(0, 10), fill="x")
        
        # Sub-contenedor principal para los Sliders (Recuadro Negro)
        self.grid_motores = ctk.CTkFrame(self.frame_izquierdo, fg_color="#1e1e1e", border_width=1, border_color="#2d2d2d")
        self.grid_motores.pack(fill="both", expand=True, pady=(0, 20), ipady=20) 
        
        # Configurar pesos de las columnas y filas del grid de sliders para que se adapten al estirar
        self.grid_motores.grid_columnconfigure(0, weight=1)
        self.grid_motores.grid_columnconfigure(1, weight=1)
        for i in range(4):
            self.grid_motores.grid_rowconfigure(i, weight=1)
        
        # --- COLUMNA 1 ---
        # Motor 1
        self.frame_m1 = ctk.CTkFrame(self.grid_motores, fg_color="transparent")
        self.frame_m1.grid(row=0, column=0, padx=25, pady=12, sticky="ew")
        self.lbl_m1 = ctk.CTkLabel(self.frame_m1, text="Motor 1 (Base): 90.0°  [350]", font=("Arial", 11), text_color="white")
        self.lbl_m1.pack(anchor="w")
        self.slider_m1 = ctk.CTkSlider(self.frame_m1, from_=150, to=600, height=14, command=lambda v: self.actualizar_label(1, v))
        self.slider_m1.pack(fill="x", pady=2)
        self.slider_m1.set(350)

        # Motor 2
        self.frame_m2 = ctk.CTkFrame(self.grid_motores, fg_color="transparent")
        self.frame_m2.grid(row=1, column=0, padx=25, pady=12, sticky="ew")
        self.lbl_m2 = ctk.CTkLabel(self.frame_m2, text="Motor 2 (Codo A): 90.0°  [350]", font=("Arial", 11), text_color="white")
        self.lbl_m2.pack(anchor="w")
        self.slider_m2 = ctk.CTkSlider(self.frame_m2, from_=150, to=600, height=14, command=self.control_codo_espejo)
        self.slider_m2.pack(fill="x", pady=2)
        self.slider_m2.set(350)

        # Motor 3
        self.frame_m3 = ctk.CTkFrame(self.grid_motores, fg_color="transparent")
        self.frame_m3.grid(row=2, column=0, padx=25, pady=12, sticky="ew")
        self.lbl_m3 = ctk.CTkLabel(self.frame_m3, text="Motor 3 (Codo B): 90.0°  [350]", font=("Arial", 11), text_color="#aaaaaa")
        self.lbl_m3.pack(anchor="w")
        self.slider_m3 = ctk.CTkSlider(self.frame_m3, from_=150, to=600, height=14, state="disabled")
        self.slider_m3.pack(fill="x", pady=2)
        self.slider_m3.set(350)

        # Motor 4
        self.frame_m4 = ctk.CTkFrame(self.grid_motores, fg_color="transparent")
        self.frame_m4.grid(row=3, column=0, padx=25, pady=12, sticky="ew")
        self.lbl_m4 = ctk.CTkLabel(self.frame_m4, text="Motor 4: 90.0°  [350]", font=("Arial", 11), text_color="white")
        self.lbl_m4.pack(anchor="w")
        self.slider_m4 = ctk.CTkSlider(self.frame_m4, from_=150, to=600, height=14, command=lambda v: self.actualizar_label(4, v))
        self.slider_m4.pack(fill="x", pady=2)
        self.slider_m4.set(350)

        # --- COLUMNA 2 ---
        # Motor 5
        self.frame_m5 = ctk.CTkFrame(self.grid_motores, fg_color="transparent")
        self.frame_m5.grid(row=0, column=1, padx=25, pady=12, sticky="ew")
        self.lbl_m5 = ctk.CTkLabel(self.frame_m5, text="Motor 5: 90.0°  [350]", font=("Arial", 11), text_color="white")
        self.lbl_m5.pack(anchor="w")
        self.slider_m5 = ctk.CTkSlider(self.frame_m5, from_=150, to=600, height=14, command=lambda v: self.actualizar_label(5, v))
        self.slider_m5.pack(fill="x", pady=2)
        self.slider_m5.set(350)

        # Motor 6
        self.frame_m6 = ctk.CTkFrame(self.grid_motores, fg_color="transparent")
        self.frame_m6.grid(row=1, column=1, padx=25, pady=12, sticky="ew")
        self.lbl_m6 = ctk.CTkLabel(self.frame_m6, text="Motor 6: 90.0°  [350]", font=("Arial", 11), text_color="white")
        self.lbl_m6.pack(anchor="w")
        self.slider_m6 = ctk.CTkSlider(self.frame_m6, from_=150, to=600, height=14, command=lambda v: self.actualizar_label(6, v))
        self.slider_m6.pack(fill="x", pady=2)
        self.slider_m6.set(350)

        # Motor 7
        self.frame_m7 = ctk.CTkFrame(self.grid_motores, fg_color="transparent")
        self.frame_m7.grid(row=2, column=1, padx=25, pady=12, sticky="ew")
        self.lbl_m7 = ctk.CTkLabel(self.frame_m7, text="Motor 7 (Terminal): 90.0°  [350]", font=("Arial", 11), text_color="white")
        self.lbl_m7.pack(anchor="w")
        self.slider_m7 = ctk.CTkSlider(self.frame_m7, from_=150, to=600, height=14, command=lambda v: self.actualizar_label(7, v))
        self.slider_m7.pack(fill="x", pady=2)
        self.slider_m7.set(350)

        # Actuador Digital (Ventosa)
        self.frame_switch = ctk.CTkFrame(self.grid_motores, fg_color="transparent")
        self.frame_switch.grid(row=3, column=1, padx=25, pady=12, sticky="nsew")
        self.estado_ventosa = ctk.StringVar(value="OFF")
        self.switch_ventosa = ctk.CTkSwitch(self.frame_switch, text="Activar Ventosa", 
                                            variable=self.estado_ventosa, onvalue="ON", offvalue="OFF",
                                            font=("Arial", 11, "bold"), text_color="white", command=self.interrupcion_bomba_manual)
        self.switch_ventosa.pack(expand=True)

        # ---------------------------------------------------------------------
        # Botón Adicionar Movimiento
        self.btn_grabar = ctk.CTkButton(self.frame_izquierdo, text="➕ Adicionar Movimiento a la Receta", 
                                         fg_color="#008000", hover_color="#006400",
                                         height=40, font=("Arial", 12, "bold"),
                                         command=self.adicionar_movimiento)
        self.btn_grabar.pack(pady=(0, 20), fill="x")

        # Recuadro de Configuración de Loop
        self.frame_intervalo = ctk.CTkFrame(self.frame_izquierdo, fg_color="#232323", border_width=1, border_color="#1f538d")
        self.frame_intervalo.pack(pady=(0, 20), fill="x")
        
        self.lbl_int_titulo = ctk.CTkLabel(self.frame_intervalo, text="⚙️ CONFIGURACIÓN DE LOOP:", font=("Arial", 11, "bold"), text_color="#5ea2e6")
        self.lbl_int_titulo.pack(pady=(14, 4), anchor="center")
        
        self.subframe_inputs = ctk.CTkFrame(self.frame_intervalo, fg_color="transparent")
        self.subframe_inputs.pack(pady=(4, 14), anchor="center")
        
        self.lbl_desde = ctk.CTkLabel(self.subframe_inputs, text="Desde:", font=("Arial", 11), text_color="white")
        self.lbl_desde.grid(row=0, column=0, padx=(5, 2), sticky="w")
        
        self.entry_desde = ctk.CTkEntry(self.subframe_inputs, width=50, height=26, justify="center", font=("Arial", 11, "bold"))
        self.entry_desde.insert(0, "0")
        self.entry_desde.grid(row=0, column=1, padx=(2, 12))
        
        self.lbl_hasta = ctk.CTkLabel(self.subframe_inputs, text="Hasta:", font=("Arial", 11), text_color="white")
        self.lbl_hasta.grid(row=0, column=2, padx=(12, 2), sticky="w")
        
        self.entry_hasta = ctk.CTkEntry(self.subframe_inputs, width=50, height=26, justify="center", font=("Arial", 11, "bold"))
        self.entry_hasta.insert(0, "0")
        self.entry_hasta.grid(row=0, column=3, padx=(2, 5))

        # Botones de control operativo (Play / Stop)
        self.frame_botones_control = ctk.CTkFrame(self.frame_izquierdo, fg_color="transparent")
        self.frame_botones_control.pack(pady=(0, 15), fill="x")
        self.frame_botones_control.grid_columnconfigure((0, 1), weight=1)

        self.btn_play = ctk.CTkButton(self.frame_botones_control, text="▶ Reproducir Loop", fg_color="#1f538d", hover_color="#14375e", height=40, font=("Arial", 12, "bold"), command=self.iniciar_reproduccion)
        self.btn_play.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.btn_stop = ctk.CTkButton(self.frame_botones_control, text="⏹ Detener", fg_color="#d32f2f", hover_color="#b71c1c", height=40, font=("Arial", 12, "bold"), command=self.detener_reproduccion, state="disabled")
        self.btn_stop.grid(row=0, column=1, padx=(6, 0), sticky="ew")

        # Mensajería operativa de estado
        self.lbl_estado_op = ctk.CTkLabel(self.frame_izquierdo, text="Estado: INICIALIZANDO INTERFAZ...", text_color="#ffcc00", font=("Arial", 12, "bold"))
        self.lbl_estado_op.pack(pady=(5, 0), fill="x")

        # ---------------------------------------------------------------------
        # PANEL DERECHO: TABLA DE DATOS
        # ---------------------------------------------------------------------
        self.frame_tabla = ctk.CTkFrame(self)
        self.frame_tabla.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        
        columnas = ("paso", "m1", "m2", "m3", "m4", "m5", "m6", "m7", "ventosa")
        
        self.tabla_scroll = ttk.Scrollbar(self.frame_tabla)
        self.tabla_scroll.pack(side="right", fill="y")
        
        self.tabla = ttk.Treeview(self.frame_tabla, columns=columnas, show="headings", yscrollcommand=self.tabla_scroll.set)
        self.tabla_scroll.config(command=self.tabla.yview)
        
        self.tabla.heading("paso", text="Mov.")
        self.tabla.heading("m1", text="M1 (Base)")
        self.tabla.heading("m2", text="M2")
        self.tabla.heading("m3", text="M3 (Esp)")
        self.tabla.heading("m4", text="M4")
        self.tabla.heading("m5", text="M5")
        self.tabla.heading("m6", text="M6")
        self.tabla.heading("m7", text="M7")
        self.tabla.heading("ventosa", text="Ventosa")
        
        anchos = {"paso": 45, "m1": 70, "m2": 60, "m3": 60, "m4": 55, "m5": 55, "m6": 55, "m7": 60, "ventosa": 70}
        for col in columnas:
            self.tabla.column(col, width=anchos[col], anchor="center", minwidth=45)
            
        self.tabla.pack(fill="both", expand=True, padx=5, pady=5)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2a2a2a", fieldbackground="#2a2a2a", foreground="white", rowheight=24)
        style.map("Treeview", background=[("selected", "#1f538d")])

    # ---- CONEXIÓN ASÍNCRONA SEGURA ----
    def conectar_serial_asincrono(self):
        try:
            self.arduino = serial.Serial(self.puerto_serial, 115200, timeout=0.1)
            time.sleep(1) 
            self.lbl_estado_op.configure(text="Estado: CONECTADO (MODO MANUAL)", text_color="#4caf50")
            print("[SERIAL] Puerto abierto con éxito.")
        except Exception as e:
            self.lbl_estado_op.configure(text="Estado: MODO SIMULACIÓN (SIN HARDWARE)", text_color="#ffcc00")
            print(f"[ALERTA] No se detectó hardware en {self.puerto_serial}. Arrancando simulación.")
            self.arduino = None

    # ---- MÉTODOS DE CONVERSIÓN Y LÓGICA DE CONTROL ----
    def adc_a_grados(self, valor_adc):
        return ((valor_adc - 150) * 180.0) / (600 - 150)

    def enviar_trama_serial(self):
        if self.reproduciendo or not self.arduino:
            return 
        val_m1 = int(self.slider_m1.get())
        val_m2 = int(self.slider_m2.get())
        val_m3 = int(self.slider_m3.get()) 
        val_m4 = int(self.slider_m4.get())
        val_m5 = int(self.slider_m5.get())
        val_m6 = int(self.slider_m6.get())
        val_m7 = int(self.slider_m7.get())
        bomba_num = 1 if self.estado_ventosa.get() == "ON" else 0
        
        trama = f"{val_m1},{val_m2},{val_m3},{val_m4},{val_m5},{val_m6},{val_m7},{bomba_num}\n"
        try: 
            self.arduino.write(trama.encode('utf-8'))
        except Exception as e: 
            print(f"Error en envío manual: {e}")

    def interrupcion_bomba_manual(self):
        self.enviar_trama_serial()

    def control_codo_espejo(self, valor):
        val_m2 = int(float(valor))
        val_m3 = 150 + (600 - val_m2) 
        self.slider_m3.set(val_m3)
        self.lbl_m2.configure(text=f"Motor 2 (Codo A): {self.adc_a_grados(val_m2):.1f}°  [{val_m2}]")
        self.lbl_m3.configure(text=f"Motor 3 (Codo B): {self.adc_a_grados(val_m3):.1f}°  [{val_m3}]")
        self.enviar_trama_serial()

    def actualizar_label(self, num_motor, valor):
        val_entero = int(float(valor))
        grados = self.adc_a_grados(val_entero)
        if num_motor == 1: 
            self.lbl_m1.configure(text=f"Motor 1 (Base): {grados:.1f}°  [{val_entero}]")
        elif num_motor == 7: 
            self.lbl_m7.configure(text=f"Motor 7 (Terminal): {grados:.1f}°  [{val_entero}]")
        else: 
            getattr(self, f"lbl_m{num_motor}").configure(text=f"Motor {num_motor}: {grados:.1f}°  [{val_entero}]")
        self.enviar_trama_serial()

    def adicionar_movimiento(self):
        val_m1 = int(self.slider_m1.get())
        val_m2 = int(self.slider_m2.get())
        val_m3 = int(self.slider_m3.get()) 
        val_m4 = int(self.slider_m4.get())
        val_m5 = int(self.slider_m5.get())
        val_m6 = int(self.slider_m6.get())
        val_m7 = int(self.slider_m7.get())
        status_v = self.estado_ventosa.get()
        
        txt_m1 = f"{self.adc_a_grados(val_m1):.0f}°"
        txt_m2 = f"{self.adc_a_grados(val_m2):.0f}°"
        txt_m3 = f"{self.adc_a_grados(val_m3):.0f}°"
        txt_m4 = f"{self.adc_a_grados(val_m4):.0f}°"
        txt_m5 = f"{self.adc_a_grados(val_m5):.0f}°"
        txt_m6 = f"{self.adc_a_grados(val_m6):.0f}°"
        txt_m7 = f"{self.adc_a_grados(val_m7):.0f}°"
        
        self.tabla.insert("", "end", values=(self.contador_pasos, txt_m1, txt_m2, txt_m3, txt_m4, txt_m5, txt_m6, txt_m7, status_v))
        self.receta_movimientos.append({"m1": val_m1, "m2": val_m2, "m3": val_m3, "m4": val_m4, "m5": val_m5, "m6": val_m6, "m7": val_m7, "ventosa": status_v})
        self.entry_hasta.delete(0, "end")
        self.entry_hasta.insert(0, str(self.contador_pasos))
        self.contador_pasos += 1

    def iniciar_reproduccion(self):
        if not self.receta_movimientos:
            self.lbl_estado_op.configure(text="Error: No hay pasos grabados", text_color="#d32f2f")
            return
        try:
            self.limite_inicial = int(self.entry_desde.get())
            self.limite_final = int(self.entry_hasta.get())
            if self.limite_inicial < 0 or self.limite_final >= len(self.receta_movimientos) or self.limite_inicial > self.limite_final: 
                raise ValueError
        except ValueError:
            self.lbl_estado_op.configure(text="Error: Índices de secuencia fuera de rango", text_color="#d32f2f")
            return

        self.reproduciendo = True
        self.indice_reproduccion = self.limite_inicial
        self.btn_play.configure(state="disabled")
        self.btn_grabar.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.lbl_estado_op.configure(text=f"Ejecutando secuencia: Pasos {self.limite_inicial} al {self.limite_final}", text_color="#4caf50")
        self.bucle_secuencia()

    def bucle_secuencia(self):
        if not self.reproduciendo: 
            return
        paso_actual = self.receta_movimientos[self.indice_reproduccion]
        filas = self.tabla.get_children()
        if filas: 
            self.tabla.selection_set(filas[self.indice_reproduccion])
        
        self.slider_m1.set(paso_actual["m1"])
        self.slider_m2.set(paso_actual["m2"])
        self.slider_m3.set(paso_actual["m3"])
        self.slider_m4.set(paso_actual["m4"])
        self.slider_m5.set(paso_actual["m5"])
        self.slider_m6.set(paso_actual["m6"])
        self.slider_m7.set(paso_actual["m7"])
        self.estado_ventosa.set(paso_actual["ventosa"])
        
        self.actualizar_label(1, paso_actual["m1"])
        self.control_codo_espejo(paso_actual["m2"])
        self.actualizar_label(4, paso_actual["m4"])
        self.actualizar_label(5, paso_actual["m5"])
        self.actualizar_label(6, paso_actual["m6"])
        self.actualizar_label(7, paso_actual["m7"])

        bomba_num = 1 if paso_actual["ventosa"] == "ON" else 0
        trama = f"{paso_actual['m1']},{paso_actual['m2']},{paso_actual['m3']},{paso_actual['m4']},{paso_actual['m5']},{paso_actual['m6']},{paso_actual['m7']},{bomba_num}\n"
        print(f"TX Serial Secuencia -> {trama.strip()}")
        
        if self.arduino and self.arduino.is_open:
            try: 
                self.arduino.write(trama.encode('utf-8'))
            except Exception as e: 
                print(f"Error en Tx secuencial: {e}")

        self.indice_reproduccion += 1
        if self.indice_reproduccion > self.limite_final: 
            self.indice_reproduccion = self.limite_inicial
        self.after(2500, self.bucle_secuencia)

    def detener_reproduccion(self):
        self.reproduciendo = False
        self.btn_play.configure(state="normal")
        self.btn_grabar.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.lbl_estado_op.configure(text="Estado: CONECTADO (MODO MANUAL)", text_color="#4caf50")

    def escuchar_esp32(self):
        if self.arduino and self.arduino.is_open:
            try:
                if self.arduino.in_waiting > 0:
                    datos_entrantes = self.arduino.readline().decode('utf-8').strip()
                    print(f"Rx ESP32 -> {datos_entrantes}")
            except Exception as e: 
                pass
        self.after(20, self.escuchar_esp32)

if __name__ == "__main__":
    app = AppGrabadorIntervalos()
    app.mainloop()