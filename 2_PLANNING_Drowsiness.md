# Planificación del Proyecto - Sistema de Monitoreo de Conductores (DMS)

## 1. Visión del Proyecto y Alcance
El proyecto consiste en el desarrollo de un motor de Visión Artificial Móvil (Edge AI) para dispositivos iOS/Android. Este motor operará en segundo plano mientras el conductor utiliza plataformas de movilidad (Uber, Didi), analizando en tiempo real la somnolencia (EAR/PERCLOS) y la distracción visual, para emitir alertas de despertar críticas de latencia cero, sincronizando las infracciones graves con el backend central (`OficinaEficiencia`).

**Duración Estimada:** 12 Semanas
**Metodología:** Agile (Scrum con Sprints de 2 semanas)

## 2. Estructura del Equipo (Roles Necesarios)
- **Product Owner (PO):** Define la visión del producto, prioriza funcionalidades (ej. Alertas Sonoras vs Dashboard Web).
- **Tech Lead / AI Engineer:** Diseña la arquitectura Edge AI (MediaPipe) y calibra las matemáticas (EAR, PnP).
- **Mobile Developer (Android - Kotlin):** Implementación nativa, manejo del ciclo de vida de la cámara y optimización térmica de dispositivos Android.
- **Mobile Developer (iOS - Swift):** Implementación nativa usando AVFoundation y manejo estricto de permisos de Apple (Notificaciones críticas en Background).
- **Backend Developer (Python):** Adapta la base de datos actual y crea el API REST/Websockets para ingestar los incidentes de microsueños.
- **QA / Test Engineer:** Crea los casos de prueba (unitarios, simuladores) e idealmente pruebas físicas de campo (Driving Simulator).

## 3. Cronograma de Sprints

### Sprint 1: "Prueba de Concepto y Hardware Base" (Semana 1-2)
* **Objetivo:** Lograr capturar la cámara frontal y renderizar los landmarks faciales de MediaPipe a 30 FPS.
* **Entregable:** App básica que muestra los 468 puntos sobre el rostro sin calentamiento excesivo en un móvil de gama media.

### Sprint 2: "Core Biométrico y Algoritmos" (Semana 3-4)
* **Objetivo:** Convertir los puntos (X, Y, Z) en mediciones utilizables.
* **Entregable:** Cálculo continuo en consola de `EAR` (Ojos), `MAR` (Boca/Bostezo) y `Head Pose` (Yaw, Pitch, Roll). Implementar Máquina de Estados (Normal -> Cansado -> Crítico).

### Sprint 3: "Sistema de Alertas Críticas de Latencia Cero" (Semana 5-6)
* **Objetivo:** "Despertar al Conductor". Forzar la reproducción de alertas sonoras sobrepasando el "Modo Silencio" del móvil y estroboscopio visual rojo.
* **Entregable:** La app grita/vibra fuertemente tras 1.5 segundos de cierre ocular continuo, deteniéndose solo si el EAR se recupera.

### Sprint 4: "Backend API y Persistencia Local Móvil" (Semana 7-8)
* **Objetivo:** Arquitectura "Store-and-Forward". Guardar los incidentes (SQL Local) y sincronizar cuando haya cobertura celular.
* **Entregable:** Integración de Room/CoreData y Worker/BackgroundTasks enviando JSONs firmados al backend Python.

### Sprint 5: "Optimización Térmica, PiP y Privacidad" (Semana 9-10)
* **Objetivo:** Hacer la app "Production-Ready" para jornadas de 8 horas al sol.
* **Entregable:** Bajada dinámica de FPS, modo Picture-in-Picture (PiP) para convivir con mapas, pantalla atenuada por defecto. Encriptado local.

### Sprint 6: "QA, Pruebas de Campo y Despliegue Beta" (Semana 11-12)
* **Objetivo:** Validar en escenarios reales y subir a tiendas.
* **Entregable:** Choferes beta testeando. Cumplimiento de Políticas de Privacidad de App Store (Apple) y Play Store (Google). Lanzamiento.

## 4. Gestión de Riesgos (Risk Management)

| Riesgo | Probabilidad | Impacto | Estrategia de Mitigación |
| :--- | :---: | :---: | :--- |
| **Baja iluminación en cabina** | Alta | Crítico | Utilizar ganancia alta en el sensor ISO. Considerar uso exclusivo en vehículos de flotilla con sensores IR. Implementar lógica "Fallback" basada solo en bostezos y yaw si no se detectan párpados fiables. |
| **Sobrecalentamiento (Thermal Throttling)** | Media | Alto | Implementar caída automática a 10-15 FPS y apagado de pantalla completo cuando se superen los 40°C en la batería. |
| **Rechazo en Apple App Store** | Media | Alto | Redactar documentación exhaustiva para Apple demostrando que los datos de FaceMesh no abandonan el dispositivo. Limitar permisos. |
| **Gafas de Sol** | Alta | Medio | Añadir "Head Pose Detection" estricta como mecanismo secundario al fallar la medición EAR por la oclusión negra. |

## 5. Criterios de Éxito (KPIs del Proyecto)
1. **Precisión EAR:** >95% de precisión en identificación de ojos cerrados en condiciones de buena/mediana luz.
2. **Latencia del Despertar:** Alarma emitida en un máximo de **200 ms** tras rebasar el umbral de los 1.5s críticos.
3. **Consumo de Batería:** Descarga no superior al 15-20% por hora en estado "dimmed screen" / PiP a 15 FPS.
4. **Data Size:** Transferencias al backend no mayores a 1MB diarios por conductor (Solo JSON, sin stream de video).
### Sprint 7: "Motor de Reportes Predictivos y Bloqueo de Despacho" (Semana 13-14)
* **Objetivo:** Transformar los datos crudos en decisiones de negocio que salven vidas *antes* del viaje (Predictivo). Implementar el FRS (Fatigue Risk Score).
* **Entregable (Backend Python):** Endpoint `/clearance` que responde si el chofer puede manejar o no basado en su FRS. Generación automatizada de PDFs diarios de "Horas de Servicio y Riesgo Biométrico".
* **Entregable (Móvil):** Pantalla de "Viaje Bloqueado por Fatiga Acumulada" con temporizador de cuenta regresiva para poder volver a conducir.

## 6. Integración Funcional con RRHH y Despacho
* **Rol Nuevo Requerido:** *Data Analyst / Gerente de Flota*. Quien interpretará los Reportes PDFs diarios de OficinaEficiencia para identificar choferes con probables trastornos de sueño (Apnea) y programarles exámenes médicos, en lugar de solo castigarlos.
