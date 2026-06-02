# Kanban Board - Tareas del Proyecto (Sistema de Monitoreo DMS Móvil)

Este documento desglosa el trabajo en Epics, User Stories y Tareas (Tickets) listos para ser importados a Jira, Trello o Asana.

## EPIC 1: Infraestructura Base y Captura de Video Nativa

### Story 1.1: [Android] Configurar CameraX para captura frontal eficiente
**Como** desarrollador Android, **quiero** usar CameraX para obtener un flujo de video (YUV) de la cámara frontal **para** pasarlo al motor de IA sin bloquear la interfaz.
* **Task 1.1.1:** Integrar dependencias CameraX (`core`, `camera2`, `lifecycle`, `view`).
* **Task 1.1.2:** Crear un analizador de imágenes (`ImageAnalysis.Analyzer`) que convierta fotogramas a Bitmap o ByteBuffer a un máximo de 640x480.
* **Task 1.1.3:** Manejar la rotación de pantalla nativa (Landscape/Portrait) en el vehículo.

### Story 1.2: [iOS] Configurar AVFoundation para captura de video
**Como** desarrollador iOS, **quiero** usar `AVCaptureSession` **para** obtener `CVPixelBuffer` optimizados desde la cámara frontal.
* **Task 1.2.1:** Configurar permisos `NSCameraUsageDescription` en Info.plist.
* **Task 1.2.2:** Inicializar sesión de captura con preset de baja resolución (`AVCaptureSession.Preset.vga640x480`).
* **Task 1.2.3:** Implementar el delegado `AVCaptureVideoDataOutputSampleBufferDelegate` para recibir frames de forma asíncrona.

---

## EPIC 2: Motor de Visión Artificial Móvil (Edge AI)

### Story 2.1: Integrar Google MediaPipe Face Mesh
**Como** ingeniero de IA, **quiero** ejecutar el modelo TFLite de Face Mesh en el móvil **para** obtener los 468 landmarks 3D en tiempo real.
* **Task 2.1.1:** Añadir librería MediaPipe Tasks Vision (Maven/CocoaPods) al proyecto nativo.
* **Task 2.1.2:** Descargar e incluir el modelo `.task` de Face Mesh en los assets de la app.
* **Task 2.1.3:** Inicializar `FaceLandmarker` con opciones de `RUNNING_MODE_LIVE_STREAM` y delegación por CPU o NPU (si está disponible).
* **Task 2.1.4:** Extraer exclusivamente los índices críticos: `[33, 160, 158, 133, 153, 144]` (Ojo Izq), `[362, 385, 387, 263, 373, 380]` (Ojo Der), `[78, 191... 80]` (Boca), `[1, 152]` (Cabeza).

### Story 2.2: Algoritmos de Fatiga y Distracción
**Como** ingeniero de IA, **quiero** calcular EAR, MAR y Head Pose **para** determinar si el conductor está durmiendo o distraído.
* **Task 2.2.1:** Escribir la función matemática `calculate_ear(landmarks)` usando distancia euclidiana entre párpados superiores e inferiores sobre anchura total.
* **Task 2.2.2:** Escribir la función `calculate_mar(landmarks)` para la boca (bostezos).
* **Task 2.2.3:** Implementar solver PnP simple nativo o aproximación matemática para `Yaw` (Giro) y `Pitch` (Inclinación).

---

## EPIC 3: Máquina de Estados Finita (Lógica de Decisión)

### Story 3.1: Determinar el Estado Crítico
**Como** sistema FSM, **quiero** evaluar los valores de EAR/MAR en el tiempo **para** disparar eventos solo si el cierre ocular es constante y no un parpadeo normal.
* **Task 3.1.1:** Crear la clase `DrowsinessDetector` que almacene un buffer circular (ventana de tiempo) de los últimos 45 valores EAR (1.5s a 30 FPS).
* **Task 3.1.2:** Lógica: Si el EAR promedio de los últimos 45 frames baja de `0.22`, emitir señal `EMERGENCY_SLEEP_DETECTED`.
* **Task 3.1.3:** Lógica de recuperación: Si el EAR sube a > `0.28` por 15 frames, emitir `DRIVER_AWAKE` para cancelar alarmas.
* **Task 3.1.4:** Implementar calibración dinámica: durante los primeros 10 segundos del viaje, registrar el EAR natural del usuario para fijar su "baseline".

---

## EPIC 4: Alertas de Despertar de Latencia Cero

### Story 4.1: Interfaz y Alertas Físicas (Despertar Forzoso)
**Como** chofer, **quiero** recibir un impacto sonoro/visual brutal si me quedo dormido **para** evitar estrellarme.
* **Task 4.1.1:** [UI] Crear un flash rojo estroboscópico a pantalla completa que anule la atenuación del sistema. Subir brillo al 100% mediante las APIs de ventana (`WindowManager.LayoutParams.BRIGHTNESS_OVERRIDE_FULL`).
* **Task 4.1.2:** [Audio Android] Usar `AudioManager` para solicitar foco, configurar `STREAM_ALARM` al volumen máximo, sobrepasando el modo no molestar y reproducir sirena (`MediaPlayer`).
* **Task 4.1.3:** [Audio iOS] Configurar `AVAudioSession` con categoría `playback` y opciones `duckOthers`.
* **Task 4.1.4:** [Háptica] Disparar vibrador del dispositivo continuamente (`VibrationEffect.createWaveform`).

