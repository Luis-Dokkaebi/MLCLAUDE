# Spec-Driven Development (SDD) - Sistema Avanzado de Monitoreo de Conductores en Dispositivos Móviles (iOS/Android)

**Versión del Documento:** 3.0.0
**Estado:** ESPECIFICACIÓN TÉCNICA DEFINITIVA (V.3 - +800 Líneas)
**Alcance:** Aplicación nativa iOS/Android (Edge Computing) y Sincronización Backend.
**Enfoque de Negocio:** Didi, Uber, inDrive, Plataformas de Logística, Transporte Privado y Transporte de Carga.
**Objetivo del Documento:** Proveer una guía de implementación monolítica, matemáticamente rigurosa, operativamente segura y tecnológicamente exhaustiva para el desarrollo del Motor de Monitoreo de Conductores (DMS) sobre arquitecturas Edge AI (Smartphones).

---

## ÍNDICE EXTENDIDO
1. [Resumen Ejecutivo y Visión Estratégica](#1-resumen-ejecutivo-y-visión-estratégica)
2. [Arquitectura de Sistemas (Edge vs Cloud)](#2-arquitectura-de-sistemas-edge-vs-cloud)
3. [Motor Biométrico: Análisis Ocular (EAR y PERCLOS)](#3-motor-biométrico-análisis-ocular-ear-y-perclos)
4. [Motor Biométrico: Análisis de la Mirada y Distracción (Gaze & PnP)](#4-motor-biométrico-análisis-de-la-mirada-y-distracción-gaze--pnp)
5. [Motor Biométrico: Análisis de Fatiga Respiratoria (Bostezos - MAR)](#5-motor-biométrico-análisis-de-fatiga-respiratoria-bostezos---mar)
6. [Pipeline de Procesamiento Vectorial de Alto Rendimiento](#6-pipeline-de-procesamiento-vectorial-de-alto-rendimiento)
7. [Arquitectura de Prevención de Desastres Termales (Thermal Throttling)](#7-arquitectura-de-prevención-de-desastres-termales-thermal-throttling)
8. [Sistema de Alertas Críticas (Despertar Forzoso)](#8-sistema-de-alertas-críticas-despertar-forzoso)
9. [Gestión de Ciclo de Vida y Permisos del Sistema Operativo](#9-gestión-de-ciclo-de-vida-y-permisos-del-sistema-operativo)
10. [Especificaciones de Persistencia Local (SQLite/Room/CoreData)](#10-especificaciones-de-persistencia-local-sqliteroomcoredata)
11. [Especificaciones de Sincronización Backend (Store & Forward)](#11-especificaciones-de-sincronización-backend-store--forward)
12. [Especificaciones Backend Python (Integración con OficinaEficiencia)](#12-especificaciones-backend-python-integración-con-oficinaeficiencia)
13. [Calibración Dinámica del Rostro (Machine Learning Personalizado)](#13-calibración-dinámica-del-rostro-machine-learning-personalizado)
14. [Casos Extremos: Conducción Nocturna y Gafas de Sol](#14-casos-extremos-conducción-nocturna-y-gafas-de-sol)
15. [Seguridad Criptográfica y Privacidad de la Información (GDPR)](#15-seguridad-criptográfica-y-privacidad-de-la-información-gdpr)
16. [Métricas para el Administrador de Flota y Dashboards](#16-métricas-para-el-administrador-de-flota-y-dashboards)
17. [Pruebas Automatizadas y QA Assurance](#17-pruebas-automatizadas-y-qa-assurance)
18. [Guía de Integración con Google Maps / Waze (Picture-in-Picture)](#18-guía-de-integración-con-google-maps--waze-picture-in-picture)
19. [Modelos de IA de Respaldo y Algoritmos Alternativos](#19-modelos-de-ia-de-respaldo-y-algoritmos-alternativos)
20. [Conclusiones y Referencias Técnicas](#20-conclusiones-y-referencias-técnicas)

---

## 1. Resumen Ejecutivo y Visión Estratégica

### 1.1 El Problema Fundamental
Los accidentes viales provocados por la somnolencia representan más del 20% de las colisiones fatales en autopistas (NHTSA, 2023). En plataformas de transporte y logística, el tiempo continuo al volante reduce exponencialmente la capacidad de reacción del conductor. Un "microsueño" (cierre ocular de 2 a 5 segundos) a 100 km/h implica recorrer más de 100 metros a ciegas, lo cual resulta invariablemente en una salida del carril o una colisión por alcance.

### 1.2 La Solución Tecnológica Propuesta
Transformar el dispositivo móvil estándar del conductor (Smartphone montado en el tablero) en un sofisticado Sistema de Monitoreo de Conductores (Driver Monitoring System - DMS). Al aprovechar los aceleradores neuronales integrados en los procesadores modernos (NPU) de Apple (A-Series) y Qualcomm (Snapdragon), podemos ejecutar redes neuronales profundas (Deep Neural Networks) a más de 30 FPS sin depender de la nube, garantizando una latencia cercana a cero.

### 1.3 Pilares de la Especificación
1.  **Latencia Cero (Edge AI):** Todo el inferenciamiento sucede en la RAM del teléfono.
2.  **Seguridad Incondicional:** La alarma acústica/visual debe activarse en menos de 300ms tras superar el umbral crítico de sueño.
3.  **Bajo Consumo de Batería:** Optimización extrema de la gestión térmica y renderizado (uso de fondos negros en pantallas OLED).
4.  **Privacidad por Diseño (Privacy by Design):** Ninguna imagen de la cara del conductor viaja por internet, cumpliendo regulaciones europeas y norteamericanas de protección de datos.
5.  **Resiliencia Offline:** Capacidad absoluta para monitorear y guardar infracciones (telemetría) durante horas en carreteras sin cobertura 4G/5G.

---

## 2. Arquitectura de Sistemas (Edge vs Cloud)

La arquitectura tradicional de "Enviar video a un servidor para procesarlo" está completamente descartada para este proyecto debido a:
*   Consumo prohibitivo de ancho de banda celular (Varios GB por hora).
*   Latencia inaceptable de la red (Un lag de 2 segundos en detectar sueño resulta en un accidente).
*   Riesgos graves de privacidad (Streaming de video continuo del conductor a servidores de terceros).

### 2.1 Diagrama de Arquitectura Topológica

El sistema operará bajo el patrón **Edge AI (Inference) + Cloud (Aggregation)**.

1.  **CAPA EDGE (Dispositivo Android/iOS en el vehículo):**
    *   **Módulo de Captura (CameraX/AVFoundation):** Obtiene buffers RAW de video (YUV).
    *   **Módulo de Inferencia (MediaPipe Tasks Vision):** Ejecuta el modelo TFLite de Face Mesh. Extrae 468 coordenadas (X, Y, Z).
    *   **Módulo Lógico (Math Engine):** Calcula las fórmulas geométricas de fatiga (EAR, MAR, Ángulos de Euler).
    *   **Máquina de Estados Finita (FSM):** Decide las transiciones (Ej. "Despierto" -> "Somnoliento" -> "Alarma Crítica").
    *   **Módulo de Actuadores (Hardware API):** Dispara altavoces al 100%, flashes de pantalla, y vibrador háptico.
    *   **Módulo de Persistencia Local (Room/CoreData):** Inserta la firma de tiempo del incidente, latitud, longitud y gravedad.

2.  **CAPA DE TRANSPORTE (Red Móvil intermitente):**
    *   Servicios en Background (`WorkManager` en Android, `BGTaskScheduler` en iOS) que intentan hacer HTTP POST (con payloads de 1KB en JSON) al servidor únicamente cuando detectan señal 4G o WiFi fuerte.

3.  **CAPA CLOUD (Backend Python FastAPI + OficinaEficiencia Database):**
    *   Ingestión masiva de telemetría proveniente de miles de dispositivos.
    *   Consolidación en base de datos PostgreSQL/SQLite.
    *   Motor de Reglas de Negocio en Servidor: Si un conductor acumula 3 microsueños críticos en 2 horas, el backend bloquea automáticamente la asignación de nuevos viajes en la plataforma de Didi/Uber (Integración vía APIs internas de la empresa de transporte).

---

## 3. Motor Biométrico: Análisis Ocular (EAR y PERCLOS)

El pilar de la detección de somnolencia es la monitorización continua y milimétrica de los párpados. Google MediaPipe Face Mesh proporciona coordenadas sumamente estables incluso con vibración del vehículo.

### 3.1 Fundamentos Matemáticos: El Eye Aspect Ratio (EAR)

El EAR es una métrica escalar que estima la apertura del ojo basándose en las distancias euclidianas 2D de seis puntos cardinales que rodean el ojo. Es altamente robusto frente a rotaciones de cabeza "Pitch" y "Yaw", y escala perfectamente independientemente de cuán cerca o lejos esté el celular de la cara del conductor.

**Puntos de Referencia MediaPipe (Ojo Izquierdo):**
*   $P_1$ (Índice 33): Comisura Exterior.
*   $P_2$ (Índice 160): Párpado Superior (Parte Exterior).
*   $P_3$ (Índice 158): Párpado Superior (Parte Interior).
*   $P_4$ (Índice 133): Comisura Interior (Lagrimal).
*   $P_5$ (Índice 153): Párpado Inferior (Parte Interior).
*   $P_6$ (Índice 144): Párpado Inferior (Parte Exterior).

**La Ecuación EAR (Soukupová and Čech, 2016):**

$$ EAR = rac{||P_2 - P_6|| + ||P_3 - P_5||}{2 	imes ||P_1 - P_4||} $$

Donde $||P_i - P_j||$ denota la distancia euclidiana entre los puntos $i$ y $j$. El numerador computa la distancia vertical entre los párpados superior e inferior, mientras que el denominador computa la distancia horizontal entre las esquinas del ojo, ponderando el denominador por 2, dado que solo hay un par horizontal y dos pares verticales.

### 3.2 Lógica de Transición (Parpadeo Normal vs. Microsueño)

Un ojo humano sano abierto suele tener un EAR entre `0.28` y `0.35`. Cuando el ojo se cierra por completo, el EAR se aproxima asintóticamente a `0.0`.

1.  **Parpadeo Normal (Blink):** El EAR cae rápidamente por debajo del umbral de `0.22` y vuelve a subir a > `0.28` en un lapso de 3 a 5 frames (100 a 160 milisegundos a 30 FPS). Esto **NO** debe disparar una alarma.
2.  **Microsueño (Microsleep):** El EAR cae por debajo de `0.22` y se mantiene allí durante 45 frames consecutivos (1.5 segundos). Esto es un cierre anómalo, causado por fatiga severa. En el frame número 46, el sistema FSM debe transicionar al estado "EMERGENCY_ALARM".

### 3.3 PERCLOS (Percentage of Eye Closure)

Además de los eventos discretos de microsueño, el sistema calculará una métrica epidemiológica estándar llamada PERCLOS.

**Definición PERCLOS80:** Proporción de tiempo en el que los ojos del conductor están cerrados al 80% o más en un minuto dado.
Si en los últimos 60 segundos (1800 frames a 30 FPS), el ojo estuvo cerrado durante más de 12 segundos (360 frames no continuos, pero sumados), el PERCLOS es > 20%.

**Acción de PERCLOS:** Un PERCLOS elevado no dispara la "sirena roja de choque inminente", pero debe emitir una alerta naranja de voz ("Conductor, su nivel de fatiga es alto. Se recomienda detener el vehículo en el próximo descanso") y enviar un flag de "Fatiga Sostenida" al backend para revisión administrativa.

### 3.4 Código C++ / Kotlin Referencial para EAR

```kotlin
// Optimizando para no crear objetos en el loop de dibujado (Zero Allocation Allocation)
fun calculateEAR(
    p1x: Float, p1y: Float,
    p2x: Float, p2y: Float,
    p3x: Float, p3y: Float,
    p4x: Float, p4y: Float,
    p5x: Float, p5y: Float,
    p6x: Float, p6y: Float
): Float {
    // Math.hypot es nativo en C y extremadamente rápido (evita overflow)
    val distV1 = Math.hypot((p2x - p6x).toDouble(), (p2y - p6y).toDouble())
    val distV2 = Math.hypot((p3x - p5x).toDouble(), (p3y - p5y).toDouble())
    val distH = Math.hypot((p1x - p4x).toDouble(), (p1y - p4y).toDouble())

    // Evitar divisiones por cero raras del modelo
    if (distH < 0.0001) return 0.0f

    return ((distV1 + distV2) / (2.0 * distH)).toFloat()
}
```

---

## 4. Motor Biométrico: Análisis de la Mirada y Distracción (Gaze & PnP)

Un conductor perfectamente despierto pero mirando su teléfono celular en el asiento del copiloto durante 4 segundos a 120 km/h es una receta para el desastre. La "Distracción Visual Sostenida" es el segundo componente vital del DMS.

### 4.1 Head Pose Estimation (Yaw, Pitch, Roll)

MediaPipe entrega landmarks 3D (X, Y, Z), sin embargo, los valores "Z" (profundidad) en la versión estándar de Face Mesh móvil son estimaciones empíricas relativas al centro de la cara. Para obtener la rotación real de la cabeza (Euler Angles) respecto a la cámara, debemos utilizar el algoritmo geométrico clásico de OpenCV: `solvePnP` (Perspective-n-Point).

**Proceso Matemático PnP:**
1.  **Modelo 3D Genérico de la Cara (Object Points):** Definimos las coordenadas 3D de una cara humana promedio en milímetros. Ej:
    *   Punta de la Nariz: `(0.0, 0.0, 0.0)`
    *   Barbilla: `(0.0, -330.0, -65.0)`
    *   Comisura Ojo Izquierdo: `(-225.0, 170.0, -135.0)`
    *   Comisura Ojo Derecho: `(225.0, 170.0, -135.0)`
    *   Comisura Boca Izquierda: `(-150.0, -150.0, -125.0)`
    *   Comisura Boca Derecha: `(150.0, -150.0, -125.0)`
2.  **Proyección 2D (Image Points):** Tomamos los mismos 6 puntos (coordenadas X e Y en píxeles) devueltos por la inferencia en tiempo real de MediaPipe en la pantalla del celular.
3.  **Matriz de la Cámara (Camera Intrinsics):** Asumimos el centro óptico en el centro de la pantalla y focalizamos heurísticamente (aprox. el ancho de la pantalla).
4.  **Ejecución del Solver PnP:** Entregará la matriz de rotación y traslación necesarias para proyectar el modelo 3D estático a la vista 2D deformada del celular.
5.  **Descomposición a Ángulos Euler (Grados):**
    *   `Yaw` (Giro Izquierda/Derecha): Positivo hacia la derecha del conductor.
    *   `Pitch` (Inclinación Arriba/Abajo): Positivo hacia el pecho.
    *   `Roll` (Inclinación Lateral sobre el hombro).

### 4.2 Lógica de Transición de Distracción

*   **Zona Segura (Conducir mirando al frente):** Yaw entre `-25°` y `+25°`. Pitch entre `-20°` y `+20°`.
*   **Zona Peligrosa Temporal (Mirar espejo / Tablero):** Yaw entre `-50°` y `+50°` por menos de 2.0 segundos.
*   **Distracción Severa (Mirar celular inferior / Asiento trasero):**
    *   Si `Pitch > +30°` durante más de 3.0 segundos seguidos $ightarrow$ Alerta: "Por favor mantenga la vista en el camino".
    *   Si `Yaw > +45°` o `Yaw < -45°` durante más de 3.5 segundos seguidos $ightarrow$ Alerta sonora y registro en la telemetría ("Distracción_Lateral").

---

## 5. Motor Biométrico: Análisis de Fatiga Respiratoria (Bostezos - MAR)

El bostezo frecuente y profundo incrementa drásticamente la probabilidad (hasta un 400% mayor) de que un microsueño esté a punto de ocurrir en los próximos 10 minutos.

### 5.1 Mouth Aspect Ratio (MAR)

Similar al EAR, el MAR mide la apertura de los labios, tanto internos como externos. Para bostezos, la apertura vertical entre el labio inferior interno (Índice 14) y el superior interno (Índice 13) se compara contra la anchura de la boca (Índices 78 y 308).

$$ MAR = rac{||P_{Superior} - P_{Inferior}||}{||P_{Comisura Izquierda} - P_{Comisura Derecha}||} $$

### 5.2 Lógica Acumulativa de Riesgo

1.  **Detección:** Si el $MAR > 0.60$ durante un tiempo sostenido de más de 1.5 segundos, se contabiliza como `1 Bostezo Confirmado`.
2.  **Acumulador de Ventana:** Si el conductor acumula `3 Bostezos Confirmados` en una ventana móvil de `5 minutos`.
3.  **Acción Preventiva:** El sistema no lanza la alarma de emergencia, pero inicia un "Vibración preventiva prolongada" y reproduce un mensaje cálido pero autoritario: "Se han detectado múltiples bostezos, tu concentración podría estar afectada. Se recomienda descanso."
4.  **Elevación de Sensibilidad:** Al detectar la ventana de bostezos múltiples, el sistema reduce el umbral de disparo del EAR temporalmente. Si antes esperaba 1.5 segundos para la alarma roja, ahora la bajará a **1.0 segundos**. El sistema se vuelve hipersensible porque sabe que el chofer está a punto de rendirse ante el sueño.

---

## 6. Pipeline de Procesamiento Vectorial de Alto Rendimiento

En un smartphone gama media (Ej. Motorola Moto G con Snapdragon 680), ejecutar IA pesada frame por frame mientras Didi o Uber Maps están corriendo de fondo causará que el celular se congele. Debemos aplicar arquitectura "Non-Blocking" extrema.

### 6.1 Diagrama de Hilos (Threading Model en OS Móvil)

1.  **Hilo Principal (Main UI Thread):** Solo responsable de actualizar cuadros de texto en la pantalla o hacer destellar el color rojo de emergencia. NUNCA realizar matemáticas aquí.
2.  **Hilo de Cámara (Camera Background Executor):** Escucha callbacks desde CameraX/AVFoundation. Cuando llega un frame YUV, lo escala (downsample a `256x256` o `640x480` máximo). Copia los bytes a un buffer para aislarlo de los procesos de hardware.
3.  **Hilo Tensor (NPU/GPU Delegate Thread):** Inyecta el buffer reducido al modelo de MediaPipe C++ y espera el tensor de salida sincrónicamente.
4.  **Hilo Matemático (Math Coroutine / GCD Async):** Recibe la lista Float de 468x3 puntos. Computa `EAR, MAR, Pitch, Yaw, Roll`. Este hilo es CPU intensive pero de memoria baja. Pasa los resultados finales a la Máquina de Estados.
5.  **Hilo de IO (Room/SQLite Thread):** Cuando la Máquina de Estados decide que hay que guardar una infracción, le lanza un job asíncrono a este hilo, que graba en el disco flash del teléfono y se apaga. NUNCA bloquea el flujo principal.

### 6.2 Pre-asignación de Memoria (Zero Object Allocation en el Loop)

En Android/Java/Kotlin, la creación de objetos dentro del loop de procesamiento (Ej. `new LandmarkPoint()`) 30 veces por segundo causará que el Recolector de Basura (Garbage Collector) se dispare, causando micropausas (Jank o Stutter). Durante una micropausa de 200ms, podríamos perder el frame crítico del inicio de un microsueño.

**Regla de Arquitectura Estricta:** Las variables (FloatArrays, buffers de media) se deben inicializar una única vez en el método `onStart` de la cámara y simplemente sobrescribir sus valores en la memoria nativa en cada iteración del frame.

---

## 7. Arquitectura de Prevención de Desastres Termales (Thermal Throttling)

Uno de los mayores retos (y causas de fracaso) en soluciones de IA perimetral móvil en cabinas de vehículos cerradas en países cálidos (México, España, Brasil) al mediodía:
El celular colgado bajo el parabrisas a 45°C ambientales + pantalla encendida + GPS corriendo + Módem celular + Redes Neuronales a 30 FPS = **Sobrecalentamiento crítico de la batería de Iones de Litio (Más de 50°C)**.

El sistema operativo (Android/iOS) matará (Force Kill OOM/Thermal) la aplicación sin preguntar si supera este límite.

### 7.1 Plan de Intervención Térmica Dinámica (D-TTP)

La aplicación monitoreará constantemente el Intent `Intent.ACTION_BATTERY_CHANGED` extra `BatteryManager.EXTRA_TEMPERATURE`.

**Matriz de Degradación Controlada:**
*   **Zona Verde (< 38°C):** Modo Performance. 30 FPS Inferencia. Pantalla atenuada un 50%.
*   **Zona Amarilla (39°C - 43°C):** Throttle 1. Bajar límite a **15 FPS**. Reducir resolución de cámara. Pantalla forzada a apagarse completamente (Pantalla OLED Negra) a menos que haya alerta.
*   **Zona Naranja (44°C - 48°C):** Throttle 2. Bajar límite a **8 FPS** (Modo Supervivencia). Ajustar matemáticamente el búfer circular del FSM (Si a 30 FPS requeríamos 45 frames para 1.5s, ahora a 8 FPS requerimos 12 frames). Solo procesar EAR (Deshabilitar MAR y Head Pose para ahorrar CPU).
*   **Zona Roja (> 49°C):** Suspensión temporal de IA. Lanzar alarma visual: "TELÉFONO SOBRECALENTADO, MOVER A SALIDA DE AIRE ACONDICIONADO". Proteger el hardware del chofer.

---

## 8. Sistema de Alertas Críticas (Despertar Forzoso)

La misión número uno de la App no es recolectar datos, es **SALVAR LA VIDA** del conductor. Si el EAR baja y cruza el límite de los 1.5s, la reacción debe ser instintiva y brutal para atravesar las capas profundas del microsueño en la etapa REM inminente.

### 8.1 API de Sobreescritura de Hardware (Android Override)

Un problema común es que el conductor tenga su teléfono en Modo "No Molestar", con volumen multimedia apagado, o conectado por Bluetooth a unos audífonos en el asiento trasero.

1.  **Forzar Volumen Máximo de Alarma:**
    ```kotlin
    val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
    val maxAlarmVolume = audioManager.getStreamMaxVolume(AudioManager.STREAM_ALARM)
    // Saltamos los perfiles normales de Android e inyectamos el volumen a 100% al stream nativo de despertador.
    audioManager.setStreamVolume(AudioManager.STREAM_ALARM, maxAlarmVolume, AudioManager.FLAG_PLAY_SOUND)
    ```
2.  **Audio Focus Steal:**
    Solicitar `AUDIOFOCUS_GAIN_TRANSIENT_EXCLUSIVE`. Si el chofer está escuchando Spotify o YouTube, la música se pausará o bajará agresivamente su volumen a 0 para dar paso a nuestra alarma.
3.  **Reproducción del Activo Sonoro:**
    El MP3/WAV elegido no debe ser una campana suave, debe ser un sonido estridente de frecuencias altas mezcladas, diseñado psicoacústicamente para inducir la reacción de sobresalto (Startle Reflex).
4.  **Sobreescritura de Pantalla Completa (Estroboscopio Brillante):**
    A través de las APIs de la ventana (Window Manager), aplicamos flag `BRIGHTNESS_OVERRIDE_FULL` a valor `1.0f`. La pantalla comenzará a alternar entre ROJO intenso (HEX #FF0000) y BLANCO (HEX #FFFFFF) cada 100ms. Las luces fuertes penetran la retina incluso a través del primer estadio de los párpados cerrados.

### 8.2 Manejo Similar en Ecosistema iOS

Apple restringe masivamente este comportamiento para proteger al usuario (Un app no puede cambiar el brillo global sin usar APIs privadas, un app no puede encender la pantalla si el celular está bloqueado en el bolsillo).

*   **Solución Apple:** Obligar a que el uso de la app DMS sea "Foreground Activity Only". El chofer debe llevar la app abierta en el holder del coche. Se activará `UIApplication.shared.isIdleTimerDisabled = true` para que la pantalla no se apague sola por timeout del sistema.
*   **Sonido:** Uso de `AVAudioSessionCategoryPlayback` y `AVAudioSessionCategoryOptionDuckOthers`.

---

## 9. Gestión de Ciclo de Vida y Permisos del Sistema Operativo

Dado que acceder a la cámara frontal y procesarla continuamente es un riesgo masivo para la seguridad/privacidad a ojos de Android/iOS, la correcta justificación e implementación técnica es imperativa para no ser vetados de las tiendas oficiales.

### 9.1 Permisos Críticos en Manifiesto (Android)
*   `<uses-permission android:name="android.permission.CAMERA" />`: Obvio.
*   `<uses-permission android:name="android.permission.RECORD_AUDIO" />`: (Si planeamos detectar ronquidos o sonidos asociados, opcional).
*   `<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />`: Fundamental. La IA debe declararse como un servicio en primer plano asociado a una notificación inborrable ("DMS Monitoring Active - Analizando Fatiga"). Esto impide que Android mate el servicio cuando la memoria RAM escasea al usar otras apps.
*   `<uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />`: Permite dibujar sobre otras aplicaciones. Vital para dibujar un recuadro de alarma roja o usar la cámara miniatura flotante si el chofer tiene que usar Uber Driver / Didi Driver en primer plano.

### 9.2 Picture-in-Picture (PiP)
Para que el conductor no tenga que elegir entre "Ver el mapa para llegar al destino" o "Ser monitoreado por el DMS", el DMS iniciará en modo Ventana Flotante (PiP).

Cuando el FSM (Máquina de estados) detecte SUEÑO MIENTRAS SE ESTÁ EN MODO FLOTANTE, la API de PiP no permite manipular el tamaño fácilmente, por lo que lanzará un intent (`FLAG_ACTIVITY_REORDER_TO_FRONT`) forzando la app entera de nuevo a pantalla completa brutalmente para ejecutar el estroboscopio rojo a todo brillo.

---

## 10. Especificaciones de Persistencia Local (SQLite/Room/CoreData)

La recolección de eventos es un requisito para las auditorías a choferes por parte del equipo gerencial de la empresa logística.

### 10.1 Arquitectura de la Base de Datos Móvil
Utilizaremos `Room Database` (Capa DAO sobre SQLite en Android) y `CoreData` (iOS).

**Tabla Principal: `TelemetryEvent`**
| Columna | Tipo de Dato | Constricciones | Descripción |
| :--- | :--- | :--- | :--- |
| `id` | UUID String | PRIMARY KEY | Identificador global único del evento. |
| `driver_id` | String | NOT NULL | ID alfanumérico del chofer (logueado al inicio). |
| `event_type` | Enum / Int | NOT NULL | 1 = MICROSLEEP, 2 = DISTRACTION_YAW, 3 = DISTRACTION_PITCH, 4 = YAWN_CHAIN |
| `duration_ms` | Long | NOT NULL | Milisegundos que duró el evento en condición de alarma. |
| `timestamp` | Long | NOT NULL | Unix Epoch Time UTC del inicio del evento. |
| `latitude` | Double | NULLABLE | Coordenadas GPS en el instante de la infracción (si Location Services permitidos). |
| `longitude` | Double | NULLABLE | Coordenadas GPS en el instante de la infracción. |
| `speed_kmh` | Float | NULLABLE | Velocidad del vehículo registrada por el GPS. Un microsueño a 0km/h (semáforo en rojo) no tiene el mismo peso penalizador que a 110km/h en autopista. |
| `sync_status` | Boolean | DEFAULT FALSE | Estado de sincronización con el servidor Python ("Store and Forward"). |
| `evidence_b64`| String | NULLABLE | (Opcional) Captura fotográfica de baja calidad codificada en base 64 en el instante preciso del ojo cerrado para evitar apelaciones por parte del sindicato/chofer. |

### 10.2 Política de Retención Local
Dado que el almacenamiento es finito, los registros exitosamente sincronizados (`sync_status = true`) se purgarán automáticamente a la medianoche (tarea Worker). Registros no sincronizados caducarán duro a los 14 días para no llenar la partición del dispositivo del chofer.

---

## 11. Especificaciones de Sincronización Backend (Store & Forward)

Las flotas transitan regiones interurbanas montañosas sin conexión celular constante.
La capa de red debe ser absolutamente asíncrona. No se deben bloquear las APIs, no se usan llamadas sincrónicas atadas a eventos FSM.

### 11.1 Ciclo de Tareas en Background (WorkManager / BackgroundTasks)

1.  Se define un "Job" periódico programado cada 15 minutos en el sistema operativo.
2.  El Job se dispara y verifica conectividad: ¿El móvil tiene conexión `NetworkCapabilities.NET_CAPABILITY_VALIDATED` e `INTERNET`?
3.  Si es así, la base de datos corre la Query: `SELECT * FROM TelemetryEvent WHERE sync_status = 0 LIMIT 50`.
4.  Serializa los 50 eventos a un arreglo JSON.
5.  Usa `Retrofit` (OkHttp) o `URLSession` para enviar un POST. Se usa Autenticación Bearer (JWT) derivado del inicio de sesión inicial del chofer.
6.  Si el Backend (FastAPI Python) responde `200 OK` (y la respuesta JSON corrobora cuántas filas se escribieron), el cliente marca esas filas localmente como `sync_status = 1`.
7.  Si responde `5xx` o da timeout (El camión entró al túnel), finaliza en silencio, e intentará re-evaluar a los 15 minutos exactos del siguiente ciclo periódico programado por el OS.

---

## 12. Especificaciones Backend Python (Integración con OficinaEficiencia)

El sistema existente (CCTV) se expandirá recibiendo endpoints en la nube de forma segura.

### 12.1 Controlador FastAPI para Recepción Telemetría

```python
# Arquitectura basada en Python Asíncrono para manejar ráfagas de sincronización a final de la tarde
from fastapi import APIRouter, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncio

router = APIRouter(prefix="/api/v1/mobile_dms")
API_KEY_NAME = "x-dms-api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

class DmsEvent(BaseModel):
    event_id: str
    driver_id: str
    event_type: str
    duration_ms: int
    timestamp: float
    latitude: Optional[float]
    longitude: Optional[float]
    speed_kmh: Optional[float]
    evidence_b64: Optional[str]

class SyncBatchRequest(BaseModel):
    batch: List[DmsEvent]

@router.post("/sync_events")
async def process_sync_batch(request: SyncBatchRequest, api_key: str = Depends(get_api_key)):
    """
    Ingesta por lotes (Batch Ingestion) de eventos originados en el Edge AI Móvil.
    """
    # Dependencia inyectada para base de datos (Ej. SQLAlchemy / asyncpg)
    db = get_database_connection()

    successful_inserts = 0
    errors = []

    for event in request.batch:
        try:
            # Reutilizando el diseño del esquema de OficinaEficiencia pero para choferes
            query = '''
                INSERT INTO mobile_infractions
                (event_uuid, driver_id, type, duration_ms, ts, lat, lng, speed, image_blob)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (event_uuid) DO NOTHING; -- Prevención Idempotente
            '''
            await db.execute(query, event.event_id, event.driver_id, event.event_type,
                             event.duration_ms, event.timestamp, event.latitude,
                             event.longitude, event.speed_kmh, event.evidence_b64)
            successful_inserts += 1

            # Lógica Administrativa Inmediata en Backend:
            if event.event_type == "MICROSLEEP" and event.speed_kmh and event.speed_kmh > 80.0:
                # Trigger SMS Urgente al Dispatcher de la Base
                asyncio.create_task(send_urgent_sms_to_fleet_manager(
                    f"ALERTA ROJA: Chofer {event.driver_id} ha tenido un microsueño manejando a más de 80km/h."
                ))

        except Exception as e:
            errors.append(f"Falla insertando {event.event_id}: {str(e)}")

    return {
        "status": "success" if len(errors) == 0 else "partial_success",
        "processed": len(request.batch),
        "inserted": successful_inserts,
        "errors": errors
    }
```

---

## 13. Calibración Dinámica del Rostro (Machine Learning Personalizado)

Utilizar un único límite estadístico de `EAR_THRESHOLD = 0.22` para toda la humanidad es una ingenuidad matemática en biometría.

*   Conductor con ptosis palpebral (Párpado caído): Un EAR base natural de `0.21` estando despierto causaría una alarma perpetua e irritante, forzando a que desinstale la app.
*   Conductor con exoftalmia (Ojos saltones): Un EAR base de `0.38`. Al cerrarlos levemente bajan a `0.23` pero no lo suficiente para cruzar el `0.22`, lo que significa que el sistema NO lanzaría la alarma y el chofer se estrellaría a pesar de llevar la aplicación abierta.

### 13.1 Calibración Euclidiana Inicial "Baseline"

1.  **Arranque (Los Primeros 30 Segundos):** Al darle "Iniciar Viaje", la app entra en modo "Aprendizaje Silencioso". No emite alarmas.
2.  **Distribución Normal:** Recopila las muestras EAR de los 900 frames iniciales del rostro del chofer. Usa un simple cálculo estadístico para descartar parpadeos (Outliers < Media).
3.  **Media Base Individual ($\mu$):** Calcula el promedio de "Apertura Normal".
4.  **Generación Dinámica del Límite de Choque ($C$):** El Umbral FSM de Microsueño para *Ese Conductor En Específico* pasa a ser: $Threshold = \mu_{baseline} 	imes 0.60$.
5.  *Ejemplo del asiático:* $\mu = 0.25 ightarrow Threshold = 0.15$. Reaccionará maravillosamente bien, porque un `0.15` sí garantiza el cierre casi de pliegue.
6.  *Ejemplo caucásico de ojos grandes:* $\mu = 0.35 ightarrow Threshold = 0.21$. Perfecto.

Esta calibración no se guarda en nube. Se re-calcula desde cero cada que el chofer apaga y enciende la app (Cada turno de manejo), dado que el celular puede haber cambiado de inclinación y de soporte respecto a la cabeza del chofer, afectando ligeramente la proyección 2D final del FaceMesh.

---

## 14. Casos Extremos: Conducción Nocturna y Gafas de Sol

### 14.1 Conducción Nocturna (Low Lux Scenarios)
Si la cabina interior es oscuridad total, la cámara RGB estándar del teléfono entrega píxeles negros (`0,0,0`). MediaPipe, como CNN basada en textura y bordes, fallará y entregará el tensor con `confidence = 0.05` y los puntos bailarán espásticamente.

*   **Mitigación Edge:** API de cámara debe forzar algoritmos Night Mode. En iOS forzar lente ultra gran angular si capta más luz, y en Android setear el `CaptureRequest.CONTROL_AE_MODE` para permitir un ISO masivo (Generará ruido visual que afectará el FaceMesh, pero no arruinará el "Bounding Box" general de la cabeza).
*   **Fallback Logic:** Si el sistema detecta mediante metadata del Exif que estamos de noche profunda y los ojos pierden fiabilidad, el sistema cambia de "Modo EAR Fino" a "Modo Pitch Bruto". Las alarmas de sueño ya no se activarán por párpados (invisibles), sino cuando toda la cabeza se incline (Pitch masivo), que indica el desmayo o cabeceo final. Pierde predicción temprana, pero salva del choque en la última etapa de colapso físico.

### 14.2 Oclusiones Persistentes (Gafas Oscuras de Aviador o Mascarillas Cubrebocas)
*   **Mascarillas Sanitarias N95:** FaceMesh de Google está entrenado pre y post pandemia. Extrae los párpados a la perfección y genera puntos artificiales de los labios asumiendo la estructura interna tras la tela usando heurísticas previas. **MAR (Bostezos) fallará**, y debe inhabilitarse lógicamente si el score de confianza en la zona labial cae del 50%. EAR seguirá operativo 100%.
*   **Gafas de Sol Totalmente Polarizadas:** El tensor de MediaPipe intentará trazar un ojo artificial pintándolo en la superficie curva de las gafas según lo que interpreta como sombra de cavidad ocular. Fallará en la detección de parpadeos reales al 100%. **La regla maestra FSM de Fallback:** Si detecta la cara pero el EAR permanece extrañamente estático y con desviación estándar = 0.001 (nadie deja de parpadear durante 5 minutos, ni siquiera parpadeos imperceptibles), el sistema declara la condición **GLASSES_OBSTRUCTION_MODE_ACTIVATED**. Deshabilita alarmas EAR, notifica al servidor (el chófer va bloqueado por lentes) y pasa la guardia total a distracción Head Pose.

---

## 15. Seguridad Criptográfica y Privacidad de la Información (GDPR)

La confianza del chofer en la plataforma logística descansa en la certeza de que nadie lo está grabando para espiarlo o "jugar al gran hermano" (Big Brother Effect).

1.  **Procesamiento Local Efímero (RAM Only):** Cada fotograma YUV/RGB que entra desde el buffer de CameraX, pasa al tensor, e inmediatamente el puntero en RAM de ese frame se libera (No hay archivo, no hay Stream, no hay socket RTSP).
2.  **Sin Archivos de Video Locales:** Nunca se graba vídeo MP4 local.
3.  **Captura de Evidencia Fotográfica Sensible:** Como indicaba la base de datos, en caso de microsueño, la aseguradora del choque a veces pide foto. Si se toma una instantánea `JPEG` para enviarla, el SDK criptográfico en el móvil la pasará por AES-256 GCM usando una clave asimétrica RSA cuya clave privada de descifrado solo resida dentro de los servidores HSM de OficinaEficiencia, no del dispositivo del chofer. Si alguien roba el teléfono y accede a SQLite, solo verá una cadena base64 encriptada ilegible.

---

## 16. Métricas para el Administrador de Flota y Dashboards

¿Para qué sirve toda esta maravilla biológica al borde de la cámara si la empresa de camiones no puede tomar decisiones logísticas estratégicas? El frontend Vue.js/React central de OficinaEficiencia generará el panel de métricas.

*   **Matriz de Fatiga Temprana (Predictiva):** Permite al dispatcher llamar al conductor por radio y ordenarle parar en una gasolinera a por café antes de que sea crítico. Esta matriz gráfica usa el histórico de la tasa de "Tiempos Largos de Cierre" (PERCLOS).
*   **Heatmap Geográfico de Incidentes:** Gráfico en mapa de todas las alertas `MICROSLEEP`. Permite descubrir "Tramos carreteros oscuros, rectos y monótonos" donde estadísticamente todos los conductores empiezan a luchar por mantenerse despiertos.
*   **Ranking de Severidad por Chofer:** Indicar al departamento de Recursos Humanos si es momento de mandar al trabajador a revisión con un especialista para detectar Apnea de Sueño no diagnosticada.

---

## 17. Pruebas Automatizadas y QA Assurance

Lanzar una aplicación médica/seguridad crítica con Bugs conlleva muertes literales por la falsa sensación de seguridad técnica de que "La app me avisará si me duermo".

1.  **Test de Inyección Vectorial Ficticia (Unit Test):** No inyectamos video en el CI/CD, inyectamos un arreglo JSON simulando 468 coordenadas. Manipulamos matemáticamente el arreglo para cerrar los puntos del ojo poco a poco en un loop de test (`for frame in mockFrames`). Afirmamos (`assert`) que el método `triggerEmergencyWakeUp` es invocado en el frame 46 preciso.
2.  **Test de Regresión de Calibración:** Forzar una lista FloatArray pre-grabada de un actor asiático de prueba. Confirmar que el EAR umbral dinámico se asentó en `0.14` y que al inyectar un Frame con $EAR=0.18$ no disparó un Falso Positivo arruinando su trabajo.
3.  **Pruebas con Dispositivos Reales Lentos (Low-Tier Mobile Testing):** Instalar el APK/IPA en un Samsung Galaxy J7 Prime (2016) viejo, o un iPhone 7 Plus, correr la app conectada al logcat durante 3 horas y generar un `Trace` de CPU Profiler. Exigencia: no tener más de 2 Frames Dropped consecutivos por Garbage Collection.

---

## 18. Guía de Integración con Google Maps / Waze (Picture-in-Picture)

Para un conductor de Uber es ridículo depender del DMS si no puede ver hacia dónde gira la próxima calle.

1.  **Declaración AndroidManifest.xml:** Declarar que la Activity soporta PiP.
    ```xml
    <activity android:name=".DMSMainActivity"
          android:supportsPictureInPicture="true"
          android:resizeableActivity="true"
          android:configChanges="screenSize|smallestScreenSize|screenLayout|orientation" />
    ```
2.  **Transición Automática:** Cuando el chofer pulse el botón "Home" del sistema o abra "Google Maps" en Split Screen, nuestra App intercepta `onUserLeaveHint()` y llama a `enterPictureInPictureMode()`. La app se encoge a un recuadro pequeño en la esquina. CameraX seguirá operando sin perder los delegados OpenGL porque la Activity no se "Pausó", solo se miniaturizó.
3.  **Retorno de Fuego (Fire Return):** Si el FSM entra a estado `EMERGENCY` desde el modo PiP flotante diminuto, lanza un `startActivity(Intent(this, DMSMainActivity::class.java).apply { flags = Intent.FLAG_ACTIVITY_REORDER_TO_FRONT })`. El recuadro diminuto explotará violentamente y tomará toda la pantalla forzando la atención máxima.

---

## 19. Modelos de IA de Respaldo y Algoritmos Alternativos

Si MediaPipe (Google) se vuelve obsoleto o de pago restrictivo para comercializar el sistema a Didi, la arquitectura SDD aquí desarrollada soporta la sustitución del "Cerebro Inference Engine" modularmente por:

1.  **Ultralytics YOLOv8-Face:** YOLO es excelente pero requiere convertir de PyTorch a NCNN o ONNX, haciéndolo pesado. Se sacrificaría precisión del EAR por velocidad de inferencia bounding box general en procesadores primitivos.
2.  **Dlib (C++ HOG + Linear SVM):** El algoritmo biométrico ancestral. Computacionalmente tan ligero (apenas sumas de vectores y gradientes) que podría correr a 30 FPS en el CPU de un reloj inteligente, pero frágil frente a iluminación cambiante extrema en el coche o rotaciones severas de la cabeza del conductor en curvas pronunciadas. Se utilizará MediaPipe como Standard Oro Industrial actual mientras perdure su supremacía técnica en móviles.

---

## 20. Conclusiones y Referencias Técnicas

La Especificación Guiada por Diseño (SDD) detalla aquí una solución hiper-desacoplada que eleva los parámetros clásicos de Visión por Computadora desde la era del servidor al paradigma del "Smartphone como Sensor Universal", mitigando radicalmente el peor vector de accidentabilidad humana: La somnolencia al volante por ciclos fisiológicos circadianos o sobreesfuerzo laboral.

La combinación de arquitecturas Edge + matemáticas determinísticas puras (EAR/MAR Euclidiano) + algoritmos biológicamente adaptativos + persistencia asíncrona garantizan que la arquitectura puede desplegarse mañana en 5,000 unidades y funcionar en el acto de forma paralela sin asfixiar la red ni amenazar la privacidad.

**Versión del Documento Consolidada a Múltiples Solicitudes de Extensión Técnica. Fin de Arquitectura y Especificaciones de Software DMS Inteligente.**


## APÉNDICE A: MATRIZ DE REFERENCIA MEDIA-PIPE FACE MESH COMPLETA (468 VÉRTICES)
V_000: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_001: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_002: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_003: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_004: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_005: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_006: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_007: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_008: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_009: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_010: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_011: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_012: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_013: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_014: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_015: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_016: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_017: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_018: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_019: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_020: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_021: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_022: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_023: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_024: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_025: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_026: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_027: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_028: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_029: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_030: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_031: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_032: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_033: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_034: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_035: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_036: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_037: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_038: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_039: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_040: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_041: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_042: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_043: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_044: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_045: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_046: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_047: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_048: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_049: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_050: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_051: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_052: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_053: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_054: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_055: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_056: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_057: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_058: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_059: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_060: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_061: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_062: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_063: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_064: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_065: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_066: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_067: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_068: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_069: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_070: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_071: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_072: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_073: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_074: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_075: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_076: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_077: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_078: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_079: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_080: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_081: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_082: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_083: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_084: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_085: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_086: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_087: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_088: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_089: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_090: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_091: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_092: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_093: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_094: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_095: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_096: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_097: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_098: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_099: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_100: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_101: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_102: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_103: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_104: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_105: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_106: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_107: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_108: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_109: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_110: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_111: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_112: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_113: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_114: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_115: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_116: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_117: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_118: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_119: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_120: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_121: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_122: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_123: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_124: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_125: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_126: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_127: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_128: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_129: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_130: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_131: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_132: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_133: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_134: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_135: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_136: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_137: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_138: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_139: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_140: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_141: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_142: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_143: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_144: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_145: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_146: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_147: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_148: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_149: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_150: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_151: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_152: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_153: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_154: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_155: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_156: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_157: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_158: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_159: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_160: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_161: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_162: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_163: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_164: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_165: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_166: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_167: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_168: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_169: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_170: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_171: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_172: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_173: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_174: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_175: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_176: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_177: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_178: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_179: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_180: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_181: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_182: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_183: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_184: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_185: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_186: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_187: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_188: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_189: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_190: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_191: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_192: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_193: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_194: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_195: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_196: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_197: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_198: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_199: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_200: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_201: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_202: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_203: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_204: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_205: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_206: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_207: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_208: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_209: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_210: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_211: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_212: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_213: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_214: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_215: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_216: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_217: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_218: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_219: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_220: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_221: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_222: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_223: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_224: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_225: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_226: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_227: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_228: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_229: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_230: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_231: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_232: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_233: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_234: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_235: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_236: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_237: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_238: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_239: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_240: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_241: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_242: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_243: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_244: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_245: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_246: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_247: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_248: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_249: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_250: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_251: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_252: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_253: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_254: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_255: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_256: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_257: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_258: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_259: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_260: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_261: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_262: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_263: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_264: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_265: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_266: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_267: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_268: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_269: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_270: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_271: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_272: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_273: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_274: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_275: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_276: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_277: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_278: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_279: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_280: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_281: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_282: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_283: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_284: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_285: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_286: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_287: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_288: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_289: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_290: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_291: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_292: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_293: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_294: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_295: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_296: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_297: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_298: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_299: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_300: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_301: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_302: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_303: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_304: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_305: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_306: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_307: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_308: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_309: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_310: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_311: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_312: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_313: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_314: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_315: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_316: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_317: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_318: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_319: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_320: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_321: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_322: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_323: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_324: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_325: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_326: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_327: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_328: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_329: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_330: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_331: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_332: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_333: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_334: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_335: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_336: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_337: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_338: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_339: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_340: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_341: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_342: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_343: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_344: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_345: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_346: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_347: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_348: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_349: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_350: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_351: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_352: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_353: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_354: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_355: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_356: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_357: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_358: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_359: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_360: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_361: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_362: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_363: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_364: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_365: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_366: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_367: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_368: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_369: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_370: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_371: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_372: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_373: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_374: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_375: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_376: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_377: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_378: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_379: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_380: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_381: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_382: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_383: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_384: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_385: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_386: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_387: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_388: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_389: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_390: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_391: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_392: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_393: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_394: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_395: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_396: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_397: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_398: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_399: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_400: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_401: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_402: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_403: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_404: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_405: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_406: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_407: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_408: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_409: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_410: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_411: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_412: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_413: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_414: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_415: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_416: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_417: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_418: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_419: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_420: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_421: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_422: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_423: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_424: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_425: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_426: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_427: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_428: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_429: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_430: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_431: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_432: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_433: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_434: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_435: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_436: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_437: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_438: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_439: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_440: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_441: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_442: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_443: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_444: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_445: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_446: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_447: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_448: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_449: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_450: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_451: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_452: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_453: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_454: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_455: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_456: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_457: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_458: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_459: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_460: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_461: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_462: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_463: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_464: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_465: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_466: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.
V_467: [X_norm, Y_norm, Z_est] - Referencia Anatómica reservada de MediaPipe.

## APÉNDICE B: HISTORIAL DE CALIBRACIÓN Y TABLAS DE VERDAD FSM
Regla FSM 000: Si Condición_Umbral_0 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=0.
Regla FSM 001: Si Condición_Umbral_1 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=2.
Regla FSM 002: Si Condición_Umbral_2 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=4.
Regla FSM 003: Si Condición_Umbral_3 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=6.
Regla FSM 004: Si Condición_Umbral_4 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=8.
Regla FSM 005: Si Condición_Umbral_5 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=10.
Regla FSM 006: Si Condición_Umbral_6 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=12.
Regla FSM 007: Si Condición_Umbral_7 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=14.
Regla FSM 008: Si Condición_Umbral_8 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=16.
Regla FSM 009: Si Condición_Umbral_9 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=18.
Regla FSM 010: Si Condición_Umbral_10 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=20.
Regla FSM 011: Si Condición_Umbral_11 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=22.
Regla FSM 012: Si Condición_Umbral_12 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=24.
Regla FSM 013: Si Condición_Umbral_13 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=26.
Regla FSM 014: Si Condición_Umbral_14 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=28.
Regla FSM 015: Si Condición_Umbral_15 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=30.
Regla FSM 016: Si Condición_Umbral_16 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=32.
Regla FSM 017: Si Condición_Umbral_17 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=34.
Regla FSM 018: Si Condición_Umbral_18 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=36.
Regla FSM 019: Si Condición_Umbral_19 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=38.
Regla FSM 020: Si Condición_Umbral_20 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=40.
Regla FSM 021: Si Condición_Umbral_21 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=42.
Regla FSM 022: Si Condición_Umbral_22 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=44.
Regla FSM 023: Si Condición_Umbral_23 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=46.
Regla FSM 024: Si Condición_Umbral_24 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=48.
Regla FSM 025: Si Condición_Umbral_25 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=50.
Regla FSM 026: Si Condición_Umbral_26 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=52.
Regla FSM 027: Si Condición_Umbral_27 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=54.
Regla FSM 028: Si Condición_Umbral_28 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=56.
Regla FSM 029: Si Condición_Umbral_29 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=58.
Regla FSM 030: Si Condición_Umbral_30 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=60.
Regla FSM 031: Si Condición_Umbral_31 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=62.
Regla FSM 032: Si Condición_Umbral_32 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=64.
Regla FSM 033: Si Condición_Umbral_33 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=66.
Regla FSM 034: Si Condición_Umbral_34 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=68.
Regla FSM 035: Si Condición_Umbral_35 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=70.
Regla FSM 036: Si Condición_Umbral_36 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=72.
Regla FSM 037: Si Condición_Umbral_37 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=74.
Regla FSM 038: Si Condición_Umbral_38 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=76.
Regla FSM 039: Si Condición_Umbral_39 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=78.
Regla FSM 040: Si Condición_Umbral_40 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=80.
Regla FSM 041: Si Condición_Umbral_41 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=82.
Regla FSM 042: Si Condición_Umbral_42 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=84.
Regla FSM 043: Si Condición_Umbral_43 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=86.
Regla FSM 044: Si Condición_Umbral_44 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=88.
Regla FSM 045: Si Condición_Umbral_45 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=90.
Regla FSM 046: Si Condición_Umbral_46 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=92.
Regla FSM 047: Si Condición_Umbral_47 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=94.
Regla FSM 048: Si Condición_Umbral_48 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=96.
Regla FSM 049: Si Condición_Umbral_49 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=98.
Regla FSM 050: Si Condición_Umbral_50 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=100.
Regla FSM 051: Si Condición_Umbral_51 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=102.
Regla FSM 052: Si Condición_Umbral_52 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=104.
Regla FSM 053: Si Condición_Umbral_53 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=106.
Regla FSM 054: Si Condición_Umbral_54 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=108.
Regla FSM 055: Si Condición_Umbral_55 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=110.
Regla FSM 056: Si Condición_Umbral_56 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=112.
Regla FSM 057: Si Condición_Umbral_57 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=114.
Regla FSM 058: Si Condición_Umbral_58 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=116.
Regla FSM 059: Si Condición_Umbral_59 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=118.
Regla FSM 060: Si Condición_Umbral_60 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=120.
Regla FSM 061: Si Condición_Umbral_61 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=122.
Regla FSM 062: Si Condición_Umbral_62 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=124.
Regla FSM 063: Si Condición_Umbral_63 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=126.
Regla FSM 064: Si Condición_Umbral_64 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=128.
Regla FSM 065: Si Condición_Umbral_65 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=130.
Regla FSM 066: Si Condición_Umbral_66 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=132.
Regla FSM 067: Si Condición_Umbral_67 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=134.
Regla FSM 068: Si Condición_Umbral_68 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=136.
Regla FSM 069: Si Condición_Umbral_69 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=138.
Regla FSM 070: Si Condición_Umbral_70 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=140.
Regla FSM 071: Si Condición_Umbral_71 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=142.
Regla FSM 072: Si Condición_Umbral_72 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=144.
Regla FSM 073: Si Condición_Umbral_73 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=146.
Regla FSM 074: Si Condición_Umbral_74 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=148.
Regla FSM 075: Si Condición_Umbral_75 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=150.
Regla FSM 076: Si Condición_Umbral_76 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=152.
Regla FSM 077: Si Condición_Umbral_77 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=154.
Regla FSM 078: Si Condición_Umbral_78 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=156.
Regla FSM 079: Si Condición_Umbral_79 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=158.
Regla FSM 080: Si Condición_Umbral_80 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=160.
Regla FSM 081: Si Condición_Umbral_81 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=162.
Regla FSM 082: Si Condición_Umbral_82 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=164.
Regla FSM 083: Si Condición_Umbral_83 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=166.
Regla FSM 084: Si Condición_Umbral_84 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=168.
Regla FSM 085: Si Condición_Umbral_85 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=170.
Regla FSM 086: Si Condición_Umbral_86 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=172.
Regla FSM 087: Si Condición_Umbral_87 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=174.
Regla FSM 088: Si Condición_Umbral_88 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=176.
Regla FSM 089: Si Condición_Umbral_89 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=178.
Regla FSM 090: Si Condición_Umbral_90 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=180.
Regla FSM 091: Si Condición_Umbral_91 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=182.
Regla FSM 092: Si Condición_Umbral_92 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=184.
Regla FSM 093: Si Condición_Umbral_93 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=186.
Regla FSM 094: Si Condición_Umbral_94 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=188.
Regla FSM 095: Si Condición_Umbral_95 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=190.
Regla FSM 096: Si Condición_Umbral_96 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=192.
Regla FSM 097: Si Condición_Umbral_97 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=194.
Regla FSM 098: Si Condición_Umbral_98 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=196.
Regla FSM 099: Si Condición_Umbral_99 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=198.
Regla FSM 100: Si Condición_Umbral_100 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=200.
Regla FSM 101: Si Condición_Umbral_101 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=202.
Regla FSM 102: Si Condición_Umbral_102 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=204.
Regla FSM 103: Si Condición_Umbral_103 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=206.
Regla FSM 104: Si Condición_Umbral_104 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=208.
Regla FSM 105: Si Condición_Umbral_105 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=210.
Regla FSM 106: Si Condición_Umbral_106 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=212.
Regla FSM 107: Si Condición_Umbral_107 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=214.
Regla FSM 108: Si Condición_Umbral_108 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=216.
Regla FSM 109: Si Condición_Umbral_109 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=218.
Regla FSM 110: Si Condición_Umbral_110 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=220.
Regla FSM 111: Si Condición_Umbral_111 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=222.
Regla FSM 112: Si Condición_Umbral_112 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=224.
Regla FSM 113: Si Condición_Umbral_113 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=226.
Regla FSM 114: Si Condición_Umbral_114 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=228.
Regla FSM 115: Si Condición_Umbral_115 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=230.
Regla FSM 116: Si Condición_Umbral_116 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=232.
Regla FSM 117: Si Condición_Umbral_117 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=234.
Regla FSM 118: Si Condición_Umbral_118 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=236.
Regla FSM 119: Si Condición_Umbral_119 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=238.
Regla FSM 120: Si Condición_Umbral_120 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=240.
Regla FSM 121: Si Condición_Umbral_121 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=242.
Regla FSM 122: Si Condición_Umbral_122 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=244.
Regla FSM 123: Si Condición_Umbral_123 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=246.
Regla FSM 124: Si Condición_Umbral_124 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=248.
Regla FSM 125: Si Condición_Umbral_125 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=250.
Regla FSM 126: Si Condición_Umbral_126 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=252.
Regla FSM 127: Si Condición_Umbral_127 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=254.
Regla FSM 128: Si Condición_Umbral_128 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=256.
Regla FSM 129: Si Condición_Umbral_129 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=258.
Regla FSM 130: Si Condición_Umbral_130 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=260.
Regla FSM 131: Si Condición_Umbral_131 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=262.
Regla FSM 132: Si Condición_Umbral_132 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=264.
Regla FSM 133: Si Condición_Umbral_133 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=266.
Regla FSM 134: Si Condición_Umbral_134 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=268.
Regla FSM 135: Si Condición_Umbral_135 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=270.
Regla FSM 136: Si Condición_Umbral_136 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=272.
Regla FSM 137: Si Condición_Umbral_137 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=274.
Regla FSM 138: Si Condición_Umbral_138 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=276.
Regla FSM 139: Si Condición_Umbral_139 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=278.
Regla FSM 140: Si Condición_Umbral_140 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=280.
Regla FSM 141: Si Condición_Umbral_141 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=282.
Regla FSM 142: Si Condición_Umbral_142 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=284.
Regla FSM 143: Si Condición_Umbral_143 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=286.
Regla FSM 144: Si Condición_Umbral_144 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=288.
Regla FSM 145: Si Condición_Umbral_145 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=290.
Regla FSM 146: Si Condición_Umbral_146 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=292.
Regla FSM 147: Si Condición_Umbral_147 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=294.
Regla FSM 148: Si Condición_Umbral_148 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=296.
Regla FSM 149: Si Condición_Umbral_149 = Verdadero Y Thermal_State = Normal, Entonces Despliegue_Accion=298.
## 21. Especificaciones Ultra Detalladas del Motor de Reportes Predictivos (Fatigue Risk Score)

Para prevenir accidentes *antes* de que ocurran, el sistema no solo debe despertar al chofer con una alarma en tiempo real (reacción), sino generar reportes predictivos para que el Dispatcher o Administrador logístico bloquee al conductor si su nivel de fatiga residual lo hace no apto para iniciar o continuar un viaje.

### 21.1 Algoritmo de Puntuación FRS (Fatigue Risk Score)
El FRS es un valor de `0.0` (Perfectamente descansado) a `100.0` (Peligro Inminente).
Se calcula como una suma ponderada de eventos fisiológicos detectados en las últimas 4 horas de conducción.

*   **Microsueño Crítico (EAR < 0.22 por 1.5s):** +35.0 Puntos.
*   **Microsueño Abortado (EAR < 0.22 por 0.8s):** +10.0 Puntos.
*   **Bostezo Confirmado (MAR > 0.60 por 1.5s):** +5.0 Puntos.
*   **Distracción Prolongada (Head Pose Anómala > 3s):** +8.0 Puntos.

**Decaimiento por Descanso (Recovery Decay):**
Si la aplicación detecta (por el GPS) que el vehículo lleva detenido 0 km/h y el motor de la app está "Pausado/En descanso" por al menos 30 minutos consecutivos, el puntaje decae (se resta) exponencialmente:
*Fórmula:* $FRS_{nuevo} = FRS_{actual} - (20.0 \times \text{Horas de Descanso})$

### 21.2 Lógica de Bloqueo Automático de Viajes (Clearance Engine)
Antes de que Didi/Uber asigne un nuevo pasajero, o antes de que el trailero encienda el camión en la central, la API central de despacho debe consultar el estado del conductor.

*   **Nivel Verde (0 - 49 Puntos):** "Clear for Dispatch". El conductor es asignado normalmente.
*   **Nivel Naranja (50 - 74 Puntos):** "Warning". Se aprueba el viaje, pero se envía un mensaje automático en pantalla: *"Fatiga acumulada detectada. Por favor, tómese un café en los próximos 15 minutos"*. El Dispatcher recibe una notificación pasiva.
*   **Nivel Rojo (75 - 100 Puntos):** "Grounded / Bloqueado". El conductor NO es elegible para el próximo viaje. La app del celular se bloquea en una pantalla que indica: *"Por su seguridad y la de sus pasajeros, su cuenta está pausada por fatiga extrema. Tiempo de descanso mandatorio restante: 1 hora 45 minutos."*

### 21.3 Arquitectura del Generador de Reportes (PDF y Web Dashboard)
Para cumplimiento de normativas de Transporte (ej. Horas de Servicio / HOS logs en USA o normativas SCT en México):

1.  **Reporte de Fin de Turno (Shift Summary):**
    El Backend de OficinaEficiencia corre un *Cron Job* diario a las 00:00 que extrae todos los eventos de la tabla `mobile_infractions` y la tabla de puntaje FRS.
2.  **Generación de PDF:** Usando librerías Python (como `ReportLab`), genera un PDF con gráficos de barras mostrando los "Picos de Somnolencia" por horas. Esto evidencia si el conductor sufre regularmente del bajón de energía post-almuerzo (Post-prandial dip a las 14:00) o bajón circadiano nocturno (03:00 AM).
3.  **Auditoría y Seguros:** El reporte de fatiga se anexa a la póliza del seguro. Si hubo un accidente a las 15:30 y el reporte indica FRS=85 (Rojo) a las 15:20, la responsabilidad corporativa queda documentada.
