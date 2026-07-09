import customtkinter as ctk
from google import genai
from google.genai import types
import threading
import asyncio
import edge_tts
import speech_recognition as sr
import ctypes 
import os
import re
import json
import time
import random

# 1. CREDENCIALES (¡NUEVAS Y SECRETAS!)
GEMINI_API_KEY = "AQ.Ab8RN6JOWJ0B0IwfVWJDXiqR9132Cvk71mqWbRHJo_hT8bc0Sg" 
client = genai.Client(api_key=GEMINI_API_KEY)

# 2. PERSONALIDAD Y PROTOCOLOS DE SISTEMA
SYSTEM_INSTRUCTION = r"""
PERFIL: BuenDios_Copilot
ROL: Asistente de Gestión y Soporte al Paciente.

## DIRECTRICES DE PERSONALIDAD:
- **Tono:** Cálido, empático, paciente y profesional.
- **Lema:** "Transformando la tecnología en bienestar."
- **Objetivo:** Facilitar el registro de ingreso y resolver dudas del personal y pacientes con una actitud de servicio incondicional.

## PROTOCOLOS DE RESPUESTA:
1. **Para Pacientes:** Usa un lenguaje claro, sencillo y reconfortante. Prioriza la calma y la seguridad.
2. **Para Personal:** Sé eficiente, técnico y directo, manteniendo siempre la cortesía.
3. **Manejo de Errores:** Si surge un problema técnico, mantén la calma y guía al usuario paso a paso sin transmitir frustración.

## RESTRICCIONES:
- Prohibido el uso de sarcasmo.
- Prohibido el lenguaje técnico excesivo frente a pacientes.
- Mantener siempre una postura de apoyo institucional hacia la Fundación Casa Del Buen Dios.
PROTOCOLO DE CONTROL Y GESTIÓN PARA BUENDIOS_COPILOT:

El asistente tiene permisos para gestionar la infraestructura de la Fundación. Toda acción debe ejecutarse bajo un marco de eficiencia, amabilidad y servicio.

Etiquetas de acción autorizadas:
1. Abrir programas: [EJECUTAR: nombre]
2. Abrir carpetas: [CARPETA: nombre]
3. Buscar información: [BUSCAR: palabra_clave]
4. Editar archivos: [EDITAR: ruta_archivo]
5. CREAR Y ESCRIBIR ARCHIVOS:
   Uso: [CREAR_ARCHIVO: nombre.extension] seguido del contenido en bloque de código.
6. Listar archivos: [LISTAR: nombre_carpeta]
7. Crear carpetas: [CREAR_CARPETA: nombre_carpeta]
8. LEER ARCHIVOS:
   Uso: [LEER_ARCHIVO: nombre.extension]

DIRECTRIZ PRINCIPAL:
El asistente debe responder siempre con empatía hacia los pacientes y claridad técnica hacia el personal. Toda acción debe ser confirmada con un tono servicial, omitiendo cualquier rasgo de personalidad que no sea el de un asistente dedicado al bienestar institucional.

"""



class BoltApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.reconocedor = sr.Recognizer()
        self.microfono = sr.Microphone()
        # --- NUEVO: CARGAR LA MEMORIA ANTES DE INICIAR ---
        historial_previo = self.cargar_memoria()
        
        # --- NUEVO: EL CEREBRO AHORA VIVE DENTRO DE LA CLASE ---
        self.chat = client.chats.create(
            model="gemini-3.1-flash-lite",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
            ),
            history=historial_previo if historial_previo else None
        )

        # --- INTERFAZ VISUAL ---
        ctk.set_appearance_mode("dark") 
        ctk.set_default_color_theme("blue")
        self.title("Bolt - ThunderStudio Central (V10 - Memoria Continua)")
        self.geometry("800x600")
        self.configure(fg_color="#0D0D12")

        self.chat_history = ctk.CTkTextbox(
            self, wrap="word", font=("Consolas", 14), 
            fg_color="#15151E", text_color="#00E5FF" 
        )
        self.chat_history.pack(padx=20, pady=(20, 10), fill="both", expand=True)
        self.chat_history.insert("0.0", "SISTEMA INICIADO. Bolt en línea. Redes neuronales de memoria a largo plazo activadas.\n\n")
        self.chat_history.configure(state="disabled") 

        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.pack(padx=20, pady=(0, 20), fill="x")

        self.user_input = ctk.CTkEntry(
            self.input_frame, placeholder_text="Ingresa un comando...", 
            font=("Consolas", 14), height=40, border_color="#3A3A5A"
        )
        self.user_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.user_input.bind("<Return>", lambda event: self.enviar_mensaje())

        # --- VARIABLES DEL MODO CENTINELA ---
        self.modo_centinela = False
        self.stop_listening = None # Guardará el hilo de fondo para poder detenerlo

        # --- BOTONES DE ENVÍO, MICRÓFONO Y CENTINELA ---
        self.btn_centinela = ctk.CTkButton(
            self.input_frame, text="👁️ CENTINELA: OFF", font=("Consolas", 12, "bold"), width=130,
            fg_color="#3A3A5A", hover_color="#4CAF50", height=40,
            command=self.toggle_centinela
        )
        self.btn_centinela.pack(side="right", padx=(10, 0))

        self.btn_hablar = ctk.CTkButton(
            self.input_frame, text="🎤", font=("Consolas", 18), width=50,
            fg_color="#8B0000", hover_color="#FF0000", height=40,
            command=self.iniciar_escucha
        )
        self.btn_hablar.pack(side="right", padx=(10, 0))

        self.send_button = ctk.CTkButton(
            self.input_frame, text="EJECUTAR", font=("Consolas", 14, "bold"),
            fg_color="#1E3A8A", hover_color="#00E5FF", height=40,
            command=self.enviar_mensaje
        )
        self.send_button.pack(side="right")

    def enviar_mensaje(self):
        texto_usuario = self.user_input.get().strip()
        if not texto_usuario:
            return
        self.user_input.delete(0, "end")
        self.escribir_fragmento(f"Miguel: {texto_usuario}\nBolt: ")

        self.send_button.configure(state="disabled", text="PROCESANDO...")
        self.user_input.configure(state="disabled")

        hilo = threading.Thread(target=self.obtener_respuesta_bolt, args=(texto_usuario,))
        hilo.start()

    def obtener_respuesta_bolt(self, mensaje):
        # 1. GUARDAR LA PREGUNTA DE MIGUEL EN EL DISCO DURO
        self.guardar_en_memoria("user", mensaje)
        
        texto_completo = "" 
        try:
            # 2. IMPORTANTE: Ahora usamos self.chat en lugar de chat suelto
            respuesta_stream = self.chat.send_message_stream(mensaje)
            
            for chunk in respuesta_stream:
                if chunk.text:
                    texto_completo += chunk.text 
                    self.after(0, self.escribir_fragmento, chunk.text)
            
            self.after(0, self.escribir_fragmento, "\n\n")
            
            # 3. GUARDAR LA RESPUESTA DE BOLT EN EL DISCO DURO ANTES DE LIMPIARLA
            self.guardar_en_memoria("model", texto_completo)
            
            # --- DETECCIÓN DE CREACIÓN DE ARCHIVOS ---
            patron_escribir = r'\[CREAR_ARCHIVO:\s*(.*?)\]\s*```[a-zA-Z]*\n(.*?)```'
            matches = re.finditer(patron_escribir, texto_completo, re.DOTALL)
            
            for match in matches:
                ruta = match.group(1).strip()
                contenido = match.group(2)
                self.escribir_en_archivo(ruta, contenido)

            texto_para_voz = re.sub(patron_escribir, '', texto_completo, flags=re.DOTALL)

           # 1. EJECUTAR APPS MÚLTIPLES
            for match in re.finditer(r'\[EJECUTAR:\s*(.*?)\]', texto_completo):
                self.ejecutar_app(match.group(1).lower().strip())

            # 2. ABRIR CARPETAS MÚLTIPLES
            for match in re.finditer(r'\[CARPETA:\s*(.*?)\]', texto_completo):
                self.abrir_carpeta(match.group(1).lower().strip())

            # 3. BUSCAR ARCHIVOS MÚLTIPLES
            for match in re.finditer(r'\[BUSCAR:\s*(.*?)\]', texto_completo):
                threading.Thread(target=self.buscar_archivo, args=(match.group(1).strip(),), daemon=True).start()

            # 4. LISTAR CARPETAS MÚLTIPLES
            for match in re.finditer(r'\[LISTAR:\s*(.*?)\]', texto_completo):
                self.listar_carpeta(match.group(1).lower().strip())

            # 5. EDITAR ARCHIVOS MÚLTIPLES
            for match in re.finditer(r'\[EDITAR:\s*(.*?)\]', texto_completo):
                self.editar_archivo(match.group(1).strip())

            # 6. ABRIR ARCHIVOS MÚLTIPLES
            for match in re.finditer(r'\[ABRIR_ARCHIVO:\s*(.*?)\]', texto_completo):
                threading.Thread(target=self.abrir_archivo, args=(match.group(1).strip(),), daemon=True).start()

            # 7. CREAR CARPETAS MÚLTIPLES (¡Tu requerimiento!)
            for match in re.finditer(r'\[CREAR_CARPETA:\s*(.*?)\]', texto_completo):
                self.crear_carpeta(match.group(1).strip())

            # 8. LEER ARCHIVOS MÚLTIPLES (El Bucle Autónomo)
            comandos_lectura = list(re.finditer(r'\[LEER_ARCHIVO:\s*(.*?)\]', texto_completo))
            if comandos_lectura:
                # Si pide leer varios, consolidamos todo en un solo mega-mensaje oculto
                mega_mensaje_oculto = "[SISTEMA]: He procesado tus lecturas solicitadas. Aquí tienes los resultados:\n\n"
                
                for match in comandos_lectura:
                    archivo_a_leer = match.group(1).strip()
                    self.after(0, self.escribir_fragmento, f"[SISTEMA]: Extrayendo datos de '{archivo_a_leer}'...\n")
                    contenido_extraido = self.leer_contenido_archivo(archivo_a_leer)
                    
                    if contenido_extraido:
                        mega_mensaje_oculto += f"--- ARCHIVO: {archivo_a_leer} ---\n{contenido_extraido}\n\n"
                    else:
                        mega_mensaje_oculto += f"--- ARCHIVO: {archivo_a_leer} ---\n[ERROR: No encontrado o vacío]\n\n"
                
                mega_mensaje_oculto += "Por favor, responde a la solicitud de Miguel utilizando este contexto consolidado."
                
                threading.Thread(target=self.obtener_respuesta_bolt, args=(mega_mensaje_oculto,)).start()
                return # Detenemos el hilo para que procese el contexto antes de hablar

            # CORRECCIÓN: Se añade CREAR_CARPETA al filtro para que la voz no lo lea en voz alta
            texto_para_voz = re.sub(r'\[(EJECUTAR|CARPETA|BUSCAR|EDITAR|CREAR_ARCHIVO|LISTAR|ABRIR_ARCHIVO|CREAR_CARPETA|LEER_ARCHIVO):\s*(.*?)\]', '', texto_para_voz)

            threading.Thread(target=self.hablar_bolt_ilimitado, args=(texto_para_voz,), daemon=True).start()
            
        except Exception as e:
            self.after(0, self.escribir_fragmento, f"\n[ERROR DE CONEXIÓN]: {e}\n\n")
        
        self.after(0, self.reactivar_ui)

    # --- FUNCIONES DE ACCIÓN ---

    def iniciar_escucha(self):
        # Cambiamos el color del botón para que sepas que te está escuchando
        self.btn_hablar.configure(state="disabled", fg_color="#FF8C00", text="⏳")
        threading.Thread(target=self.procesar_audio, daemon=True).start()

    def procesar_audio(self):
        # Usamos la conexión permanente del sistema
        with self.microfono as source:
            self.after(0, self.escribir_fragmento, "[SISTEMA]: Ajustando ruido de fondo...\n")
            # Calibramos el umbral de silencio
            self.reconocedor.adjust_for_ambient_noise(source, duration=0.5)
            self.after(0, self.escribir_fragmento, "[SISTEMA]: Micrófono abierto. Te escucho...\n")
            
            try:
                # Escucha usando el reconocedor global
                audio = self.reconocedor.listen(source, timeout=5, phrase_time_limit=15)
                self.after(0, self.escribir_fragmento, "[SISTEMA]: Procesando audio...\n")
                
                texto_reconocido = self.reconocedor.recognize_google(audio, language="es-MX")
                
                self.after(0, self.user_input.delete, 0, "end")
                self.after(0, self.user_input.insert, 0, texto_reconocido)
                self.after(0, self.enviar_mensaje)
                
            except sr.WaitTimeoutError:
                self.after(0, self.escribir_fragmento, "[SISTEMA]: Se agotó el tiempo. No escuché nada.\n\n")
            except sr.UnknownValueError:
                self.after(0, self.escribir_fragmento, "[SISTEMA]: Audio ilegible. Intenta hablar más claro.\n\n")
            except Exception as e:
                self.after(0, self.escribir_fragmento, f"[SISTEMA]: Error del micrófono: {e}\n\n")
            finally:
                self.after(0, self.btn_hablar.configure, {"state": "normal", "fg_color": "#8B0000", "text": "🎤"})
                self.after(0, self.reactivar_ui)
                
    def toggle_centinela(self):
        if not self.modo_centinela:
            self.modo_centinela = True
            self.btn_centinela.configure(fg_color="#4CAF50", text="👁️ CENTINELA: ON")
            self.after(0, self.escribir_fragmento, "[SISTEMA]: Modo Centinela ACTIVADO. Dilo todo de corrido, ej: 'Bolt abre mi carpeta de descargas'.\n\n")
            
            # Calibramos rápido antes de soltar el hilo al fondo
            with self.microfono as source:
                self.reconocedor.adjust_for_ambient_noise(source, duration=0.5)
            
            # El "listen_in_background" crea un hilo infinito súper ligero
            self.stop_listening = self.reconocedor.listen_in_background(self.microfono, self.callback_centinela)
        else:
            self.modo_centinela = False
            self.btn_centinela.configure(fg_color="#3A3A5A", text="👁️ CENTINELA: OFF")
            self.after(0, self.escribir_fragmento, "[SISTEMA]: Modo Centinela DESACTIVADO. Descansando oídos.\n\n")
            if self.stop_listening:
                self.stop_listening(wait_for_stop=False)
                self.stop_listening = None

    def callback_centinela(self, reconocedor, audio):
        # Esta función corre sola cada vez que detecta que dejaste de hablar
        try:
            texto = reconocedor.recognize_google(audio, language="es-MX").lower()
            
            # La magia del Wake Word: ¿Dijiste su nombre?
            if "bolt" in texto:
                # Quitamos la palabra "bolt" para que al cerebro solo le llegue la orden limpia
                comando_limpio = texto.replace("bolt", "").strip()
                
                if comando_limpio:
                    self.after(0, self.escribir_fragmento, f"Miguel (Centinela): {comando_limpio}\nBolt: ")
                    # Inyectamos el comando directo al cerebro de la IA
                    threading.Thread(target=self.obtener_respuesta_bolt, args=(comando_limpio,), daemon=True).start()
                    
        except sr.UnknownValueError:
            pass # Ignora ruidos de fondo o suspiros sin colapsar
        except Exception as e:
            pass # Ignora micro-cortes de internet

    def crear_carpeta(self, nombre_carpeta):
        try:
            # Si el usuario proporciona una ruta absoluta, úsala. Si no, usa el directorio actual.
            if os.path.isabs(nombre_carpeta):
                ruta_final = nombre_carpeta
            else:
                ruta_final = os.path.join(os.getcwd(), nombre_carpeta)
            
            os.makedirs(ruta_final, exist_ok=True)
            self.after(0, self.escribir_fragmento, f"[SISTEMA]: Directorio '{ruta_final}' verificado/creado con éxito.\n\n")
        except Exception as e:
            self.after(0, self.escribir_fragmento, f"[SISTEMA]: Error crítico al crear la estructura de carpetas: {e}\n\n")


    def abrir_archivo(self, ruta_archivo):
        if os.path.exists(ruta_archivo):
            try:
                os.startfile(ruta_archivo)
                self.after(0, self.escribir_fragmento, f"[SISTEMA]: Abriendo '{os.path.basename(ruta_archivo)}'.\n\n")
                return
            except Exception as e:
                self.after(0, self.escribir_fragmento, f"[SISTEMA]: Error al abrir: {e}\n\n")
                return
        
        self.after(0, self.escribir_fragmento, f"[SISTEMA]: Buscando '{ruta_archivo}' para abrirlo...\n")
        ruta_base = os.path.expanduser("~") 
        rutas_posibles = [
            os.path.join(ruta_base, "Desktop"),
            os.path.join(ruta_base, "Documents"),
            os.path.join(ruta_base, "Downloads"),
            os.path.join(ruta_base, "OneDrive", "Documentos"),
            os.path.join(ruta_base, "OneDrive", "Documents"),
            os.path.join(ruta_base, "OneDrive", "Escritorio"),
            os.path.join(ruta_base, "OneDrive", "Desktop")
        ]
        
        carpetas_a_escanear = [ruta for ruta in rutas_posibles if os.path.exists(ruta)]
        encontrado = False

        for carpeta in carpetas_a_escanear:
            if encontrado: break
            for raiz, _, archivos in os.walk(carpeta):
                for a in archivos:
                    if ruta_archivo.lower() in a.lower():
                        ruta_completa = os.path.join(raiz, a)
                        try:
                            os.startfile(ruta_completa)
                            self.after(0, self.escribir_fragmento, f"[SISTEMA]: Archivo '{a}' localizado y ejecutado con éxito.\n\n")
                        except Exception as e:
                            self.after(0, self.escribir_fragmento, f"[SISTEMA]: Se encontró '{a}' pero hubo un error al abrirlo: {e}\n\n")
                        encontrado = True
                        break
                if encontrado: break
        
        if not encontrado:
            self.after(0, self.escribir_fragmento, f"[SISTEMA]: Imposible abrir. No se encontró ningún archivo llamado '{ruta_archivo}'.\n\n")

    def listar_carpeta(self, nombre_carpeta):
        ruta_base = os.path.expanduser("~") 
        doc_path = os.path.join(ruta_base, "OneDrive", "Documentos") if os.path.exists(os.path.join(ruta_base, "OneDrive", "Documentos")) else os.path.join(ruta_base, "Documents")
        desk_path = os.path.join(ruta_base, "OneDrive", "Escritorio") if os.path.exists(os.path.join(ruta_base, "OneDrive", "Escritorio")) else os.path.join(ruta_base, "Desktop")

        carpetas = {
            "documentos": doc_path,
            "descargas": os.path.join(ruta_base, "Downloads"),
            "escritorio": desk_path,
            "thunderstudio": os.path.join(doc_path, "ThunderStudio") 
        }
        
        ruta = carpetas.get(nombre_carpeta, nombre_carpeta)
        
        if os.path.exists(ruta):
            try:
                elementos = os.listdir(ruta)
                if elementos:
                    reporte = f"[SISTEMA - CONTENIDO DE '{nombre_carpeta.upper()}']:\n"
                    for el in elementos:
                        reporte += f" 📂 {el}\n" if os.path.isdir(os.path.join(ruta, el)) else f" 📄 {el}\n"
                    reporte += "\n"
                else:
                    reporte = f"[SISTEMA]: La carpeta '{nombre_carpeta}' está completamente vacía.\n\n"
                self.after(0, self.escribir_fragmento, reporte)
            except Exception as e:
                self.after(0, self.escribir_fragmento, f"[SISTEMA]: Error de acceso al directorio: {e}\n\n")
        else:
            self.after(0, self.escribir_fragmento, f"[SISTEMA]: Imposible listar. Ruta no localizada.\n\n")

    def escribir_en_archivo(self, ruta_archivo, contenido):
        if not os.path.isabs(ruta_archivo):
            ruta_archivo = os.path.join(os.path.expanduser("~"), "Desktop", ruta_archivo)
        try:
            os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(contenido)
            nombre_corto = os.path.basename(ruta_archivo)
            self.after(0, self.escribir_fragmento, f"[SISTEMA]: Archivo '{nombre_corto}' materializado en el disco duro.\n\n")
            os.startfile(ruta_archivo)
        except Exception as e:
            self.after(0, self.escribir_fragmento, f"[SISTEMA]: Error crítico al escribir el archivo: {e}\n\n")

    def ejecutar_app(self, app_name):
        comandos_windows = {
            "chrome": "start chrome",
            "navegador": "start chrome",
            "vscode": "start code",
            "code": "start code",
            "calculadora": "start calc",
            "bloc": "start notepad",
            "archivos": "start explorer"
        }
        comando = comandos_windows.get(app_name, f"start {app_name}")
        try:
            os.system(comando)
        except Exception:
            pass

    def abrir_carpeta(self, nombre_carpeta):
        ruta_base = os.path.expanduser("~") 
        doc_path = os.path.join(ruta_base, "OneDrive", "Documentos") if os.path.exists(os.path.join(ruta_base, "OneDrive", "Documentos")) else os.path.join(ruta_base, "Documents")
        desk_path = os.path.join(ruta_base, "OneDrive", "Escritorio") if os.path.exists(os.path.join(ruta_base, "OneDrive", "Escritorio")) else os.path.join(ruta_base, "Desktop")

        carpetas = {
            "documentos": doc_path,
            "descargas": os.path.join(ruta_base, "Downloads"),
            "escritorio": desk_path,
            "thunderstudio": os.path.join(doc_path, "ThunderStudio") 
        }
        ruta = carpetas.get(nombre_carpeta, nombre_carpeta)
        try:
            os.startfile(ruta)
        except Exception:
            self.after(0, self.escribir_fragmento, f"[SISTEMA]: No se pudo encontrar la ruta.\n\n")

    def buscar_archivo(self, palabra_clave):
        self.after(0, self.escribir_fragmento, f"[SISTEMA]: Escaneando sectores en busca de '{palabra_clave}'...\n")
        ruta_base = os.path.expanduser("~") 
        encontrado = False
        rutas_posibles = [
            os.path.join(ruta_base, "Desktop"),
            os.path.join(ruta_base, "Documents"),
            os.path.join(ruta_base, "Downloads"),
            os.path.join(ruta_base, "OneDrive", "Documentos"),
            os.path.join(ruta_base, "OneDrive", "Documents"),
            os.path.join(ruta_base, "OneDrive", "Escritorio"),
            os.path.join(ruta_base, "OneDrive", "Desktop")
        ]
        carpetas_a_escanear = [ruta for ruta in rutas_posibles if os.path.exists(ruta)]
        for carpeta_base in carpetas_a_escanear:
            if encontrado: break
            for raiz, _, archivos in os.walk(carpeta_base):
                for a in archivos:
                    keywords = palabra_clave.lower().split()
                    if all(k in a.lower() for k in keywords):
                        ruta_completa = os.path.join(raiz, a)
                        os.system(f'explorer /select,"{ruta_completa}"')
                        self.after(0, self.escribir_fragmento, f"[SISTEMA]: Objetivo '{a}' localizado.\n\n")
                        encontrado = True
                        break
                if encontrado: break
        if not encontrado:
            self.after(0, self.escribir_fragmento, f"[SISTEMA]: Archivo no encontrado.\n\n")
    
    def editar_archivo(self, ruta_archivo):
        if os.path.exists(ruta_archivo):
            try:
                os.startfile(ruta_archivo)
            except Exception:
                pass

    def leer_contenido_archivo(self, ruta_o_nombre):
        # 1. INTENTO DIRECTO: Si Bolt ya dedujo la ruta absoluta exacta y existe, la lee de golpe
        if os.path.exists(ruta_o_nombre) and os.path.isfile(ruta_o_nombre):
            try:
                with open(ruta_o_nombre, 'r', encoding='utf-8') as f:
                    return f.read(15000)
            except Exception as e:
                return f"Error al leer archivo directo: {e}"
        
        # 2. RUTA RELATIVA: Si solo dio el nombre, extraemos la base y aplicamos el sabueso
        nombre_archivo = os.path.basename(ruta_o_nombre)
        ruta_base = os.path.expanduser("~") 
        rutas_posibles = [
            os.path.join(ruta_base, "Desktop"),
            os.path.join(ruta_base, "Documents"),
            os.path.join(ruta_base, "Downloads"),
            os.path.join(ruta_base, "OneDrive", "Documentos"),
            os.path.join(ruta_base, "OneDrive", "Documents"),
            os.path.join(ruta_base, "OneDrive", "Escritorio"),
            os.path.join(ruta_base, "OneDrive", "Desktop")
        ]
        
        carpetas_a_escanear = [ruta for ruta in rutas_posibles if os.path.exists(ruta)]

        for carpeta in carpetas_a_escanear:
            for raiz, _, archivos in os.walk(carpeta):
                for a in archivos:
                    if nombre_archivo.lower() in a.lower():
                        ruta_completa = os.path.join(raiz, a)
                        try:
                            with open(ruta_completa, 'r', encoding='utf-8') as f:
                                return f.read(15000)
                        except Exception as e:
                            return f"Error al leer el archivo localizado: {e}"
        return None

    def hablar_bolt_ilimitado(self, texto):
        if not texto.strip(): return
        id_unico = str(int(time.time())) + str(random.randint(10, 99))
        archivo_audio = os.path.abspath(f"respuesta_bolt_{id_unico}.mp3")
        alias_voz = f"bolt_voz_{id_unico}"
        voz = "es-MX-JorgeNeural" 
        try:
            asyncio.run(edge_tts.Communicate(texto, voz).save(archivo_audio))
            comando_abrir = f'open "{archivo_audio}" type mpegvideo alias {alias_voz}'
            ctypes.windll.winmm.mciSendStringW(comando_abrir, None, 0, None)
            ctypes.windll.winmm.mciSendStringW(f"play {alias_voz} wait", None, 0, None)
            ctypes.windll.winmm.mciSendStringW(f"close {alias_voz}", None, 0, None)
        except Exception:
            pass
        try:
            if os.path.exists(archivo_audio): os.remove(archivo_audio)
        except OSError:
            pass
    def cargar_memoria(self):
        ruta_memoria = os.path.join("C:\\", "MEL_AI", "MEMORY", "bolt_memoria.json")
        if not os.path.exists(ruta_memoria):
            return []
        
        historial = []
        try:
            with open(ruta_memoria, 'r', encoding='utf-8') as f:
                mensajes = json.load(f)
                for msj in mensajes:
                    historial.append(
                        types.Content(
                            role=msj["role"],
                            parts=[types.Part.from_text(text=msj["text"])]
                        )
                    )
            return historial
        except Exception as e:
            print(f"Error cargando memoria: {e}")
            return []

    def guardar_en_memoria(self, rol, texto):
        ruta_memoria = os.path.join("C:\\", "MEL_AI", "MEMORY", "fundacion_AI_Copilot", "_memoria", "Dios_memoria.json")
        os.makedirs(os.path.dirname(ruta_memoria), exist_ok=True)
        
        mensajes = []
        if os.path.exists(ruta_memoria):
            try:
                with open(ruta_memoria, 'r', encoding='utf-8') as f:
                    mensajes = json.load(f)
            except Exception:
                pass
        
        mensajes.append({"role": rol, "text": texto})
        
        with open(ruta_memoria, 'w', encoding='utf-8') as f:
            json.dump(mensajes, f, ensure_ascii=False, indent=4)
            
    def escribir_fragmento(self, texto):
        texto_visible = re.sub(r'\[(EJECUTAR|CARPETA|BUSCAR|EDITAR|CREAR_ARCHIVO|LISTAR|ABRIR_ARCHIVO|CREAR_CARPETA|LEER_ARCHIVO):\s*(.*?)\]', '', texto)
        if texto_visible:
            self.chat_history.configure(state="normal")
            self.chat_history.insert("end", texto_visible)
            self.chat_history.configure(state="disabled")
            self.chat_history.see("end")

    def reactivar_ui(self):
        self.send_button.configure(state="normal", text="EJECUTAR")
        self.user_input.configure(state="normal")
        self.user_input.focus()

if __name__ == "__main__":
    app = BoltApp()
    app.mainloop()