---

## EPIC 5: Optimización Térmica y Batería

### Story 5.1: Prevención de Thermal Throttling
**Como** desarrollador móvil, **quiero** regular dinámicamente el rendimiento **para** que el teléfono soporte estar al sol en el tablero sin apagarse por calor.
* **Task 5.1.1:** Monitorear el Intent `ACTION_BATTERY_CHANGED` (Temperatura > 40°C).
* **Task 5.1.2:** Si hay calor extremo, bajar el procesamiento de la cámara a 10 FPS de forma dinámica. Ajustar la ventana de tiempo del `DrowsinessDetector` (15 frames = 1.5s).
* **Task 5.1.3:** Implementar "Dimming mode": Poner la pantalla completamente negra (ahorro OLED) a menos que haya una alarma roja o el usuario toque la pantalla.

---

## EPIC 6: Persistencia y Sincronización Backend

### Story 6.1: Almacenamiento Local (Store and Forward)
**Como** sistema offline, **quiero** guardar métricas temporalmente **para** no perder eventos de sueño si el vehículo transita por carretera sin señal celular.
* **Task 6.1.1:** Crear base de datos local (Room/SQLite) tabla `MicroSleepEvents` (Id, Timestamp, EAR_Value, Duration_Seconds, GPS_Lat, GPS_Lng).
* **Task 6.1.2:** Grabar en DB local cada vez que se dispare una alerta de `EMERGENCY_SLEEP_DETECTED`.

### Story 6.2: API de Sincronización Python
**Como** servidor backend, **quiero** recibir el JSON de los móviles de los conductores **para** actualizar el panel web del gerente de flota.
* **Task 6.2.1:** (Backend Python) Crear endpoint POST `/api/v1/telemetry/events` (FastAPI).
* **Task 6.2.2:** (Móvil) Crear un servicio de WorkManager / BackgroundTasks que corra cada 15 min, lea datos no sincronizados de Room, intente PUSH vía Retrofit/URLSession. Si responde 200 OK, marcar como "Sync" y purgar métricas antiguas de SQLite.

---

## EPIC 7: Certificación y Store Publishing

### Story 7.1: Privacidad y Políticas de Tienda
**Como** Product Owner, **quiero** garantizar la privacidad del chofer **para** cumplir con GDPR/CCPA y que Apple/Google acepten la app.
* **Task 7.1.1:** Redactar "Privacy Policy" aclarando que ningún video/imagen sale del celular del conductor; solo se envía "telemetría numérica de riesgo".
* **Task 7.1.2:** Enviar a revisión en App Store (Citar uso del micrófono/cámara solo "in-app" y proveer video de demostración a los revisores).
## EPIC 8: Motor de Reportes Predictivos y Bloqueo de Rutas
Este Epic se enfoca en el valor preventivo del DMS para Uber/Logística: Prevenir que choferes cansados tomen nuevos pasajeros.

### Story 8.1: Cálculo del Fatigue Risk Score (FRS)
**Como** Analista de Datos, **quiero** calcular el riesgo de choque de un chofer (0 a 100) en base a su historial biométrico de las últimas 4 horas **para** bloquear su inicio de viaje.
* **Task 8.1.1:** Escribir servicio Python que asigne 35pts por microsueño, 5pts por bostezo, 8pts por distracción.
* **Task 8.1.2:** Escribir el decay job (Cron) que reste 20pts por cada hora real de descanso del vehículo.

### Story 8.2: Integración de Bloqueo al API de Despacho (Didi/Logística)
**Como** Sistema de Asignación, **quiero** preguntar si el chofer está fresco o agotado **para** autorizar el viaje.
* **Task 8.2.1:** (Backend Python) Crear endpoint `/api/v1/mobile_dms/clearance/{driver_id}` que devuelva `ALLOWED` (0-49pts), `WARNING` (50-74pts), `BLOCKED_FATIGUE` (75-100pts) con sus tiempos obligatorios de descanso en minutos.
* **Task 8.2.2:** (Móvil UI) Crear la pantalla "Fatiga Acumulada - Viaje Pausado. Podrá conducir de nuevo en 45:00 min".

### Story 8.3: Generación de Reportes Automatizados PDF (Shift Summary)
**Como** Gerente de Flota/Sindicato, **quiero** un PDF diario de cada chofer **para** auditar el cumplimiento normativo de "Horas de Servicio y Descanso Fisiológico".
* **Task 8.3.1:** Instalar `ReportLab` o librerías PDF en el entorno Python.
* **Task 8.3.2:** Generar gráficos de barras agrupando incidentes por hora (Ej: Pico a las 03:00 AM).
* **Task 8.3.3:** Enviar un reporte por correo o colocarlo en S3/MinIO al finalizar el turno del chofer si el FRS alguna vez alcanzó nivel ROJO en la jornada, catalogándolo como un reporte "PRIORITY REVIEW".
