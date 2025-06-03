import json
from datetime import datetime, timedelta
import os

# --- Funciones de Utilidad ---

def _obtener_saludo_dinamico(nombre, last_interaction_date_str):
    """Genera un saludo dinámico basado en la hora del día y la última interacción."""
    ahora = datetime.now()
    saludo_parte = ""

    if 5 <= ahora.hour < 12:
        saludo_parte = "¡Buenos días"
    elif 12 <= ahora.hour < 19:
        saludo_parte = "¡Buenas tardes"
    else:
        saludo_parte = "¡Buenas noches"

    bienvenida_parte = ""
    if last_interaction_date_str:
        try:
            last_interaction_date = datetime.strptime(last_interaction_date_str, "%Y-%m-%d")
            
            if last_interaction_date.date() == ahora.date():
                bienvenida_parte = "! ¡Qué bueno verte de nuevo!"
            elif last_interaction_date.date() == (ahora - timedelta(days=1)).date():
                bienvenida_parte = "! ¡Bienvenido de vuelta!"
            else:
                bienvenida_parte = "! ¡Me alegra que regreses!" 
        except ValueError:
            bienvenida_parte = "! ¡Bienvenido al Bot de RRHH!"
    else:
        bienvenida_parte = "! ¡Es un gusto conocerte!"

    return f"{saludo_parte}, {nombre}{bienvenida_parte}"


def _actualizar_last_interaction(telefono):
    """Actualiza la fecha de la última interacción del usuario en empleados.json."""
    empleados_data = {}
    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados_data = json.load(f)
    except FileNotFoundError:
        print("Error: empleados.json no encontrado al actualizar la interacción.")
        return
    except json.JSONDecodeError:
        print("Error: Formato de empleados.json inválido al actualizar la interacción.")
        return

    encontrado = False
    # Limpiar el número de teléfono para la búsqueda (asumiendo que viene de Twilio como whatsapp:+XXXXXXXX)
    telefono_limpio = str(telefono).replace("whatsapp:", "").replace("+", "").strip()

    for emp_id, emp_info in empleados_data.items():
        emp_telefono_limpio = str(emp_info.get("telefono", "")).replace("+", "").strip()
        
        # Considerar si el número guardado en JSON puede ser el de Argentina sin el "9" o "549"
        # y si el de Twilio siempre tiene el "549" después del +
        if emp_telefono_limpio == telefono_limpio:
            emp_info["last_interaction_date"] = datetime.now().strftime("%Y-%m-%d")
            encontrado = True
            break
        # Si el número de Twilio es +54911xxxx y el de JSON es 11xxxx, coincidir
        if telefono_limpio.startswith("549") and emp_telefono_limpio == telefono_limpio[3:]:
             emp_info["last_interaction_date"] = datetime.now().strftime("%Y-%m-%d")
             encontrado = True
             break
        # Si el número de Twilio es +5411xxxx y el de JSON es 11xxxx, coincidir
        if telefono_limpio.startswith("54") and emp_telefono_limpio == telefono_limpio[2:]:
            emp_info["last_interaction_date"] = datetime.now().strftime("%Y-%m-%d")
            encontrado = True
            break


    if encontrado:
        with open("empleados.json", "w", encoding="utf-8") as f:
            json.dump(empleados_data, f, indent=4, ensure_ascii=False)
        # print(f"[DEBUG] last_interaction_date actualizado para {telefono}") # Descomentar para depuración
    else:
        print(f"[DEBUG] No se encontró al empleado con teléfono {telefono} para actualizar last_interaction_date.")

# --- Funciones de Menú ---

