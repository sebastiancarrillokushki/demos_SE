# 🍽️ Kushki's Restaurant - Cloud Terminal API Demo

Una aplicación de demostración que simula un restaurante usando la Cloud Terminal API de Kushki para procesar pagos en México y Chile.

## 🚀 Características

- **Interfaz de restaurante**: Menú visual con productos y precios
- **Soporte multi-país**: México y Chile con monedas locales (MXN/CLP)
- **Integración Cloud Terminal API**: Procesamiento de pagos en tiempo real
- **Webhooks**: Recepción automática de confirmaciones de pago
- **Devoluciones**: Funcionalidad para procesar reembolsos
- **Interfaz moderna**: Diseño responsive con Streamlit

## 🛠️ Tecnologías

- **Frontend**: Streamlit
- **Backend**: Python
- **APIs**: Kushki Cloud Terminal API
- **Deployment**: Render

## 📋 Requisitos

- Python 3.8+
- Cuenta en Kushki con acceso a Cloud Terminal API
- Credenciales de API para México y Chile

## 🚀 Instalación Local

1. **Clona el repositorio**
   ```bash
   git clone https://github.com/tu-usuario/kushki-restaurant.git
   cd kushki-restaurant
   ```

2. **Instala las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecuta la aplicación**
   ```bash
   streamlit run app.py
   ```

4. **Abre tu navegador**
   - Ve a `http://localhost:8501`

## 🌐 Deployment en Render

### Configuración Automática

1. **Conecta tu repositorio de GitHub a Render**
2. **Crea un nuevo Web Service**
3. **Configura las siguientes variables**:

#### Variables de Entorno (Opcional)
```bash
# Para desarrollo local
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

#### Configuración del Build
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`

### Configuración Manual

Si necesitas configurar manualmente:

1. **En Render Dashboard**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`

2. **Variables de entorno** (si las necesitas):
   - `PORT`: Render lo asigna automáticamente
   - `STREAMLIT_SERVER_PORT`: `$PORT`
   - `STREAMLIT_SERVER_ADDRESS`: `0.0.0.0`

## 📁 Estructura del Proyecto

```
kushki-restaurant/
├── app.py                 # Aplicación principal
├── webhook_server.py      # Servidor de webhooks
├── requirements.txt       # Dependencias Python
├── README.md             # Este archivo
├── .gitignore            # Archivos a ignorar
├── Imagenes/             # Imágenes de productos
│   ├── Hamburguesa.png
│   ├── Tacos.png
│   ├── Pizza.png
│   ├── Refresco.png
│   ├── Cerveza.png
│   ├── Agua.png
│   └── Propina.png
└── kushki_logo.png       # Logo de Kushki
```

## 🔧 Configuración de APIs

### México (BillPocket)
- **Endpoint**: `https://kushkicollect.billpocket.dev/`
- **Headers**: `X-BP-AUTH: {api_key}`

### Chile (Haulmer)
- **Endpoint**: `https://integrations.payment.haulmer.com/`
- **Headers**: `X-API-Key: {api_key}`

## 📊 Funcionalidades

### 1. Selección de País e Ingeniero
- Configuración automática según el país seleccionado
- Credenciales pre-configuradas para demostración

### 2. Menú de Productos
- Interfaz visual con imágenes de productos
- Precios en moneda local
- Sistema de carrito integrado

### 3. Procesamiento de Pagos
- Envío automático a terminal física
- Espera de confirmación vía webhook
- Fallback a consulta de estado si no llega webhook

### 4. Gestión de Transacciones
- Visualización de payloads enviados
- Respuestas de API en tiempo real
- Sistema de devoluciones

## 🔒 Seguridad

- Las credenciales de API están hardcodeadas para demostración
- En producción, usar variables de entorno
- Los archivos temporales se excluyen del control de versiones

## 🐛 Troubleshooting

### Problemas Comunes

1. **Error de conexión con API**
   - Verifica las credenciales de API
   - Confirma que el serial number esté activo

2. **Webhook no llega**
   - La aplicación tiene fallback automático
   - Consulta el estado manualmente si es necesario

3. **Error en Render**
   - Verifica que el puerto esté configurado correctamente
   - Revisa los logs de build

## 📝 Notas de Desarrollo

- La aplicación está diseñada para demostración
- Los precios son simulados
- Las transacciones se procesan en ambiente de pruebas

## 🤝 Contribuciones

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o preguntas sobre la Cloud Terminal API:
- 📧 Email: soporte@kushki.com
- 🌐 Web: https://www.kushki.com
- 📚 Docs: https://docs.kushki.com

---

**Desarrollado con ❤️ por el equipo de Kushki** 