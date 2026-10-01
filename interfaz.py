import tkinter as tk
from tkinter import messagebox, scrolledtext
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
        fondo, panel, texto = "#10141f", "#191f2e", "#edf1fa"
        self.ventana = tk.Tk()
        self.ventana.title("EVA - Asistente Virtual")
        self.ventana.geometry("860x720")
        self.ventana.minsize(620, 500)
        self.ventana.resizable(True, True)
        self.ventana.configure(bg=fondo)
        self.ventana.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.ventana.columnconfigure(0, weight=1)
        self.ventana.rowconfigure(1, weight=1)

        encabezado = tk.Frame(self.ventana, bg=fondo)
        encabezado.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 18))
        encabezado.columnconfigure(0, weight=1)
        self.titulo = tk.Label(encabezado, text="EVA", font=("Segoe UI", 32, "bold"),
                               bg=fondo, fg=texto)
        self.titulo.grid(row=0, column=0, sticky="w")
        self.subtitulo = tk.Label(encabezado, text="Asistente Virtual", font=("Segoe UI", 12),
                                  bg=fondo, fg="#99a7bd")
        self.subtitulo.grid(row=1, column=0, sticky="w")
        self.estado = tk.Label(encabezado, font=("Segoe UI", 10, "bold"), bg=panel,
                               padx=14, pady=9)
        self.estado.grid(row=0, column=1, rowspan=2, sticky="e")

        conversacion = tk.Frame(self.ventana, bg=panel, padx=12, pady=12)
        conversacion.grid(row=1, column=0, sticky="nsew", padx=28)
        conversacion.columnconfigure(0, weight=1)
        conversacion.rowconfigure(0, weight=1)
        self.historial = scrolledtext.ScrolledText(
            conversacion, font=("Segoe UI", 11), bg=panel, fg=texto,
            selectbackground="#425c88", selectforeground="white", relief="flat",
            borderwidth=0, wrap="word", padx=14, pady=10, state="disabled",
            width=40, height=10, cursor="xterm", takefocus=True,
        )
        self.historial.grid(row=0, column=0, sticky="nsew")
        self.historial.vbar.configure(bg=panel, troughcolor=fondo, activebackground="#425c88")
        for etiqueta, color, alineacion in (
            ("usuario", "#8bc7ff", "right"), ("eva", "#cab5ff", "left")
        ):
            self.historial.tag_configure(etiqueta, foreground=color, justify=alineacion,
                                         spacing1=8, spacing3=14, lmargin1=8, lmargin2=8,
                                         rmargin=8)
            self.historial.tag_configure(etiqueta + "_nombre", foreground=color,
                                         justify=alineacion, font=("Segoe UI", 10, "bold"),
                                         spacing1=10)

        controles = tk.Frame(self.ventana, bg=fondo)
        controles.grid(row=2, column=0, sticky="ew", padx=28, pady=20)
        controles.columnconfigure(0, weight=1)
        self.entrada = tk.Entry(controles, font=("Segoe UI", 12), bg=panel, fg=texto,
                                insertbackground=texto, relief="flat", borderwidth=0,
                                highlightthickness=1, highlightbackground="#303b51",
                                highlightcolor="#8b9fff", selectbackground="#425c88")
        self.entrada.grid(row=0, column=0, sticky="ew", ipady=13, padx=(0, 12))
        self.entrada.bind("<Return>", lambda evento: self.presionar_enviar())
        self.boton_enviar = self._crear_boton(controles, "ENVIAR", self.presionar_enviar, "#788bfa")
        self.boton_enviar.grid(row=0, column=1, sticky="ns")
        self.boton = self._crear_boton(controles, "HABLAR", self.presionar_hablar, "#29354d")
        self.boton.grid(row=1, column=0, columnspan=2, pady=(12, 0))
        self._actualizar_estado()
        self.entrada.focus_set()
        self._temporizador = self.ventana.after(30, self._vaciar_cola)

    def _crear_boton(self, padre, texto, comando, color):
        return tk.Button(padre, text=texto, command=comando, font=("Segoe UI", 10, "bold"),
                         bg=color, fg="white", activebackground="#5267bc", activeforeground="white",
                         disabledforeground="#8490a5", relief="flat", borderwidth=0,
                         padx=20, pady=11, cursor="hand2", takefocus=True)

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
        self.estado.config(text="●  " + estado, fg=self._colores_estado[estado])

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
        self.historial.config(state="normal")
        self.historial.insert(tk.END, persona + "\n", etiqueta + "_nombre")
        self.historial.insert(tk.END, mensaje + "\n\n", etiqueta)
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