def mostrar_menu_admin(nombre_admin, telefono_admin=None):
    """Muestra el menú para el rol de administrador con saludo dinámico y estilo mejorado."""
    saludo = ""
    if telefono_admin:
        empleado_info = obtener_usuario_por_telefono(telefono_admin)
        if empleado_info:
            saludo = f"👋 ¡Hola {nombre_admin}! Bienvenido al panel de RRHH.\nEstoy acá para ayudarte a gestionar todo. 🛠️"

    if not saludo:
        saludo = f"👋 ¡Hola {nombre_admin}! Bienvenido al panel de RRHH."

    menu_text = (
        f"{saludo}\n\n"
        "📋 Panel del Administrador\n\n"
        "1️⃣ Agregar Empleado ➕\n"
        "2️⃣ Editar Empleado ✏️\n"
        "3️⃣ Eliminar Empleado 🗑️\n"
        "4️⃣ Ver Todos 👥\n"
        "5️⃣ Consultar Info 🔍\n"
        "6️⃣ Subir Archivo a Empleado ⬆️\n"
        "7️⃣ Próximos Cumples 📅\n"
        "8️⃣ Cerrar Sesión 🔒"
    )
    return menu_text


def mostrar_menu_empleado(nombre_empleado, telefono_empleado=None):
    """Muestra el menú para el rol de empleado con saludo dinámico y estilo mejorado."""
    saludo = ""
    if telefono_empleado:
        empleado_info = obtener_usuario_por_telefono(telefono_empleado)
        if empleado_info:
            saludo = f"👋 ¡Hola {nombre_empleado}! Soy tu asistente de RRHH.\nEstoy acá para ayudarte con tus consultas. 💼"

    if not saludo:
        saludo = f"👋 ¡Hola {nombre_empleado}! Bienvenido al Bot de RRHH."

    menu_text = (
        f"{saludo}\n\n"
        "📋 Menú Principal - Empleado\n\n"
        "1️⃣ Vacaciones 🏖️\n"
        "2️⃣ Préstamo 💰\n"
        "3️⃣ Cumpleaños y Edad 🎂\n"
        "4️⃣ Mi Información 🧾\n"
        "5️⃣ Mis Archivos 📁\n"
        "6️⃣ Subir Archivo ⬆️\n"
        "7️⃣ Próximos Cumples 📅\n"
        "8️⃣ Salir ❌"
    )
    return menu_text


# --- Funciones de Procesamiento de Opciones ---

def procesar_opcion_admin(usuario, opcion, current_state=None, base_url=""):
    """Procesa las opciones elegidas por un administrador."""
    response_text = ""
    next_state = None
    
    if opcion == "1":
        response_text = "Ingresá los datos del nuevo empleado en el siguiente formato:\n" \
                        "nombre, rol, sector, fecha_nacimiento (DD-MM-YYYY), fecha_ingreso (DD-MM-YYYY), " \
                        "vacaciones (días), préstamo (monto), notas, telefono (sin 'whatsapp:')\n" \
                        "Ejemplo: Juan Pérez, empleado, Ventas, 15-06-1990, 01-01-2015, 10, 5000, " \
                        "Buen rendimiento, 54911xxxxxxxx"
        next_state = "crear_empleado_paso_1_datos"
    elif opcion == "2":
        response_text = "Ingresá el ID del empleado que querés editar."
        next_state = "editar_empleado_paso_1_id"
    elif opcion == "3":
        response_text = "Ingresá el ID del empleado que querés eliminar."
        next_state = "eliminar_empleado_paso_1_id"
    elif opcion == "4":
        response_text = listar_todos_los_empleados()
        next_state = "menu_admin" # Vuelve al menú después de listar
    elif opcion == "5":
        response_text = "Ingresá el nombre o ID del empleado a consultar."
        next_state = "esperando_nombre_info_empleado"
    elif opcion == "6":
        response_text = "Ingresá el nombre del empleado a quien querés subir un archivo."
        next_state = "esperando_nombre_subir_archivo_admin_paso_1"
    elif opcion == "7": # Esta es la nueva posición para "Ver próximos cumpleaños"
        response_text = obtener_proximos_cumpleanos()
        next_state = "menu_admin" # Vuelve al menú después de mostrar
    elif opcion == "8": # Esta es la nueva posición para "Cerrar sesión"
        response_text = "Sesión cerrada. ¡Hasta luego!"
        registrar_log(usuario, "Admin cerró sesión.")
        next_state = "cerrar" # Indica al manejador principal que limpie el estado
    else:
        response_text = "❌ Opción no válida. Por favor, elegí una opción del menú."
        next_state = current_state # Mantiene el estado actual si la opción no es válida

    return response_text, next_state


