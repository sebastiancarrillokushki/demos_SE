import streamlit as st
import requests
import uuid
import json
import os
import time
from streamlit_autorefresh import st_autorefresh
import base64

st.set_page_config(page_title="Kushki's Restaurant", layout="centered")

# Logo
st.image("kushki_logo.png", width=200)

# CSS adicional (opcional)
st.markdown("""
    <style>
        .main {
            background-color: #FFFFFF;
            padding: 20px;
            border-radius: 10px;
        }
        h1, h2, h3 {
            color: #023365;
        }
        .stButton>button {
            background-color: #023365;
            color: white;
            border-radius: 8px;
        }
        .stSelectbox>div>div>div {
            background-color: #F4F5F7;
        }
        .element-container input[type="number"] {
        text-align: center !important;
    }
    </style>
""", unsafe_allow_html=True)


def limpiar_archivos_estado():
    for archivo in ["payload_enviado.json", "payload_cancelacion.json", "respuesta_pago.json"]:
        if os.path.exists(archivo):
            os.remove(archivo)

def construir_payload_mexico(serial, total, reference, propina, show_notification, auto_payment_enabled, enable_dialog_tip):
    payload = {
        "serialNumber": serial,
        "amount": total,
        "identifier": reference,
        "uniqueReference": reference,
        "description": "Compra en restaurante",
        "showNotification": show_notification,
        "ttl": 60,
        "msi": 0,
        "deviceToken": "58e9a981",
        "extras": {
            "autoPaymentEnabled": auto_payment_enabled,
            "timerFinishTRX": 10,
            "enableDialogTip": enable_dialog_tip
        }
    }
    if propina > 0:
        payload["tip"] = propina
    return payload

def construir_payload_chile(serial, total, reference):
    return {
        "idempotencyKey": reference,
        "amount": total,
        "device": serial,
        "description": "Compra Test",
        "dteType": 0,
        "extraData": {
            "exemptAmount": 0,
            "customFields": [
                {"name": "Kiosko", "value": "2", "print": True},
                {"name": "Terminal", "value": "15", "print": True},
                {"name": "MID", "value": "21887398273982", "print": False}
            ],
            "sourceName": "Kushki's Restaurant",
            "sourceVersion": "12.3"
        }
    }

def enviar_pago(url, headers, payload):
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        with open("payload_enviado.json", "w") as f:
            json.dump(payload, f)
        with open("respuesta_pago.json", "w") as f:
            try:
                json.dump(response.json(), f)
            except:
                json.dump({}, f)
        return response
    except Exception as e:
        st.error(f"❌ Error al conectar con la API: {e}")
        return None

def mostrar_archivo_json(titulo, ruta):
    if os.path.exists(ruta):
        with open(ruta, "r") as f:
            contenido = json.load(f)
        st.subheader(titulo)
        st.code(json.dumps(contenido, indent=2), language="json")

def inicializar_estado():
    if "pago_enviado" not in st.session_state:
        st.session_state["pago_enviado"] = False
    if "transaccion_cancelada" not in st.session_state:
        st.session_state["transaccion_cancelada"] = False

def verificar_estado_api_si_no_llega_webhook(pais, referencia, api_key):
    intentos = 0
    while intentos < 10:
        # --- NUEVO: Verificar si el webhook ya llegó consultando el endpoint remoto ---
        estado_remoto = obtener_estado_remoto()
        if estado_remoto and estado_remoto.get("uniqueReference") == referencia:
            # Webhook llegó, se rompe el ciclo
            return

        time.sleep(30)
        intentos += 1

        if pais == "México":
            url = f"https://kushkicollect.billpocket.dev/get-status/?uniqueReference={referencia}"
            headers = {"X-BP-AUTH": api_key}
        else:
            url = f"https://integrations.payment.haulmer.com/RemotePayment/v2/GetPaymentRequest/{referencia}"
            headers = {
                "X-API-Key": api_key,
                "User-Agent": "PostmanRuntime/7.32.3"
            }

        try:
            response = requests.get(url, headers=headers)
            st.subheader(f"🔎 Verificación #{intentos} - Consulta a la API:")
            st.write("📡 Endpoint:", url)
            st.code(json.dumps(response.json(), indent=2), language="json")

            status = response.json().get("status", "").lower()
            if status in ["cancelled", "canceled"]:
                with open("respuesta_api_get_estatus.json", "w") as f:
                    try:
                        json.dump(response.json(), f)
                    except:
                        json.dump({"error": "Respuesta no es JSON"}, f)

                st.warning("⚠️ La transacción fue cancelada por la terminal.")
                session_keys = list(st.session_state.keys())
                for key in session_keys:
                    if key != "transaccion_cancelada":
                        del st.session_state[key]
                st.session_state["transaccion_cancelada"] = True
                st.rerun()
            else:
                if status in ["Approved", "Approve"]:
                    st.rerun()
                else:
                    st.info("⚠️ No se ha recibido el webhook. ")
        except Exception as e:
            st.error(f"❌ Error consultando el estado: {e}")

