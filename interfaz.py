import tkinter as tk
from tkinter import messagebox, scrolledtext, font
import threading
from queue import Queue, Empty


class InterfazEVA:
    """Vista de EVA; los trabajadores envían actualizaciones mediante una cola."""

    def __init__(self):
        self.funcion_escuchar = None
        self.funcion_comando = None
        self._cerrando = threading.Event()
        self._actualizaciones = Queue()
        self._actividades = {"ESCUCHANDO": 0, "PROCESANDO": 0, "HABLANDO": 0}
        self._escucha_activa = False
        self._estado_base = "LISTA"
        self._colores_estado = {
            "LISTA": "#62d6a8", "ESCUCHANDO": "#68b5ff",
            "PROCESANDO": "#f5c76b", "HABLANDO": "#ba9cff",
        }
        fondo, panel, texto = "#0d111b", "#151c2b", "#eef2ff"
        self._simbolos_estado = {"LISTA": "✓", "ESCUCHANDO": "◎",
                                 "PROCESANDO": "◈", "HABLANDO": "≋"}
        self._fondos_estado = {"LISTA": "#16372f", "ESCUCHANDO": "#18344e",
                               "PROCESANDO": "#3b3020", "HABLANDO": "#302747"}
        self.ventana = tk.Tk()
        self.ventana.title("EVA - Asistente Virtual")
        self.ventana.geometry("1100x760")
        self.ventana.minsize(840, 560)
        self.ventana.resizable(True, True)
        self.ventana.configure(bg=fondo)
        self.ventana.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.ventana.columnconfigure(1, weight=1)
        self.ventana.rowconfigure(0, weight=1)

        lateral = tk.Frame(self.ventana, bg="#111725", width=198,
                           highlightthickness=1, highlightbackground="#263046")
        lateral.grid(row=0, column=0, sticky="ns")
        lateral.grid_propagate(False)
        lateral.columnconfigure(0, weight=1)
        lateral.rowconfigure(8, weight=1)
        logo = tk.Canvas(lateral, width=58, height=58, bg="#111725", highlightthickness=0)
        logo.grid(row=0, column=0, sticky="w", padx=24, pady=(30, 8))
        logo.create_polygon(29, 3, 54, 17, 54, 43, 29, 57, 4, 43, 4, 17,
                            fill="#252747", outline="#a79aff", width=2)
        logo.create_line(17, 38, 29, 17, 41, 38, fill="#d7d0ff", width=3)
        logo.create_line(22, 31, 36, 31, fill="#d7d0ff", width=3)
        self.titulo = tk.Label(lateral, text="EVA", font=("Segoe UI", 28, "bold"),
                               bg="#111725", fg=texto)
        self.titulo.grid(row=1, column=0, sticky="w", padx=24)
        self.subtitulo = tk.Label(lateral, text="Asistente Virtual", font=("Segoe UI", 10),
                                  bg="#111725", fg="#a8b3c9")
        self.subtitulo.grid(row=2, column=0, sticky="w", padx=24, pady=(0, 28))
        for fila, nombre in enumerate(("Inicio", "Conversación", "Recordatorios", "Alarmas", "Ajustes"), 3):
            activa = nombre == "Conversación"
            item = tk.Frame(lateral, bg="#282943" if activa else "#111725",
                            highlightthickness=1,
                            highlightbackground="#55517d" if activa else "#111725")
            item.grid(row=fila, column=0, sticky="ew", padx=14, pady=4)
            tk.Label(item, text=("▎  " if activa else "   ") + nombre,
                     font=("Segoe UI", 11, "bold" if activa else "normal"),
                     bg=item.cget("bg"), fg="#e4deff" if activa else "#acb7cc",
                     anchor="w").pack(fill="x", padx=8, pady=(8, 2))
            tk.Label(item, text="ACTIVA" if activa else "Próximamente",
                     font=("Segoe UI", 8), bg=item.cget("bg"),
                     fg="#baafff" if activa else "#98a4ba", anchor="w").pack(
                         fill="x", padx=23, pady=(0, 8))
        tk.Label(lateral, text="TU ASISTENTE PERSONAL", font=("Segoe UI", 8),
                 bg="#111725", fg="#98a4ba").grid(row=9, column=0, pady=22)

        principal = tk.Frame(self.ventana, bg=fondo)
        principal.grid(row=0, column=1, sticky="nsew", padx=18, pady=18)
        principal.columnconfigure(0, weight=1)
        principal.rowconfigure(1, weight=1)
        encabezado = tk.Frame(principal, bg=fondo)
        encabezado.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        encabezado.columnconfigure(0, weight=1)
        tk.Label(encabezado, text="Conversación", font=("Segoe UI", 23, "bold"),
                 bg=fondo, fg=texto).grid(row=0, column=0, sticky="w")
        tk.Label(encabezado, text="Escribe o habla con EVA", font=("Segoe UI", 10),
                 bg=fondo, fg="#a8b3c9").grid(row=1, column=0, sticky="w", pady=(5, 0))
        self.estado = tk.Label(encabezado, font=("Segoe UI", 10, "bold"),
                               padx=10, pady=6)
        self.estado.grid(row=0, column=1, rowspan=2, sticky="e", padx=(12, 0))

        conversacion = tk.Frame(principal, bg=panel, padx=4, pady=4,
                                highlightthickness=1, highlightbackground="#222c3e")
        conversacion.grid(row=1, column=0, sticky="nsew")
        conversacion.columnconfigure(0, weight=1)
        conversacion.rowconfigure(0, weight=1)
        self.historial = scrolledtext.ScrolledText(
            conversacion, font=("Segoe UI", 11), bg=panel, fg=texto,
            selectbackground="#526b9d", selectforeground="white", relief="flat",
            borderwidth=0, wrap="word", padx=12, pady=10, state="disabled",
            width=20, height=10, cursor="xterm", takefocus=True,
        )
        self.historial.grid(row=0, column=0, sticky="nsew")
        self.historial.vbar.configure(bg="#253149", troughcolor=panel,
                                      activebackground="#526b9d", width=12)
        self._tarjetas = []
        self._fuente_mensaje = font.Font(family="Segoe UI", size=11)
        for etiqueta, alineacion in (("eva", "left"), ("usuario", "right")):
            self.historial.tag_configure(etiqueta, justify=alineacion,
                                         spacing1=0, spacing3=0)
        self.historial.bind("<Configure>", self._ajustar_tarjetas)

        controles = tk.Frame(principal, bg=panel, padx=12, pady=10,
                             highlightthickness=1, highlightbackground="#222c3e")
        controles.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        controles.columnconfigure(0, weight=1)
        tk.Label(controles, text="Escribe un comando", font=("Segoe UI", 10),
                 bg=panel, fg="#b9c4d8").grid(row=0, column=0, columnspan=3,
                                            sticky="w", pady=(0, 6))
        self.entrada = tk.Entry(controles, font=("Segoe UI", 11), bg="#0e1522", fg=texto,
                                width=12, insertbackground=texto, relief="flat", borderwidth=0,
                                highlightthickness=1, highlightbackground="#34415b",
                                highlightcolor="#b6a7ff", selectbackground="#526b9d")
        self.entrada.grid(row=1, column=0, sticky="ew", ipady=8, padx=(0, 8))
        self.entrada.bind("<Return>", lambda evento: self.presionar_enviar())
        self.boton = self._crear_boton(controles, "HABLAR", self.presionar_hablar, "#2b3954")
        # Icono dibujado con Tkinter, sin archivos ni fuentes de iconos externas.
        self._icono_microfono = tk.PhotoImage(width=16, height=20)
        for izquierda, arriba, derecha, abajo in (
            (6, 1, 10, 11), (3, 7, 4, 12), (12, 7, 13, 12),
            (4, 12, 12, 14), (7, 14, 9, 18), (4, 18, 12, 19)
        ):
            self._icono_microfono.put("#e4eaff", to=(izquierda, arriba, derecha, abajo))
        self.boton.configure(image=self._icono_microfono, compound="left")
        self.boton.grid(row=1, column=1, sticky="ns", padx=(0, 8))
        self.boton_enviar = self._crear_boton(controles, "ENVIAR", self.presionar_enviar, "#6853ba")
        self.boton_enviar.grid(row=1, column=2, sticky="ns")
        self._actualizar_estado()
        self.entrada.focus_set()
        self._temporizador = self.ventana.after(30, self._vaciar_cola)

    def _crear_boton(self, padre, texto, comando, color):
        boton = tk.Button(padre, text=texto, command=comando, font=("Segoe UI", 10, "bold"),
                          bg=color, fg="white", activebackground=color, activeforeground="white",
                          disabledforeground="#78849a", relief="flat", borderwidth=0,
                          highlightthickness=1, highlightbackground="#43516b",
                          highlightcolor="#cfbfff", padx=12, pady=7,
                          cursor="hand2", takefocus=True)
        def entrar(evento):
            if boton.cget("state") != "disabled":
                boton.configure(bg="#354663" if texto == "HABLAR" else "#7560c6")
        boton.bind("<Enter>", entrar)
        boton.bind("<Leave>", lambda evento: boton.configure(bg=color))
        return boton

    def _ajustar_tarjetas(self, evento):
        if evento.width == getattr(self, "_ancho_tarjetas", None):
            return
        self._ancho_tarjetas = evento.width
        for tarjeta, contenido, texto in self._tarjetas:
            self._dimensionar_tarjeta(tarjeta, contenido, texto)

    def _dimensionar_tarjeta(self, tarjeta, contenido, texto):
        disponible = max(100, self.historial.winfo_width() - 24)
        limite = int(disponible * 0.60)
        natural = max(self._fuente_mensaje.measure(linea) for linea in texto.split("\n")) + 28
        ancho = max(80, min(limite, natural))
        interior = max(40, ancho - 24)
        # Calcular líneas también para tarjetas fuera del área visible.
        lineas = 0
        for parrafo in texto.split("\n"):
            usado = 0
            lineas += 1
            for palabra in parrafo.split(" "):
                medida = self._fuente_mensaje.measure(palabra + " ")
                if usado and usado + medida > interior:
                    lineas += 1
                    usado = 0
                if medida > interior:
                    for caracter in palabra + " ":
                        medida_caracter = self._fuente_mensaje.measure(caracter)
                        if usado + medida_caracter > interior:
                            lineas += 1
                            usado = 0
                        usado += medida_caracter
                else:
                    usado += medida
        tarjeta.configure(width=ancho,
                          height=lineas * self._fuente_mensaje.metrics("linespace") + 20)

    def _desplazar_conversacion(self, evento):
        self.historial.yview_scroll(-int(evento.delta / 120), "units")
        return "break"

    def _programar(self, funcion, *args):
        if not self._cerrando.is_set():
            self._actualizaciones.put((funcion, args))

    def _vaciar_cola(self):
        if self._cerrando.is_set():
            return
        # Limitar el lote mantiene sensible la ventana ante muchos mensajes.
        for _ in range(100):
            try:
                funcion, args = self._actualizaciones.get_nowait()
            except Empty:
                break
            try:
                funcion(*args)
            except Exception as error:
                print("Error actualizando interfaz:", error)
            if self._cerrando.is_set():
                return
        self._temporizador = self.ventana.after(30, self._vaciar_cola)

    def _cerrar(self):
        self._cerrando.set()
        self.ventana.after_cancel(self._temporizador)
        self.ventana.destroy()

    def iniciar_actividad(self, estado):
        self._programar(self._cambiar_actividad, estado, 1)

    def finalizar_actividad(self, estado):
        self._programar(self._cambiar_actividad, estado, -1)

    def _cambiar_actividad(self, estado, cambio):
        if estado in self._actividades:
            self._actividades[estado] = max(0, self._actividades[estado] + cambio)
            self._actualizar_estado()

    def _actualizar_estado(self):
        estado = self._estado_base
        for candidato in ("HABLANDO", "ESCUCHANDO", "PROCESANDO"):
            if self._actividades[candidato]:
                estado = candidato
                break
        self.estado.config(text=self._simbolos_estado[estado] + "  " + estado,
                           fg=self._colores_estado[estado], bg=self._fondos_estado[estado])

    def configurar_escucha(self, funcion):
        self.funcion_escuchar = funcion

    def configurar_comando(self, funcion):
        self.funcion_comando = funcion

    def presionar_enviar(self):
        comando = self.entrada.get().strip()
        if not comando or self._cerrando.is_set():
            return
        self.entrada.delete(0, tk.END)
        self.agregar_mensaje("TÚ", comando)
        if self.funcion_comando is not None:
            threading.Thread(target=self._ejecutar_comando, args=(comando,), daemon=True).start()

    def _ejecutar_comando(self, comando):
        self.iniciar_actividad("PROCESANDO")
        try:
            self.funcion_comando(comando)
        except Exception as error:
            print("Error procesando comando:", error)
        finally:
            self.finalizar_actividad("PROCESANDO")

    def presionar_hablar(self):
        if self.funcion_escuchar is None or self._escucha_activa or self._cerrando.is_set():
            return
        self._escucha_activa = True
        self.boton.config(state="disabled")
        threading.Thread(target=self.ejecutar_escucha, daemon=True).start()

    def ejecutar_escucha(self):
        try:
            self.funcion_escuchar()
        except Exception as error:
            print("Error en interfaz:", error)
        finally:
            self._programar(self.finalizar_escucha)

    def finalizar_escucha(self):
        self._escucha_activa = False
        self.boton.config(state="normal")
        self._actualizar_estado()

    def agregar_mensaje(self, persona, mensaje):
        self._programar(self._insertar_mensaje, persona, mensaje)

    def _insertar_mensaje(self, persona, mensaje):
        etiqueta = "eva" if persona == "EVA" else "usuario"
        fondo = "#2a2943" if etiqueta == "eva" else "#243a57"
        texto = persona + "\n" + mensaje
        tarjeta = tk.Frame(self.historial, bg=fondo)
        tarjeta.pack_propagate(False)
        contenido = tk.Text(tarjeta, font=self._fuente_mensaje, bg=fondo,
                            fg="#eef2ff", wrap="word", relief="flat", borderwidth=0,
                            highlightthickness=0, padx=12, pady=8, width=1, height=1,
                            selectbackground="#526b9d", selectforeground="white",
                            cursor="xterm", takefocus=True)
        contenido.pack(fill="both", expand=True)
        contenido.insert("1.0", texto)
        contenido.tag_configure("nombre", font=("Segoe UI", 11, "bold"))
        contenido.tag_add("nombre", "1.0", "1.end")
        contenido.configure(state="disabled")
        contenido.bind("<MouseWheel>", self._desplazar_conversacion)
        self._tarjetas.append((tarjeta, contenido, texto))
        self._dimensionar_tarjeta(tarjeta, contenido, texto)
        self.historial.config(state="normal")
        inicio = self.historial.index("end-1c")
        self.historial.window_create(tk.END, window=tarjeta, pady=8)
        self.historial.insert(tk.END, "\n")
        self.historial.tag_add(etiqueta, inicio, "end-1c")
        self.historial.config(state="disabled")
        self.historial.see(tk.END)

    def cambiar_estado(self, texto):
        self._programar(self._establecer_estado, texto)

    def _establecer_estado(self, texto):
        normalizado = texto.upper()
        self._estado_base = next((estado for estado in self._actividades if estado in normalizado), "LISTA")
        self._actualizar_estado()

    def mostrar_recordatorio(self, mensaje):
        self._programar(messagebox.showinfo, "Recordatorio de EVA", mensaje)

    def iniciar(self):
        self.ventana.mainloop()