def procesar_opcion_empleado(usuario, opcion, base_url=""):
    """Procesa las opciones elegidas por un empleado."""
    response_text = ""
    next_state = None

    if opcion == "1":
        response_text = consultar_dias_vacaciones(usuario["telefono"])
        next_state = "menu_empleado"
    elif opcion == "2":
        response_text = consultar_prestamo(usuario["telefono"])
        next_state = "menu_empleado"
    elif opcion == "3":
        # Esta opción en tu menú original era "Ver cumpleaños y edad" para el propio empleado
        response_text = consultar_cumpleanos_y_edad(usuario["telefono"]) 
        next_state = "menu_empleado"
    elif opcion == "4":
        response_text = ver_informacion_completa(usuario["telefono"])
        next_state = "menu_empleado"
    elif opcion == "5":
        response_text = listar_archivos_empleado(usuario["telefono"], base_url)
        next_state = "menu_empleado"
    elif opcion == "6":
        response_text = "📎Por favor, adjuntá el archivo que quieres subir a tu carpeta personal."
        next_state = "esperando_archivo_empleado"
    elif opcion == "7": # Esta es la nueva posición para "Ver próximos cumpleaños"
        response_text = obtener_proximos_cumpleanos()
        next_state = "menu_empleado" # Vuelve al menú después de mostrar
    elif opcion == "8": # Esta es la nueva posición para "Salir"
        response_text = "Sesión finalizada. ¡Hasta luego!"
        registrar_log(usuario, "Empleado cerró sesión.")
        next_state = "cerrar" # Indica al manejador principal que limpie el estado
    else:
        response_text = "❌ Opción no válida. Por favor, elegí una opción del menú."
        next_state = "menu_empleado" # Si la opción es inválida, vuelve a mostrar el menú.

    return response_text, next_state

# --- Funciones de Procesamiento de Empleados (EXISTENTES) ---

def obtener_usuario_por_telefono(telefono):
    """Busca un usuario por número de teléfono en empleados.json."""
    # print(f"[DEBUG] Intentando cargar empleados desde: {os.path.abspath('empleados.json')}") # Descomentar para depuración
    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados_data = json.load(f)
        # print(f"[DEBUG] Empleados cargados exitosamente.") # Descomentar para depuración
    except FileNotFoundError:
        print("Error: empleados.json no encontrado.")
        return None
    except json.JSONDecodeError:
        print("Error: Formato de empleados.json inválido.")
        return None

    telefono_limpio = str(telefono).replace("whatsapp:", "").replace("+", "").strip()
    # print(f"[DEBUG] Número recibido de Twilio: {telefono}") # Descomentar para depuración
    # print(f"[DEBUG] Número después de quitar 'whatsapp:': {telefono.replace('whatsapp:', '')}") # Descomentar para depuración
    # print(f"[DEBUG] Buscando usuario con teléfono limpio (final): {telefono_limpio}") # Descomentar para depuración

    for emp_id, emp_info in empleados_data.items():
        # Normalizar el teléfono guardado también por si tiene prefijos o espacios
        emp_telefono_limpio = str(emp_info.get("telefono", "")).replace("+", "").strip()
        
        # Considerar múltiples formatos posibles
        if emp_telefono_limpio == telefono_limpio:
            # print(f"[DEBUG] Usuario encontrado: {emp_info.get('nombre')}") # Descomentar para depuración
            return emp_info
        # Si el número de Twilio es +54911xxxx y el de JSON es 11xxxx (sin 549)
        if telefono_limpio.startswith("549") and emp_telefono_limpio == telefono_limpio[3:]:
            # print(f"[DEBUG] Usuario encontrado (coincidencia parcial 549): {emp_info.get('nombre')}") # Descomentar para depuración
            return emp_info
        # Si el número de Twilio es +5411xxxx y el de JSON es 11xxxx (sin 54)
        if telefono_limpio.startswith("54") and emp_telefono_limpio == telefono_limpio[2:]:
            # print(f"[DEBUG] Usuario encontrado (coincidencia parcial 54): {emp_info.get('nombre')}") # Descomentar para depuración
            return emp_info

    # print(f"[DEBUG] No se encontró usuario para el teléfono: {telefono_limpio}") # Descomentar para depuración
    return None

