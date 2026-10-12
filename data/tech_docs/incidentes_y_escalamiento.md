# Gestión de incidentes y escalamiento — NubeGestor

Este documento del equipo de Tech describe cómo se reportan, clasifican y resuelven los incidentes técnicos de NubeGestor, tanto los que afectan a las herramientas internas como los que afectan a la plataforma que usan los clientes. Un incidente es cualquier evento que interrumpe o degrada un servicio, o que pone en riesgo la seguridad de la información.

## Cómo reportar un incidente

Cualquier persona puede reportar un incidente por estos canales:

- Mesa de ayuda: extensión 4000 o soporte-ti@nubegestor.example, para incidentes de herramientas internas, equipos y accesos.
- Canal de chat "incidentes-plataforma", para problemas en el producto que afectan a clientes.
- Teléfono de guardia, publicado en Mi NubeGestor > Tech > Guardia, fuera del horario laboral y solo para incidentes P1 y P2.

Al reportar hay que indicar qué servicio falla, desde cuándo, a cuántas personas o clientes afecta y, si existe, el mensaje de error o una captura de pantalla.

## Niveles de severidad

Cada incidente se clasifica en uno de cuatro niveles de severidad. Los tiempos de respuesta son: P1 respuesta en 15 minutos, P2 en 1 hora, P3 en 4 horas, P4 en 1 día hábil. El tiempo de respuesta es el plazo máximo para que una persona de Tech tome el caso y responda al reporte, no el plazo para resolverlo.

- P1 — Crítico: la plataforma está caída para todos los clientes o hay una filtración de datos en curso. Respuesta en 15 minutos, las 24 horas, los 7 días.
- P2 — Alto: una función principal no funciona para muchos clientes, o un sistema interno crítico, como el correo o el SSO, está caído. Respuesta en 1 hora, las 24 horas.
- P3 — Medio: una función no principal falla o el problema afecta a pocas personas y existe una alternativa. Respuesta en 4 horas, en horario laboral.
- P4 — Bajo: consultas, problemas menores o pedidos que no impiden trabajar. Respuesta en 1 día hábil.

Quien reporta propone una severidad, y la persona de guardia de Tech la confirma o la ajusta.

## Roles durante un incidente

En los incidentes P1 y P2 se asignan tres roles:

- Responsable del incidente: coordina la respuesta, toma decisiones y define cuándo se cierra el incidente.
- Responsable técnico: investiga la causa y aplica la solución.
- Responsable de comunicación: informa a las personas afectadas y, si el incidente afecta a clientes, actualiza la página de estado status.nubegestor.example cada 30 minutos.

En los incidentes P3 y P4 una misma persona de Tech cumple los tres roles.

## Escalamiento

Si un incidente no avanza dentro de los plazos esperados, se escala:

1. Primer nivel: mesa de ayuda o persona de guardia.
2. Segundo nivel: el equipo especialista del servicio afectado, por ejemplo infraestructura, base de datos o seguridad.
3. Tercer nivel: la dirección de Tecnología, que se involucra en todos los P1 desde el inicio y en los P2 que superan las 4 horas sin resolución.

Un incidente que involucra datos personales de clientes se escala siempre al equipo de seguridad, aunque su severidad inicial sea baja.

## Guardias

El equipo de Tech tiene guardias rotativas de una semana. La persona de guardia debe estar disponible fuera del horario laboral para responder incidentes P1 y P2 con su laptop y conexión a internet. Las guardias se compensan con un día libre por semana de guardia, que se registra con HR.

## Cierre y análisis posterior

Un incidente se cierra cuando el servicio funciona normalmente y la persona que reportó lo confirma. Para todos los incidentes P1 y P2 se escribe un análisis posterior, sin buscar culpables, dentro de los 5 días hábiles siguientes. El análisis incluye la línea de tiempo, la causa raíz, el impacto y las acciones para evitar que se repita.

Los análisis posteriores se publican en Mi NubeGestor > Tech > Incidentes y se revisan en la reunión mensual de confiabilidad.

## Incidentes de seguridad

Son incidentes de seguridad, entre otros: correos de phishing que alguien abrió, una laptop perdida o robada, accesos sospechosos a una cuenta y cualquier sospecha de filtración de datos. Estos casos se reportan de inmediato a la extensión 4000, sin intentar resolverlos por cuenta propia. No hay que borrar el correo sospechoso ni apagar el equipo: Tech necesita la evidencia.

## Mantenimientos programados

Los mantenimientos de la plataforma se realizan los domingos entre las 2:00 y las 5:00, hora de Bogotá. Se avisan a los clientes con 72 horas de anticipación en la página de estado. Un mantenimiento programado no se considera incidente salvo que se extienda más allá de la ventana anunciada.

## Preguntas frecuentes sobre incidentes

**La plataforma no carga para ningún cliente, ¿qué severidad es?** P1: respuesta en 15 minutos.

**Mi impresora no funciona, ¿es un incidente?** Sí, de severidad P4, con respuesta en 1 día hábil.

**Abrí un correo sospechoso, ¿qué hago?** Llamar de inmediato a la extensión 4000 y no borrar el correo.

**¿Dónde veo el estado de la plataforma?** En status.nubegestor.example.