WEBHOOK_BASE_URL = "https://webhook-server-ctapi.onrender.com"

def obtener_estado_remoto():
    try:
        response = requests.get(f"{WEBHOOK_BASE_URL}/get-estado", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error consultando estado remoto: {e}")
    return None

def obtener_devolucion_remota():
    try:
        response = requests.get(f"{WEBHOOK_BASE_URL}/get-devolucion", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error consultando devolución remota: {e}")
    return None

def mostrar_estado_webhook():
    estado = obtener_estado_remoto()
    referencia_esperada = st.session_state.get("ultima_referencia")
    referencia_recibida = estado.get("uniqueReference") if estado else None
    if estado:
        result = estado.get("result") or estado.get("status")
        ref = estado.get("uniqueReference", "[sin referencia]")
        if ref == referencia_esperada:
            # Si el webhook llega por primera vez, forzar recarga para limpiar estado
            if not st.session_state.get("webhook_mostrado"):
                st.session_state["webhook_mostrado"] = True
                st.rerun()
            st.subheader("📦 Webhook recibido:")
            st.code(json.dumps(estado, indent=2), language="json")
            st.subheader("📊 Resultado del pago:")
            if result and result.lower() in ["aprobada", "approved"]:
                st.success("✅ ¡Pago aprobado correctamente!")
                # Timer solo si no ha finalizado
                if not st.session_state.get("timer_finalizado"):
                    st.info("⏱️ Tiempo restante para completar la acción: 1 minuto")
                    countdown_placeholder = st.empty()
                    for i in range(60, 0, -1):
                        countdown_placeholder.info(f"⏳ {i} segundos restantes")
                        time.sleep(1)
                    st.session_state["timer_finalizado"] = True
                    st.rerun()
            elif result and result.lower() in ["rechazada", "rechazadaprosa", "declined"]:
                st.error("❌ El pago fue rechazado.")
            elif result and result.lower() == "cancelled":
                st.warning("⚠️ El cliente canceló el pago.")
            else:
                st.info(f"ℹ️ Estado del pago: {result or 'desconocido'}")
            st.subheader("💸 Solicitud de devolución")
            # Botón solo si el timer terminó (NO antes)
            if st.session_state.get("timer_finalizado"):
                if st.button("📤 Solicitar devolución"):
                    with st.spinner("Enviando solicitud de devolución..."):
                        payload = {"uniqueReference": ref}
                        with open("payload_cancelacion.json", "w") as f:
                            json.dump(payload, f)
                        headers = {
                            "X-BP-AUTH": st.session_state.get("api_key", ""),
                            "Content-Type": "application/json"
                        }
                        url = "https://kushkicollect.billpocket.dev/refund"
                        response = requests.post(url, json=payload, headers=headers)
                        st.subheader("📦 Payload de devolución enviado")
                        st.code(json.dumps(payload, indent=2), language="json")
                        st.subheader("📨 Respuesta de la API")
                        st.code(json.dumps(response.json(), indent=2), language="json")

def mostrar_webhook_devolucion():
    devolucion = obtener_devolucion_remota()
    if devolucion:
        result = devolucion.get("result") or devolucion.get("status")
        ref = devolucion.get("uniqueReference", "[sin referencia]")
        if ref == st.session_state.get("ultima_referencia"):
            st.subheader("📦 Webhook recibido (devolución)")
            st.code(json.dumps(devolucion, indent=2), language="json")
            st.subheader("📊 Resultado de la devolución:")
            if result and result.lower() in ["aprobada", "approved"]:
                st.success("✅ ¡Devolución procesada correctamente!")
            elif result and result.lower() in ["rechazada", "declined"]:
                st.error("❌ La devolución fue rechazada.")
            else:
                st.info(f"ℹ️ Estado: {result or 'desconocido'}")


# === Interfaz de configuración inicial ===
st.subheader("🌎 Selecciona el país de operación")
pais = st.selectbox("País", ["Seleccionar...", "México", "Chile"])

ingenieros_config = {
    "México": {
        "Juanse": {
            "serial": "TJ54239M21196",
            "api_key": "78197c2d035dc6f8297e8fdfc8ebbabfb8f2ab209ce3ce1d19a283e3786ae975"
        }
    },
    "Chile": {
        "Juanse": {
            "serial": "TJ71246J20345",
            "api_key": "IGdVHHeImV0CK3LTIaSDVVvK3EjuDSkNODagTWAsfMETq4fK5h28JszFQbu3324wUL9xT8VOyJdvw5LYQYtyjWUKftcKriDMqXyYYDK5WAeNCnMJPOZavPwrK6oagH"
        }
    }
}

if pais != "Seleccionar...":
    st.subheader("👤 Selecciona el ingeniero de preventa")
    ingeniero = st.selectbox("Ingeniero", ["Seleccionar..."] + list(ingenieros_config[pais].keys()))
    if ingeniero != "Seleccionar...":
        config = ingenieros_config[pais][ingeniero]
        serial_number = config["serial"]
        api_key = config["api_key"]
        simbolo_moneda = "MXN" if pais == "México" else "CLP"

        st.success(f"✅ Operando en {pais} con {ingeniero}")

        productos = {
            "México": {
                "Hamburguesa": 120,
                "Tacos": 90,
                "Pizza": 150,
                "Refresco": 30,
                "Cerveza": 60,
                "Agua": 25
            },
            "Chile": {
                "Hamburguesa": 7000,
                "Tacos": 5000,
                "Pizza": 8500,
                "Refresco": 1800,
                "Cerveza": 3500,
                "Agua": 1200
            }
            # Cargar imágenes locales
            

        }[pais]


        imagenes_productos = {
                producto: f"Imagenes/{producto}.png" for producto in productos.keys()
            }

        st.subheader("🛒 Menú")
        carrito = {}
        
        productos_lista = list(productos.items())
        for fila in range(0, len(productos_lista), 3):
            cols = st.columns(3)
            for i in range(3):
                if fila + i < len(productos_lista):
                    producto, precio = productos_lista[fila + i]
                    with cols[i]:
                        try:
                            ruta = f"Imagenes/{producto}.png"
                            imagen_b64 = base64.b64encode(open(ruta, "rb").read()).decode()
                            st.markdown(f"""
                                <div style='text-align: center; padding: 15px; height: 240px; border-radius: 10px; background-color: #f8f9fa; box-shadow: 1px 1px 6px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between;'>
                                    <img src='data:image/png;base64,{imagen_b64}' style='height: 80px; object-fit: contain; margin: auto;' />
                                    <div style='font-weight: bold; font-size: 16px; margin-top: 8px;'>{precio} {simbolo_moneda}</div>
                                    <div style='margin-top: 4px;'>{producto}</div>
                                </div>
                            """, unsafe_allow_html=True)
                        except FileNotFoundError:
                            st.warning(f"Imagen no encontrada para {producto}")
                        cantidad = st.number_input(
                            label=f"Cantidad de {producto}", key=producto, min_value=0, max_value=10, step=1, label_visibility="collapsed"
                        )
                        if cantidad > 0:
                            carrito[producto] = (cantidad, precio)

        # Tarjeta visual de propina dentro de columna central alineada con el resto
        fila_propina = st.columns(3)
        with fila_propina[0]:
            st.empty()
        with fila_propina[1]:
            st.markdown(f"""
                <div style='text-align: center; padding: 15px; height: 240px; border-radius: 10px; background-color: #f8f9fa; box-shadow: 1px 1px 6px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between;'>
                    <img src='data:image/png;base64,{base64.b64encode(open(f"Imagenes/Propina.png","rb").read()).decode()}' style='height: 80px; object-fit: contain; margin: auto;' />
                    <div style='font-weight: bold; font-size: 16px;'>Propina {simbolo_moneda}</div>
                    <div style='margin-top: 4px;'>Opcional</div>
                </div>
            """, unsafe_allow_html=True)
        with fila_propina[2]:
            st.empty()

        # Input centrado abajo
        espacio_izq2, input_col, espacio_der2 = st.columns([3, 2, 3])
        with input_col:
            propina = st.number_input("Propina", min_value=0, step=1, key="propina", label_visibility="collapsed")

        # Mostrar checkboxes para México antes del botón de pago
        if pais == "México":
            show_notification = st.checkbox("showNotification", value=False, key="showNotification")
            auto_payment_enabled = st.checkbox("autoPaymentEnabled", value=True, key="autoPaymentEnabled")
            enable_dialog_tip = st.checkbox("enableDialogTip", value=False, key="enableDialogTip")

        if carrito:
            st.subheader("🧾 Resumen del pedido:")
            total = sum(c * p for (c, p) in carrito.values())
            for producto, (cantidad, precio) in carrito.items():
                st.write(f"{producto} x {cantidad} = {cantidad * precio} {simbolo_moneda}")
            if propina > 0:
                st.write(f"Propina: {propina} {simbolo_moneda}")
            st.write(f"**Total a pagar: {total + propina} {simbolo_moneda}**")

            inicializar_estado()

            if not st.session_state["pago_enviado"]:
                if st.button("📲 Enviar a terminal para pagar"):
                    st.session_state["ultima_referencia"] = uuid.uuid4().hex
                    limpiar_archivos_estado()

                    if pais == "México":
                        payload = construir_payload_mexico(
                            serial_number, total, st.session_state["ultima_referencia"], propina,
                            show_notification, auto_payment_enabled, enable_dialog_tip
                        )
                        headers = {"X-BP-AUTH": api_key, "Content-Type": "application/json"}
                        url = "https://kushkicollect.billpocket.dev/v2/push-notifications"
                    else:
                        payload = construir_payload_chile(serial_number, total + propina, st.session_state["ultima_referencia"])
                        headers = {"X-API-Key": api_key, "Content-Type": "application/json", "User-Agent": "PostmanRuntime/7.32.3"}
                        url = "https://integrations.payment.haulmer.com/RemotePayment/v2/Create"

                    response = enviar_pago(url, headers, payload)
                    if response:
                        st.session_state["pago_enviado"] = True
                        st.session_state["api_key"] = api_key
                        st.success("✅ Solicitud enviada correctamente. Esperando webhook...")

# Mostrar resultados después del envío
if "ultima_referencia" in st.session_state:
    mostrar_archivo_json("📤 Payload enviado a Cloud Terminal API", "payload_enviado.json")
    mostrar_archivo_json("📨 Respuesta de la API", "respuesta_pago.json")
    verificar_estado_api_si_no_llega_webhook(pais, st.session_state["ultima_referencia"], api_key)

    estado = obtener_estado_remoto()
    webhook_recibido = estado and estado.get("uniqueReference") == st.session_state.get("ultima_referencia")
    timer_finalizado = st.session_state.get("timer_finalizado")
    if webhook_recibido:
        mostrar_estado_webhook()
        mostrar_webhook_devolucion()
    else:
        if not timer_finalizado:
            st_autorefresh(interval=3000, limit=10, key="espera_webhook")
            st.info("⏳ Procesando transacción... esperando confirmación del pago.")

# Botón para nueva transacción (en la parte inferior, fuera de mostrar_estado_webhook)
if "ultima_referencia" in st.session_state:
    st.divider()
    if st.button("🧾 Nueva transacción"):
        limpiar_archivos_estado()
        for clave in ["ultima_referencia", "temporizador_mostrado", "pago_enviado", "api_key", "webhook_mostrado", "timer_finalizado"]:
            if clave in st.session_state:
                del st.session_state[clave]
        for producto in ["Hamburguesa", "Tacos", "Pizza", "Refresco", "Cerveza", "Agua"]:
            st.session_state[producto] = 0  # Reiniciar a 0 explícitamente
        st.session_state["propina"] = 0  # Reiniciar propina a 0
        st.rerun()

if st.session_state.get("transaccion_cancelada"):
    mostrar_archivo_json("📤 Payload enviado a Cloud Terminal API", "payload_enviado.json")
    mostrar_archivo_json("📨 Respuesta de la API", "respuesta_pago.json")
    mostrar_archivo_json("🔎 Última verificación de estado (API)", "respuesta_api_get_estatus.json")
    st.divider()
    st.warning("🛑 Transacción cancelada en la terminal. Puedes iniciar una nueva.")
    if st.button("🧾 Nueva transacción"):
        limpiar_archivos_estado()
        keys_to_clear = list(st.session_state.keys())
        for key in keys_to_clear:
            if key != "mostrar_boton_nueva_trx":
                del st.session_state[key]
        for producto in ["Hamburguesa", "Tacos", "Pizza", "Refresco", "Cerveza", "Agua"]:
            st.session_state[producto] = 0  # Reiniciar a 0 explícitamente
        st.session_state["propina"] = 0  # Reiniciar propina a 0
        st.session_state["mostrar_boton_nueva_trx"] = True
        st.rerun()

