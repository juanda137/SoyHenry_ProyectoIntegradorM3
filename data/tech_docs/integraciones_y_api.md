# Integraciones y API pública — NubeGestor

Este documento del equipo de Tech explica cómo funcionan la API pública de NubeGestor y las integraciones con otras herramientas. Lo usan los equipos internos de soporte y de implementación para resolver consultas técnicas de clientes, y también las personas que desarrollan integraciones internas.

## Qué es la API pública

La API pública permite que los clientes conecten NubeGestor con sus propios sistemas: crear proyectos y tareas, consultar avances, sincronizar usuarios y descargar reportes de forma automática. Es una API REST que responde en formato JSON y está documentada en developers.nubegestor.example.

La API está disponible en los planes Pro y Empresa. El plan Básico no incluye acceso a la API.

## Límites de solicitudes

Para proteger la plataforma, la API tiene límites de solicitudes por minuto según el plan: 100 solicitudes por minuto en plan Pro y 1.000 en plan Empresa. El límite se cuenta por cuenta de cliente, no por usuario.

Cuando un cliente supera el límite, la API responde con el código HTTP 429 y el encabezado Retry-After, que indica cuántos segundos esperar antes de reintentar. Se recomienda a los clientes reintentar con espera exponencial y agrupar operaciones cuando sea posible.

Los clientes del plan Empresa pueden pedir un aumento temporal del límite para migraciones de datos. La solicitud se hace por el equipo de soporte y la aprueba Tech, por un máximo de 7 días.

## Tokens de acceso

Los tokens se generan en Configuración > API dentro de la cuenta del cliente. Solo los usuarios con rol de administrador pueden crear tokens.

Al generar un token se elige:

- Un nombre descriptivo, por ejemplo "Integración con ERP".
- Los permisos: solo lectura, o lectura y escritura.
- La fecha de vencimiento: 30, 90 o 365 días.

El token se muestra una sola vez al crearlo. Si se pierde, hay que revocarlo y generar uno nuevo. Los tokens se revocan en la misma pantalla, Configuración > API, y la revocación es inmediata.

Nunca se debe compartir un token por correo o chat. Si un token se expone por error, el cliente debe revocarlo de inmediato y el equipo de soporte debe reportarlo a Tech como incidente de seguridad.

## Webhooks

Los webhooks permiten que NubeGestor avise a otro sistema cuando ocurre un evento, por ejemplo cuando se crea una tarea o cuando se cierra un proyecto. Se configuran en Configuración > Webhooks indicando la URL de destino y los eventos de interés.

NubeGestor reintenta el envío de un webhook hasta 5 veces durante 24 horas si el sistema de destino no responde con un código 2xx. Después del quinto intento fallido el webhook se desactiva y el administrador recibe un correo de aviso.

## Integraciones nativas

NubeGestor ofrece integraciones nativas, que no requieren programar, con las herramientas más usadas por las pymes:

- Calendarios de Google y de Microsoft, para sincronizar fechas de entrega.
- Herramientas de chat corporativo, para recibir notificaciones de tareas.
- Almacenamiento en la nube, para adjuntar archivos a las tareas.
- Software contable, para exportar horas facturables.

Las integraciones nativas se activan en Configuración > Integraciones y requieren permisos de administrador. Están disponibles en todos los planes, salvo la integración con software contable, que es exclusiva del plan Empresa.

## Inicio de sesión único para clientes

Los clientes del plan Empresa pueden conectar su propio proveedor de identidad para que sus usuarios entren a NubeGestor con SSO. La configuración la hace el administrador del cliente en Configuración > Seguridad > SSO, con el acompañamiento del equipo de implementación. Este SSO de clientes es distinto del SSO interno que usan los empleados de NubeGestor.

## Versionado de la API

La versión actual de la API es la v2. Las versiones anteriores se mantienen durante 12 meses después del lanzamiento de una nueva versión. Los cambios que pueden romper integraciones se anuncian con 6 meses de anticipación en developers.nubegestor.example y por correo a los administradores.

## Entorno de pruebas

Los clientes del plan Empresa tienen un entorno de pruebas separado, en sandbox.nubegestor.example, con los mismos límites de solicitudes que su plan. Los datos del entorno de pruebas se borran cada 30 días.

## Soporte técnico de integraciones

Las consultas técnicas sobre la API las atiende primero el equipo de soporte. Si el problema parece un error de la plataforma, soporte abre un incidente con la severidad correspondiente según el documento de incidentes y escalamiento.

Para diagnosticar un problema de API conviene pedir al cliente el identificador de la solicitud, que aparece en el encabezado X-Request-Id de cada respuesta.

## Preguntas frecuentes sobre la API

**¿Cuál es el límite de la API en el plan Pro?** 100 solicitudes por minuto por cuenta.

**¿Dónde genero un token de API?** En Configuración > API, con un usuario administrador.

**La API me responde 429, ¿qué significa?** Que se superó el límite de solicitudes; hay que esperar los segundos que indica Retry-After.

**¿El plan Básico tiene API?** No. La API está disponible en los planes Pro y Empresa. Las preguntas sobre precios de los planes las responde Finance.