def registrar_log(usuario_info, mensaje):
    """Registra las acciones del bot en un archivo de log."""
    log_file = "bot_log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_identifier = usuario_info.get("nombre", usuario_info.get("telefono", "Desconocido"))
    log_entry = f"[{timestamp}] Usuario: {user_identifier} - Acción: {mensaje}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)

def procesar_datos_nuevo_empleado(message_body):
    """Procesa los datos para crear un nuevo empleado."""
    try:
        data = [item.strip() for item in message_body.split(',')]
        if len(data) != 9:
            return "❌ Formato incorrecto. Deben ser 9 campos separados por comas.", None

        nombre, rol, sector, fecha_nacimiento, fecha_ingreso, vacaciones_str, prestamo_str, notas, telefono = data
        
        # Validaciones básicas
        if rol.lower() not in ["admin", "empleado"]:
            return "❌ Rol inválido. Debe ser 'admin' o 'empleado'.", None
        
        try:
            vacaciones = int(vacaciones_str)
            prestamo = float(prestamo_str)
        except ValueError:
            return "❌ Vacaciones y Préstamo deben ser números válidos.", None
        
        # Validación de formato de fechas DD-MM-YYYY
        try:
            datetime.strptime(fecha_nacimiento, "%d-%m-%Y")
            datetime.strptime(fecha_ingreso, "%d-%m-%Y")
        except ValueError:
            return "❌ Formato de fecha incorrecto. Usá DD-MM-YYYY.", None

        empleados_data = {}
        try:
            with open("empleados.json", "r", encoding="utf-8") as f:
                empleados_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            empleados_data = {} # Si el archivo no existe o está vacío, crea un diccionario vacío
        
        # Generar un nuevo ID (el último ID + 1)
        new_id = str(max([int(k) for k in empleados_data.keys()] or [0]) + 1)

        empleados_data[new_id] = {
            "nombre": nombre,
            "rol": rol.lower(),
            "sector": sector,
            "fecha_nacimiento": fecha_nacimiento,
            "fecha_ingreso": fecha_ingreso,
            "vacaciones": vacaciones,
            "prestamo": prestamo,
            "notas": notas,
            "telefono": telefono.replace("+", "").strip(), # Asegurar el formato del teléfono
            "last_interaction_date": datetime.now().strftime("%Y-%m-%d") # Inicializar con la fecha actual
        }

        with open("empleados.json", "w", encoding="utf-8") as f:
            json.dump(empleados_data, f, indent=4, ensure_ascii=False)

        return f"✅ Empleado {nombre} agregado con ID {new_id}!", new_id
    except Exception as e:
        return f"❌ Error al procesar los datos: {e}. Asegurate del formato correcto.", None

