# 🚌 Terminal Terrestre — Sistema de Control de Acceso
### Terminal Terrestre "Mons. Santiago Fernández García" · Alcaldía de Calvas · Cariamanga

Sistema web para generación automática de tickets QR integrado con torniquetes Hikvision vía ISAPI, con panel administrativo, control de ventas y reporte oficial de recaudaciones.

---

## 📋 Contenido

1. [Requisitos](#1-requisitos)
2. [Instalar Python](#2-instalar-python)
3. [Instalar PostgreSQL](#3-instalar-postgresql)
4. [Crear la base de datos](#4-crear-la-base-de-datos)
5. [Descargar y preparar el proyecto](#5-descargar-y-preparar-el-proyecto)
6. [Configurar el archivo .env](#6-configurar-el-archivo-env)
7. [Instalar dependencias Python](#7-instalar-dependencias-python)
8. [Crear las tablas y cargar datos iniciales](#8-crear-las-tablas-y-cargar-datos-iniciales)
9. [Iniciar el sistema](#9-iniciar-el-sistema)
10. [Credenciales de acceso](#10-credenciales-de-acceso)
11. [Uso del sistema](#11-uso-del-sistema)
12. [Configurar la conexión Hikvision](#12-configurar-la-conexión-hikvision)
13. [Producción con Waitress](#13-producción-con-waitress)
14. [Solución de problemas](#14-solución-de-problemas)

---

## 1. Requisitos

Antes de empezar necesitas instalar dos programas:

| Programa   | Versión | Enlace de descarga |
|------------|---------|-------------------|
| Python     | 3.11 o superior | https://www.python.org/downloads/ |
| PostgreSQL | 16      | https://www.enterprisedb.com/downloads/postgres-postgresql-downloads |

> **Node.js NO es necesario.** El sistema usa Django con plantillas HTML directamente, sin React.

---

## 2. Instalar Python

1. Entra a https://www.python.org/downloads/ y descarga la última versión de Python 3.11 o superior.

2. Ejecuta el instalador. **MUY IMPORTANTE:** en la primera pantalla del instalador marca la casilla que dice **"Add Python to PATH"** antes de hacer clic en *Install Now*.

   ```
   ☑ Add Python to PATH     ← MARCAR ESTO
   ```

3. Cuando termine, abre **PowerShell** (búscalo en el menú inicio) y verifica la instalación:

   ```powershell
   python --version
   pip --version
   ```

   Debes ver algo como `Python 3.11.x` y `pip 24.x`. Si aparece un error, revisa la sección [Python no se reconoce](#python-no-se-reconoce-como-comando).

---

## 3. Instalar PostgreSQL

1. Entra a https://www.enterprisedb.com/downloads/postgres-postgresql-downloads y descarga **PostgreSQL 16** para Windows x86-64.

2. Ejecuta el instalador. Usa los valores por defecto en todo excepto:
   - **Contraseña del superusuario:** pon una contraseña que recuerdes, por ejemplo `postgres123`. La necesitarás más adelante.
   - **Puerto:** déjalo en `5432`.

3. Cuando el instalador pregunte si quieres instalar Stack Builder, puedes decir **No**.

4. Verifica que PostgreSQL quedó instalado abriendo el menú inicio y buscando **"SQL Shell (psql)"**. Si aparece en el menú, la instalación fue exitosa.

---

## 4. Crear la base de datos

1. Abre **SQL Shell (psql)** desde el menú inicio.

2. El programa te pedirá varios datos. Presiona **Enter** en todos para usar los valores por defecto, y cuando pida la contraseña escribe la que definiste al instalar PostgreSQL:

   ```
   Server [localhost]:          ← Enter
   Database [postgres]:         ← Enter
   Port [5432]:                 ← Enter
   Username [postgres]:         ← Enter
   Password for user postgres:  ← escribe tu contraseña
   ```

3. Una vez dentro, verás el símbolo `postgres=#`. Escribe el siguiente comando y presiona Enter:

   ```sql
   CREATE DATABASE terminal_terrestre;
   ```

4. Verifica que se creó:

   ```sql
   \l
   ```

   Debes ver `terminal_terrestre` en la lista.

5. Sal del programa:

   ```sql
   \q
   ```

---

## 5. Descargar y preparar el proyecto

1. Descarga el archivo ZIP del proyecto y descomprímelo. Elige una ubicación sencilla, por ejemplo:

   ```
   C:\terminal_terrestre\
   ```

2. Abre **PowerShell** y navega hasta esa carpeta:

   ```powershell
   cd C:\terminal_terrestre
   ```

   > **Consejo:** también puedes abrir la carpeta en el Explorador de Windows, hacer clic en la barra de direcciones, escribir `powershell` y presionar Enter. Esto abre PowerShell directamente en esa carpeta.

3. Crea el entorno virtual de Python:

   ```powershell
   python -m venv venv
   ```

4. Activa el entorno virtual:

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

   Si PowerShell muestra un error sobre la ejecución de scripts, ejecuta primero este comando y luego vuelve a intentarlo:

   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

5. Cuando el entorno virtual está activo, verás `(venv)` al inicio de la línea en PowerShell:

   ```
   (venv) PS C:\terminal_terrestre>
   ```

---

## 6. Configurar el archivo .env

El archivo `.env` contiene la configuración del sistema (base de datos, clave secreta, etc.).

1. En la carpeta del proyecto hay un archivo llamado `.env.example`. Cópialo y renómbralo a `.env`:

   ```powershell
   copy .env.example .env
   ```

2. Abre el archivo `.env` con el Bloc de notas u otro editor de texto:

   ```powershell
   notepad .env
   ```

3. Edita los valores según tu configuración. Los más importantes son:

   ```env
   # Clave secreta de Django (cámbiala por cualquier texto largo y aleatorio)
   SECRET_KEY=cambia-esto-por-una-clave-larga-y-aleatoria-minimo-50-caracteres

   # Datos de tu base de datos PostgreSQL
   DB_NAME=terminal_terrestre
   DB_USER=postgres
   DB_PASSWORD=postgres123       ← la contraseña que pusiste al instalar PostgreSQL
   DB_HOST=localhost
   DB_PORT=5432
   ```

4. Guarda el archivo.

---

## 7. Instalar dependencias Python

Con el entorno virtual activo (debe verse `(venv)` al inicio), ejecuta:

```powershell
pip install -r requirements.txt
```

Este proceso descarga e instala todos los paquetes necesarios (Django, librerías QR, conexión a PostgreSQL, etc.). Puede tardar unos minutos dependiendo de tu conexión a internet.

Cuando termine, debes ver un mensaje como:
```
Successfully installed Django-5.0.6 ...
```

> **Si aparece un error con psycopg2**, ejecuta:
> ```powershell
> pip install psycopg2-binary
> ```

---

## 8. Crear las tablas y cargar datos iniciales

Estos comandos solo se ejecutan **una vez** cuando instalas el sistema por primera vez.

**Paso 1 — Crear las tablas en la base de datos:**

```powershell
python manage.py migrate
```

Verás una lista de migraciones aplicadas. Al final debe decir `OK` en todas.

**Paso 2 — Cargar los datos iniciales del terminal:**

```powershell
python manage.py seed_data
```

Este comando crea automáticamente:

| Qué crea | Detalle |
|----------|---------|
| Usuarios | admin, maria, juan, pedro, ana |
| Tipos de ticket | Los 7 tipos reales del terminal con sus precios |
| Cooperativas | Flota Imbabura, Trans Esmeraldas, Reina del Camino, Pullman Carchi |
| Config Hikvision | IP 172.168.109.5, puerto 80, puerta 1 |

---

## 9. Iniciar el sistema

Con el entorno virtual activo, ejecuta:

```powershell
python manage.py runserver
```

Verás algo como:

```
Django version 5.0.6, using settings 'config.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

Abre tu navegador y ve a:

```
http://localhost:8000
```

El sistema te redirigirá automáticamente al formulario de inicio de sesión.

> Para detener el servidor en cualquier momento presiona `Ctrl + C` en la ventana de PowerShell.

---

## 10. Credenciales de acceso

Estas son las cuentas creadas por el comando `seed_data`:

| Usuario    | Contraseña     | Rol          | Horario sugerido |
|------------|---------------|--------------|-----------------|
| `admin`    | `admin123`     | Administrador | — |
| `maria`    | `operador123`  | Operador     | 06:00 – 14:00 |
| `juan`     | `operador123`  | Operador     | 14:00 – 22:00 |
| `pedro`    | `operador123`  | Operador     | 22:00 – 06:00 |
| `ana`      | `supervisor123`| Supervisora  | — |

> ⚠️ Cambia todas las contraseñas antes de poner el sistema en producción. Puedes hacerlo desde el menú **Usuarios** dentro del sistema.

---

## 11. Uso del sistema

### Generar un ticket QR

1. Inicia sesión con un usuario operador (por ejemplo `maria`).
2. En la página principal **Generar QR**:
   - Selecciona el **tipo de ticket** del menú desplegable.
   - Si aplica, selecciona la **cooperativa**.
   - Elige el **tiempo de expiración** en minutos (botones rápidos o escribe el valor).
3. Haz clic en **⚡ Generar Ticket QR**.
4. El sistema se conecta automáticamente al torniquete Hikvision, crea el usuario y asigna la tarjeta QR.
5. Aparece la imagen QR junto con el número de ticket (TK-000001, TK-000002, etc.).
6. Haz clic en **🖨️ Imprimir Ticket** para imprimir dos copias: una para el pasajero y otra para el archivo del operador.

### Ver el Dashboard

Muestra en tiempo real:
- Ingresos del día
- Total de tickets generados, activos, usados y expirados
- Gráfica de ventas por tipo de ticket
- Gráfica de ventas por hora
- Ingresos de los últimos 30 días

### Generar el Reporte de Recaudaciones

1. Ve al menú **Recaudaciones**.
2. Selecciona el tipo de reporte: **Diario**, **Mensual** o **Anual**.
3. Ingresa la fecha, mes o año según corresponda.
4. Haz clic en **📊 Generar Reporte**.
5. El reporte muestra el formato oficial del terminal:
   - Encabezado institucional
   - Tabla con ticket inicial, ticket final, cantidad y valores
   - Total en letras (SON: VEINTICINCO DÓLARES CON 50/100 CENTAVOS)
   - Área de firma de la administradora
6. Haz clic en **🖨️ Imprimir** para imprimir el documento. El sidebar y los controles se ocultan automáticamente al imprimir.

### Numeración de tickets entre turnos

Los tickets se numeran de forma **continua y global** (TK-000001, TK-000002, ...). Cuando un operador termina su turno, el siguiente operador continúa desde el último número registrado. El reporte de recaudaciones muestra el número inicial y final del período seleccionado.

---

## 12. Configurar la conexión Hikvision

Si necesitas cambiar los datos de conexión al torniquete:

1. Inicia sesión con el usuario `admin`.
2. Ve al menú **Config Hikvision** (aparece solo para administradores).
3. Completa los datos:
   - **IP:** dirección IP del torniquete en tu red local (por defecto `172.168.109.5`)
   - **Puerto:** normalmente `80`
   - **Usuario y contraseña:** los del dispositivo Hikvision
   - **Número de puerta:** normalmente `1`
   - **Minutos por defecto:** tiempo de expiración cuando el operador no especifica uno
4. Haz clic en **💾 Guardar configuración**.
5. Luego haz clic en **🔗 Probar conexión** para verificar que el sistema puede comunicarse con el torniquete.

> **Si el torniquete no está disponible** (equipo apagado o red desconectada), los tickets se generan igualmente pero con estado `error`. El QR no funcionará en el torniquete hasta que se registre manualmente o se vuelva a generar.

---

## 13. Producción con Waitress

Para uso en producción en Windows se recomienda Waitress (ya incluido en requirements.txt) en lugar del servidor de desarrollo de Django.

**Paso 1 — Ajusta el archivo .env:**

```env
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,IP-DE-TU-SERVIDOR
SECRET_KEY=clave-muy-larga-y-aleatoria-para-produccion
```

**Paso 2 — Recolecta los archivos estáticos:**

```powershell
python manage.py collectstatic --noinput
```

**Paso 3 — Inicia el servidor con Waitress:**

```powershell
python -m waitress --host=0.0.0.0 --port=8000 config.wsgi:application
```

El sistema estará disponible en la red local en `http://IP-DEL-EQUIPO:8000`.

**Para que inicie automáticamente con Windows**, puedes crear una tarea en el Programador de tareas de Windows que ejecute el comando anterior al iniciar el sistema.

---

## 14. Solución de problemas

### Python no se reconoce como comando

**Síntoma:**
```
python : El término 'python' no se reconoce...
```

**Solución:**
- Desinstala Python y vuelve a instalarlo **marcando la casilla "Add Python to PATH"**.
- O agrega Python manualmente al PATH: busca "Variables de entorno" en el menú inicio, edita la variable `Path` del sistema y agrega la ruta donde se instaló Python (normalmente `C:\Users\TuUsuario\AppData\Local\Programs\Python\Python311\`).

---

### Error al activar el entorno virtual

**Síntoma:**
```
.\venv\Scripts\Activate.ps1 : ... no está firmado digitalmente...
```

**Solución:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Luego vuelve a ejecutar `.\venv\Scripts\Activate.ps1`.

---

### Error de conexión a PostgreSQL

**Síntoma:**
```
django.db.OperationalError: could not connect to server
```

**Causas y soluciones:**

1. **PostgreSQL no está corriendo.** Abre el menú inicio, busca "Servicios", busca el servicio `postgresql-x64-16` y verifica que esté **En ejecución**. Si no, haz clic derecho → Iniciar.

2. **Contraseña incorrecta.** Abre `.env` y verifica que `DB_PASSWORD` coincide con la contraseña que pusiste al instalar PostgreSQL.

3. **Base de datos no existe.** Abre SQL Shell (psql) y ejecuta `CREATE DATABASE terminal_terrestre;`.

---

### Error con psycopg2

**Síntoma:**
```
ImportError: DLL load failed while importing _psycopg
```

**Solución:**
```powershell
pip uninstall psycopg2
pip install psycopg2-binary
```

---

### La página muestra error 500 o página en blanco

**Solución:**
1. Verifica que en `.env` tienes `DEBUG=True` (solo durante desarrollo).
2. Mira la consola de PowerShell donde corre el servidor — muestra el error completo.
3. Verifica que ejecutaste `python manage.py migrate` correctamente.

---

### El torniquete no acepta el QR

**Posibles causas:**

1. **Error de integración:** en la página de Generar QR aparece el ícono ❌ junto al ticket. Significa que el sistema no pudo comunicarse con el torniquete al momento de generar el ticket.

2. **El ticket ya fue usado o expiró:** cada QR solo funciona una vez y por el tiempo configurado.

3. **Hora desincronizada:** el torniquete Hikvision verifica las fechas de validez del ticket. Si la hora del servidor Windows y la del torniquete no coinciden, puede rechazar tickets válidos. Sincroniza ambos relojes con internet (NTP).

4. **Para diagnosticar:** ve a **Config Hikvision** y usa el botón **🔗 Probar conexión**. Si falla, hay un problema de red entre el servidor y el torniquete.

---

### Cómo reiniciar el sistema si algo falla

Cierra la ventana de PowerShell y abre una nueva. Luego:

```powershell
cd C:\terminal_terrestre
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

---

## 📁 Estructura del proyecto

```
terminal_terrestre/
│
├── config/                  Configuración Django (settings, urls, wsgi)
│
├── apps/
│   ├── usuarios/            Usuarios del sistema con roles
│   ├── tickets/             Tipos de ticket con precios
│   ├── qr_codes/            ★ Módulo principal: generación QR + Hikvision
│   ├── ventas/              Registro de ventas con numeración TK-000001
│   ├── cooperativas/        Cooperativas de transporte
│   ├── accesos/             Endpoint API para validación desde torniquetes
│   └── dashboard/           Estadísticas y reporte de recaudaciones
│
├── templates/               Plantillas HTML (lo que ve el usuario)
│   ├── base.html            Layout general con sidebar y topbar
│   ├── login.html           Pantalla de inicio de sesión
│   ├── qr_codes/            Generar QR, Config Hikvision
│   ├── dashboard/           Dashboard con gráficas
│   ├── recaudaciones/       Reporte oficial imprimible
│   ├── tickets/             CRUD tipos de ticket
│   ├── cooperativas/        CRUD cooperativas
│   └── usuarios/            Gestión de usuarios
│
├── static/                  Archivos estáticos (CSS, JS, imágenes)
├── manage.py                Comandos de Django
├── requirements.txt         Dependencias Python
├── .env.example             Plantilla de configuración
└── README.md                Este archivo
```

---

## 🔑 Resumen de comandos útiles

Todos los comandos se ejecutan en PowerShell con el entorno virtual activo:

```powershell
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Iniciar el servidor (desarrollo)
python manage.py runserver

# Iniciar en una IP y puerto específico
python manage.py runserver 0.0.0.0:8000

# Aplicar migraciones (cuando hay cambios en la BD)
python manage.py migrate

# Cargar datos iniciales (solo la primera vez)
python manage.py seed_data

# Crear un superusuario manualmente
python manage.py createsuperuser

# Recolectar archivos estáticos (para producción)
python manage.py collectstatic --noinput

# Iniciar con Waitress (producción)
python -m waitress --host=0.0.0.0 --port=8000 config.wsgi:application
```

---

*Sistema desarrollado para la Alcaldía de Calvas — Cariamanga, Ecuador.*
