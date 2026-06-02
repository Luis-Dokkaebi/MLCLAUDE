# Code & Architecture Review - Sistema DMS Móvil

**Revisor:** Tech Lead / AI Architect
**Fecha:** 2023-10-25
**Objetivo:** Analizar las propuestas documentadas en los archivos de Especificaciones, Tareas e Implementación y asegurar su viabilidad para producción en Flotas (Didi/Uber).

## 1. Revisión de Arquitectura (Specs)

### Puntos Fuertes:
*   **Desacoplamiento Edge-Cloud:** Acertada decisión de usar MediaPipe localmente. Transmitir video 24/7 de mil choferes destruiría los servidores.
*   **Gestión Térmica:** Brillante la anticipación al "Thermal Throttling". Un celular al sol se apaga si no reducimos los FPS dinámicamente.
*   **Audio Focus Steal:** La idea de inyectar el sonido usando `AudioManager.STREAM_ALARM` al máximo nivel es la única forma real de despertar a un conductor que lleve Spotify a volumen bajo.

### Puntos de Mejora y Vulnerabilidades (A solucionar en próximos Sprints):
*   *Lentes Oscuros y Polarizados:* Las especificaciones mencionan pasar a control `Head Pose` (Cabeceo) si MediaPipe pierde los ojos por gafas oscuras. **Sin embargo, el cabeceo es muy tardío.** Si el conductor se duerme con la cabeza apoyada en el asiento (hacia atrás), el Pitch nunca pasará el umbral y se estrellará. **Acción requerida:** Evaluar la comercialización de accesorios infrarrojos Bluetooth o usar un enfoque basado en "Micro-correcciones de volante" consumiendo APIs del acelerómetro del celular si los ojos están tapados.

## 2. Revisión de Código e Implementación

### Análisis de la función `calculateEar()` en Kotlin
**Código Actual:**
```kotlin
fun calculateEar(landmarks: List<NormalizedLandmark>, eyeIndices: IntArray): Float { ... }
```
**Observación:** La implementación funciona, pero en un entorno móvil de baja gama, la creación iterativa y el boxing/unboxing de listas puede generar latencia.
**Aprobación:** CONDICIONADA. Se aprueba para MVP, pero debe refactorizarse a utilizar un arreglo de floats pre-alojados (C++ ByteBuffer style) para lograr *Zero Object Allocation* si se observan *Garbage Collection Pauses* mayores a 10ms.

### Análisis de la FSM `DrowsinessDetector`
**Observación Fuerte:** Se asume un framerate perfecto de `30 FPS` en la línea:
`private val requiredFramesForSleep = (fps * 1.5).toInt()`
Si el celular sufre calentamiento y los FPS bajan a 15, el sistema tardará 3 segundos (45 frames a 15fps) en disparar la alarma, no 1.5s.
**Acción Requerida:** La FSM no debe basarse en un contador de *Frames*, sino en el `System.currentTimeMillis()`.
*Corrección Recomendada (Pseudocódigo):*
```kotlin
if (currentEar < threshold) {
   if (eyesClosedStartTime == 0L) eyesClosedStartTime = System.currentTimeMillis()
   if ((System.currentTimeMillis() - eyesClosedStartTime) > 1500L) {
       triggerAlarm()
   }
} else {
   eyesClosedStartTime = 0L
}
```

### Análisis del Backend en Python (FastAPI)
**Observación:** Se utiliza `INSERT ... ON CONFLICT (event_uuid) DO NOTHING`. Esto es una excelente práctica para sistemas "Store-and-Forward" en los que los reintentos HTTP por mala conexión podrían duplicar infracciones.
**Aprobación:** Aprobado.

## 3. Revisión de Seguridad y Permisos
*   Apple App Store es notoriamente estricto al solicitar el permiso de uso de micrófono y cámara en background o pantalla apagada.
*   **Revisión Final:** El equipo debe preparar un video explicativo de 2 minutos para los revisores de Apple, demostrando que el uso de PIP y "Cámara Activa" es estrictamente por seguridad vital y no una herramienta de espionaje publicitaria.

## 4. Conclusión Final del Review
El sistema está **Aprobado para Desarrollo (Go-Ahead)** sujeto a la corrección del "Contador de tiempo basado en ms en lugar de Frames". La suite de documentos es hiper-robusta y provee una hoja de ruta clara para construir un producto B2B de primer nivel en la industria de la movilidad.
### Análisis de la Arquitectura de Reportes y "Clearance API" (Fatigue Risk Score)
**Observación:** La idea de generar un PDF al día al Gerente es vital para RRHH y Seguros. Además, el FRS (Puntaje de 0-100) es lo que distingue esto de una "Cámara Dashcam Normal" a una Verdadera IA de Logística.
*   **Decaimiento por Descanso (Recovery Decay):** El algoritmo actual de Python resta `20 puntos por hora` sin eventos. Sin embargo, hay un bug conceptual: Si la App está apagada (Porque el chofer terminó su turno el viernes), el sistema asumirá un descanso pasivo y bajará los puntos. Esto ES CORRECTO. Pero, ¿y si apagó la App y condujo otro camión sin el DMS?
*   **Acción Requerida para QA y Operaciones:** El sistema "Store-and-Forward" de sincronización es el que sube los puntos negativos al chofer, por lo que el FRS del servidor solo se entera cuando recupera cobertura 4G. En zonas sin señal (offline prolongado), el FRS en el móvil podría seguir subiendo, por lo que la App también debe tener una copia en memoria del "Fatigue Score" y auto-bloquearse nativamente sin esperar permiso de la red. ¡La penalización debe ser Edge + Cloud, no solo Cloud!