def procesar_edicion_empleado(empleado_id, campo, nuevo_valor):
    """Procesa la edición de un empleado existente."""
    empleados_data = {}
    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "❌ Error: Archivo de empleados no encontrado o inválido.", False

    if empleado_id not in empleados_data:
        return f"❌ Empleado con ID *{empleado_id}* no encontrado.", False

    empleado = empleados_data[empleado_id]
    campo = campo.lower() # Normalizar el campo a minúsculas

    # Lista de campos permitidos y sus tipos de conversión
    allowed_fields = {
        "nombre": str, "rol": str, "sector": str, 
        "fecha_nacimiento": str, "fecha_ingreso": str, 
        "vacaciones": int, "prestamo": float, "notas": str, 
        "telefono": str, "last_interaction_date": str # Añadir last_interaction_date
    }

    if campo not in allowed_fields:
        return f"❌ Campo '{campo}' no es válido para edición. Campos permitidos: {', '.join(allowed_fields.keys())}.", False

    try:
        # Convertir el nuevo valor al tipo esperado por el campo
        if campo in ["vacaciones", "prestamo"]:
            converted_value = allowed_fields[campo](nuevo_valor)
            if converted_value < 0: # Validación adicional para números no negativos
                return f"❌ El valor para '{campo}' no puede ser negativo.", False
            empleado[campo] = converted_value
        elif campo == "rol":
            if nuevo_valor.lower() not in ["admin", "empleado"]:
                return "❌ Rol inválido. Debe ser 'admin' o 'empleado'.", False
            empleado[campo] = nuevo_valor.lower()
        elif campo in ["fecha_nacimiento", "fecha_ingreso", "last_interaction_date"]:
            # Validar formato de fecha DD-MM-YYYY o YYYY-MM-DD para last_interaction_date
            if campo in ["fecha_nacimiento", "fecha_ingreso"]:
                datetime.strptime(nuevo_valor, "%d-%m-%Y")
            elif campo == "last_interaction_date":
                datetime.strptime(nuevo_valor, "%Y-%m-%d")
            empleado[campo] = nuevo_valor
        elif campo == "telefono":
            empleado[campo] = nuevo_valor.replace("+", "").strip()
        else:
            empleado[campo] = allowed_fields[campo](nuevo_valor)

        with open("empleados.json", "w", encoding="utf-8") as f:
            json.dump(empleados_data, f, indent=4, ensure_ascii=False)

        return f"✅ Empleado ID *{empleado_id}* actualizado. Campo '{campo}' ahora es '{nuevo_valor}'.", True
    except ValueError:
        return f"❌ Error de formato para el campo '{campo}'. El valor '{nuevo_valor}' no es válido para este tipo.", False
    except Exception as e:
        return f"❌ Error desconocido al editar el empleado: {e}", False

def eliminar_empleado(empleado_id):
    """Elimina un empleado por su ID."""
    empleados_data = {}
    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "❌ Error: Archivo de empleados no encontrado o inválido."

    if empleado_id in empleados_data:
        del empleados_data[empleado_id]
        with open("empleados.json", "w", encoding="utf-8") as f:
            json.dump(empleados_data, f, indent=4, ensure_ascii=False)
        return f"✅ Empleado con ID *{empleado_id}* eliminado."
    else:
        return f"❌ Empleado con ID *{empleado_id}* no encontrado."

def listar_todos_los_empleados():
    """Lista todos los empleados con su ID y nombre."""
    empleados_data = {}
    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "❌ No hay empleados registrados."

    if not empleados_data:
        return "❌ No hay empleados registrados."
    
    response_lines = ["👥 *Lista de Empleados:*\n"]
    for emp_id, emp_info in empleados_data.items():
        response_lines.append(f"• ID: {emp_id} - Nombre: {emp_info.get('nombre', 'N/A')} ({emp_info.get('rol', 'N/A')})")
    return "\n".join(response_lines)

