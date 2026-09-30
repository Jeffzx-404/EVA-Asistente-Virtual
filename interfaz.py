import tkinter as tk
from tkinter import scrolledtext
from tkinter import messagebox
import threading


class InterfazEVA:



    def mostrar_recordatorio(self, mensaje):

        def mostrar():

            messagebox.showinfo(
                "🔔 Recordatorio de EVA",
                mensaje
            )

        self.ventana.after(
            0,
            mostrar
        )


    def __init__(self):

        self.ventana = tk.Tk()

        self.ventana.title(
            "EVA - Asistente Virtual"
        )

        self.ventana.geometry(
            "700x650"
        )
        

        self.ventana.resizable(
            True,
            True
        )

        # Función que se ejecutará
        # cuando presionemos HABLAR
        self.funcion_escuchar = None

        # ==========================================
        # TÍTULO
        # ==========================================

        self.titulo = tk.Label(
            self.ventana,
            text="EVA",
            font=("Arial", 32, "bold")
        )

        self.titulo.pack(
            pady=(25, 5)
        )

        self.subtitulo = tk.Label(
            self.ventana,
            text="Asistente Virtual Personal",
            font=("Arial", 12)
        )

        self.subtitulo.pack(
            pady=(0, 20)
        )

        # ==========================================
        # HISTORIAL
        # ==========================================

        self.historial = scrolledtext.ScrolledText(
            self.ventana,
            width=70,
            height=15,
            font=("Arial", 11),
            state="disabled"
        )

        self.historial.pack(
            padx=20,
            pady=10
        )

        # ==========================================
        # ESTADO
        # ==========================================

        self.estado = tk.Label(
            self.ventana,
            text="EVA está lista",
            font=("Arial", 11)
        )

        self.estado.pack(
            pady=10
        )

        # ==========================================
        # ENTRADA DE TEXTO
        # ==========================================

        self.entrada = tk.Entry(
            self.ventana,
            font=("Arial", 12),
            width=45
        )

        self.entrada.pack(
            pady=5
        )

        self.entrada.bind(
            "<Return>",
            lambda evento: self.presionar_enviar()
        )

        # BOTON PARA ENVIAR

        self.boton_enviar = tk.Button(
            self.ventana,
            text="ENVIAR",
            font=("Arial", 11, "bold"),
            width=15,
            command=self.presionar_enviar
        )

        self.boton_enviar.pack(
            pady=5
        )


        # ==========================================
        # BOTÓN HABLAR
        # ==========================================

        self.boton = tk.Button(
            self.ventana,
            text="🎤 HABLAR",
            font=("Arial", 12, "bold"),
            width=20,
            height=2,
            command=self.presionar_hablar
        )

        self.boton.pack(
            pady=10
        )


    # ==============================================
    # CONFIGURAR FUNCIÓN DE VOZ
    # ==============================================

    def configurar_escucha(
        self,
        funcion
    ):

        self.funcion_escuchar = funcion

        self.funcion_comando = None


    def configurar_comando(
        self,
        funcion
):

        self.funcion_comando = funcion

    def presionar_enviar(self):

        comando = self.entrada.get().strip()

        if comando == "":
            return

        self.entrada.delete(
            0,
            tk.END
    )

        self.agregar_mensaje(
            "TÚ",
            comando
    )

        if self.funcion_comando is not None:

            hilo = threading.Thread(
                target=self.funcion_comando,
                args=(comando,),
                daemon=True
        )

            hilo.start()


    # ==============================================
    # BOTÓN HABLAR
    # ==============================================

    def presionar_hablar(self):

        if self.funcion_escuchar is None:
            return

        self.boton.config(
            state="disabled"
        )

        self.cambiar_estado(
            "🎤 Escuchando..."
        )

        hilo = threading.Thread(
            target=self.ejecutar_escucha,
            daemon=True
        )

        hilo.start()


    def ejecutar_escucha(self):

        try:

            self.funcion_escuchar()

        except Exception as error:

            print(
                "Error en interfaz:",
                error
            )

        finally:

            self.ventana.after(
                0,
                self.finalizar_escucha
            )


    def finalizar_escucha(self):

        self.cambiar_estado(
            "EVA está lista"
        )

        self.boton.config(
            state="normal"
        )


    # ==============================================
    # HISTORIAL
    # ==============================================

    def agregar_mensaje(
        self,
        persona,
        mensaje
    ):

        def actualizar():

            self.historial.config(
                state="normal"
            )

            self.historial.insert(
                tk.END,
                f"{persona}: {mensaje}\n\n"
            )

            self.historial.config(
                state="disabled"
            )

            self.historial.see(
                tk.END
            )

        self.ventana.after(
            0,
            actualizar
        )


    # ==============================================
    # CAMBIAR ESTADO
    # ==============================================

    def cambiar_estado(
        self,
        texto
    ):

        def actualizar():

            self.estado.config(
                text=texto
            )

        self.ventana.after(
            0,
            actualizar
        )


    # MOSTRAR RECORDATORIO


    def mostrar_recordatorio(self, mensaje):

        def mostrar():

            messagebox.showinfo(
                "🔔 Recordatorio de EVA",
                mensaje
            )

        self.ventana.after(
            0,
            mostrar
        )

    # ==============================================
    # INICIAR INTERFAZ
    # ==============================================

    def iniciar(self):

        self.ventana.mainloop()