def obtener_info_empleado_por_nombre_o_id(query):
    """
    Obtiene información detallada de un empleado por nombre o ID,
    incluyendo el cálculo de antigüedad.
    """
    empleados_data = {}
    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "❌ No hay empleados registrados."

    empleado_encontrado = None
    if query.isdigit() and query in empleados_data:
        empleado_encontrado = empleados_data[query]
    else:
        # Buscar por nombre (insensible a mayúsculas/minúsculas)
        for emp_id, emp_info in empleados_data.items():
            if emp_info.get('nombre', '').lower() == query.lower():
                empleado_encontrado = emp_info
                break
    
    if empleado_encontrado:
        info_lines = [f"ℹ️ *Información de {empleado_encontrado['nombre']}:*\n"]
        for key, value in empleado_encontrado.items():
            if key != "telefono": # No mostrar el teléfono directamente por privacidad
                info_lines.append(f"• {key.replace('_', ' ').title()}: {value}")
        
        # --- Cálculo de Antigüedad ---
        fecha_ingreso_str = empleado_encontrado.get('fecha_ingreso')
        if fecha_ingreso_str:
            try:
                fecha_ingreso = datetime.strptime(fecha_ingreso_str, '%d-%m-%Y')
                hoy = datetime.now()
                antiguedad_anos = hoy.year - fecha_ingreso.year - ((hoy.month, hoy.day) < (fecha_ingreso.month, fecha_ingreso.day))
                antiguedad_meses = hoy.month - fecha_ingreso.month
                if antiguedad_meses < 0:
                    antiguedad_meses += 12

                info_lines.append(f"• Antigüedad: {antiguedad_anos} años y {antiguedad_meses} meses")
            except ValueError:
                info_lines.append("• Antigüedad: Fecha de ingreso inválida")
        else:
            info_lines.append("• Antigüedad: No disponible")

        return "\n".join(info_lines)
    else:
        return f"❌ Empleado '{query}' no encontrado por nombre o ID."

def consultar_dias_vacaciones(telefono):
    """Consulta los días de vacaciones de un empleado."""
    usuario = obtener_usuario_por_telefono(telefono)
    if usuario and "vacaciones" in usuario:
        return f"🏖️ Tenés {usuario['vacaciones']} días de vacaciones disponibles."
    return "❌ No se pudo obtener la información de vacaciones."

def consultar_prestamo(telefono):
    """Consulta el monto del préstamo de un empleado."""
    usuario = obtener_usuario_por_telefono(telefono)
    if usuario:
        prestamo = usuario.get("prestamo")
        if isinstance(prestamo, (int, float)) and prestamo > 0:
            return f"💰 Tu préstamo actual es de ${prestamo:,.2f}."
        else:
            return "ℹ️ No tenés un préstamo registrado actualmente."
    return "❌ No se pudo obtener la información del préstamo."

def consultar_cumpleanos_y_edad(telefono):
    """
    Consulta la fecha de cumpleaños y edad de un empleado,
    calculando la edad que cumplirá y los días restantes.
    """
    usuario = obtener_usuario_por_telefono(telefono)
    if usuario and "fecha_nacimiento" in usuario and usuario["fecha_nacimiento"]:
        try:
            nacimiento = datetime.strptime(usuario["fecha_nacimiento"], "%d-%m-%Y")
            hoy = datetime.now()
            
            # Calcular edad que cumplirá
            edad_a_cumplir = hoy.year - nacimiento.year
            proximo_cumple = datetime(hoy.year, nacimiento.month, nacimiento.day)
            
            if proximo_cumple < hoy:
                proximo_cumple = datetime(hoy.year + 1, nacimiento.month, nacimiento.day)
                edad_a_cumplir += 1
            
            dias_para_cumple = (proximo_cumple - hoy).days

            response_text = f"🎂 Tu cumpleaños es el {nacimiento.strftime('%d de %B').replace('January', 'Enero').replace('February', 'Febrero').replace('March', 'Marzo').replace('April', 'Abril').replace('May', 'Mayo').replace('June', 'Junio').replace('July', 'Julio').replace('August', 'Agosto').replace('September', 'Septiembre').replace('October', 'Octubre').replace('November', 'Noviembre').replace('December', 'Diciembre')}."
            
            if dias_para_cumple == 0:
                response_text += f" ¡Es hoy! 🎉 Cumplís {edad_a_cumplir} años."
            elif dias_para_cumple == 1:
                response_text += f" ¡Es mañana! 🎂 Cumplirás {edad_a_cumplir} años."
            elif dias_para_cumple > 1:
                response_text += f" Faltan {dias_para_cumple} días para tu próximo cumpleaños. Cumplirás {edad_a_cumplir} años."
            return response_text
        except ValueError:
            return "❌ Fecha de nacimiento no válida."
    return "❌ No se pudo obtener la información de cumpleaños."

def listar_archivos_empleado(telefono, base_url):
    """Lista los archivos de un empleado desde la carpeta static/archivos/Apellido_Nombre."""
    usuario = obtener_usuario_por_telefono(telefono)
    if not usuario:
        return "❌ No se encontró tu información de empleado."

    apellido = usuario.get("apellido", "SinApellido").strip().replace(" ", "_")
    nombre = usuario.get("nombre", "SinNombre").strip().replace(" ", "_")
    folder_name = f"{apellido}_{nombre}"
    folder_path = os.path.join("static", "archivos", folder_name)

    if not os.path.exists(folder_path) or not os.listdir(folder_path):
        return f"📁 No tenés archivos subidos en tu carpeta personal."

    response_lines = [f"📁 *Tus archivos ({usuario['nombre']}):*\n"]
    for filename in os.listdir(folder_path):
        file_url = f"{base_url}/static/archivos/{folder_name}/{filename}".replace(" ", "%20")
        response_lines.append(f"• {filename} → {file_url}")  # Acá armamos el link completo

    return "\n".join(response_lines)


def ver_informacion_completa(telefono):
    """
    Muestra toda la información del empleado (excepto el teléfono directo),
    incluyendo el cálculo de antigüedad.
    """
    usuario = obtener_usuario_por_telefono(telefono)
    if not usuario:
        return "❌ No se pudo obtener tu información completa."

    info_lines = [f"ℹ️ *Tu Información Completa ({usuario['nombre']}):*\n"]
    for key, value in usuario.items():
        if key != "telefono": # No mostrar el teléfono directamente por privacidad
            info_lines.append(f"• {key.replace('_', ' ').title()}: {value}")
    
    # --- Cálculo de Antigüedad ---
    fecha_ingreso_str = usuario.get('fecha_ingreso')
    if fecha_ingreso_str:
        try:
            fecha_ingreso = datetime.strptime(fecha_ingreso_str, '%d-%m-%Y')
            hoy = datetime.now()
            antiguedad_anos = hoy.year - fecha_ingreso.year - ((hoy.month, hoy.day) < (fecha_ingreso.month, fecha_ingreso.day))
            antiguedad_meses = hoy.month - fecha_ingreso.month
            if antiguedad_meses < 0:
                antiguedad_meses += 12

            info_lines.append(f"• Antigüedad: {antiguedad_anos} años y {antiguedad_meses} meses")
        except ValueError:
            info_lines.append("• Antigüedad: Fecha de ingreso inválida")
    else:
        info_lines.append("• Antigüedad: No disponible")

    return "\n".join(info_lines)


def obtener_proximos_cumpleanos():
    """
    Obtiene una lista de los próximos cumpleaños (en los próximos 30 días)
    ordenados por fecha, incluyendo la edad que cumplirán.
    """
    empleados_data = {}
    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados_data = json.load(f)
    except FileNotFoundError:
        return "❌ Error: Archivo de empleados no encontrado."
    except json.JSONDecodeError:
        return "❌ Error: Formato de archivo de empleados inválido."

    hoy = datetime.now()
    cumpleanos_proximos = []

    for emp_id, emp_info in empleados_data.items():
        if "fecha_nacimiento" in emp_info and emp_info["fecha_nacimiento"]:
            try:
                dia, mes, anio_nacimiento = map(int, emp_info["fecha_nacimiento"].split('-'))
                
                # Calcular la edad actual
                edad_actual = hoy.year - anio_nacimiento - ((hoy.month, hoy.day) < (mes, dia))

                # Crear una fecha de cumpleaños para el año actual
                cumple_este_anio = datetime(hoy.year, mes, dia)

                # Si el cumpleaños ya pasó este año, considerar el del próximo año
                if cumple_este_anio < hoy:
                    cumple_proximo_ocasion = datetime(hoy.year + 1, mes, dia)
                    edad_a_cumplir = edad_actual + 1
                else:
                    cumple_proximo_ocasion = cumple_este_anio
                    edad_a_cumplir = edad_actual
                
                # Calcular la diferencia de días
                dias_restantes = (cumple_proximo_ocasion - hoy).days

                # Si está dentro de los próximos 30 días o es hoy, agrégalo
                if 0 <= dias_restantes <= 30:
                    cumpleanos_proximos.append({
                        "nombre": emp_info["nombre"],
                        "fecha": cumple_proximo_ocasion,
                        "dias_restantes": dias_restantes,
                        "edad_a_cumplir": edad_a_cumplir 
                    })
            except (ValueError, IndexError):
                print(f"Advertencia: Fecha de nacimiento inválida para {emp_info.get('nombre', emp_id)}: {emp_info.get('fecha_nacimiento')}")
                continue

    cumpleanos_proximos.sort(key=lambda x: x["fecha"])

    if not cumpleanos_proximos:
        return "🎉 No hay próximos cumpleaños en los próximos 30 días."
    
    response_lines = ["🎉 *Próximos Cumpleaños (próximos 30 días):*\n"]
    for cumple in cumpleanos_proximos:
        fecha_formato = cumple["fecha"].strftime("%d de %B").replace("January", "Enero").replace("February", "Febrero") \
                                     .replace("March", "Marzo").replace("April", "Abril").replace("May", "Mayo").replace("June", "Junio") \
                                     .replace("July", "Julio").replace("August", "Agosto").replace("September", "Septiembre") \
                                     .replace("October", "Octubre").replace("November", "Noviembre").replace("December", "Diciembre")

        if cumple["dias_restantes"] == 0:
            response_lines.append(f"• {cumple['nombre']}: ¡Es hoy! 🎉 Cumple {cumple['edad_a_cumplir']} años.")
        elif cumple["dias_restantes"] == 1:
            response_lines.append(f"• {cumple['nombre']} ({fecha_formato}): Mañana 🎂 Cumple {cumple['edad_a_cumplir']} años.")
        else:
            response_lines.append(f"• {cumple['nombre']} ({fecha_formato}): en {cumple['dias_restantes']} días. Cumplirá {cumple['edad_a_cumplir']} años.")
    
    return "\n".join(response_lines)

import requests

def guardar_archivo_enviado_por_whatsapp(telefono, media_url, media_type, media_filename=None):
    """Guarda un archivo recibido por WhatsApp en la carpeta del empleado."""
    usuario = obtener_usuario_por_telefono(telefono)
    if not usuario:
        return "❌ No se encontró tu información para guardar el archivo."

    apellido = usuario.get("apellido", "SinApellido").strip().replace(" ", "_")
    nombre = usuario.get("nombre", "SinNombre").strip().replace(" ", "_")
    carpeta = os.path.join("static", "archivos", f"{apellido}_{nombre}")
    os.makedirs(carpeta, exist_ok=True)

    if not media_filename:
        extension = media_type.split("/")[-1]  # ejemplo: image/jpeg → jpeg
        media_filename = f"archivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"

    ruta_destino = os.path.join(carpeta, media_filename)

    try:
        respuesta = requests.get(media_url)
        if respuesta.status_code == 200:
            with open(ruta_destino, "wb") as f:
                f.write(respuesta.content)
            return f"✅ Archivo recibido y guardado como *{media_filename}*."
        else:
            return f"❌ Error al descargar el archivo (status {respuesta.status_code})."
    except Exception as e:
        return f"❌ Error al guardar el archivo: {e}"
