# Respaldos de información y política de contraseñas — NubeGestor

Este documento del equipo de Tech describe cómo se respalda la información de NubeGestor y de sus clientes, cómo se recuperan archivos y datos, y cuáles son las reglas para crear y cambiar contraseñas. Cumplir estas reglas es obligatorio para todas las personas con una cuenta corporativa.

## Respaldos de la plataforma

La plataforma NubeGestor, que usan los clientes, tiene respaldos diarios con retención de 30 días. Cada respaldo es una copia completa de la base de datos y de los archivos adjuntos de los clientes, cifrada y guardada en una región distinta de la del servidor principal.

Además, la base de datos guarda un registro continuo de cambios que permite recuperar el estado de los datos en cualquier minuto de los últimos 7 días.

Los respaldos se prueban una vez por mes: Tech restaura un respaldo completo en un entorno aislado y verifica que los datos estén íntegros. El resultado de cada prueba se registra en Mi NubeGestor > Tech > Continuidad.

## Recuperación de datos de clientes

Si un cliente borra por error un proyecto o una tarea, puede recuperarlo desde la papelera durante 30 días. Pasado ese plazo, el administrador del cliente puede pedir una restauración desde un respaldo al equipo de soporte. La restauración la ejecuta Tech en un plazo de 2 días hábiles y solo es posible dentro de los 30 días de retención de los respaldos.

Las restauraciones parciales, de un solo proyecto, no tienen costo en el plan Empresa. En los planes Básico y Pro se ofrece una restauración gratuita por año.

## Respaldos de las laptops

Los archivos de trabajo deben guardarse en el almacenamiento en la nube corporativo, que se sincroniza automáticamente. Lo que se guarda solo en el disco de la laptop no tiene respaldo. Si la laptop se pierde o se rompe, los archivos locales no se pueden recuperar.

Los archivos borrados del almacenamiento en la nube corporativo se pueden recuperar desde la papelera durante 90 días.

## Política de contraseñas

Las contraseñas de las cuentas corporativas deben tener mínimo 12 caracteres, se cambian cada 180 días y no se pueden reutilizar las últimas 5.

Recomendaciones para crear una buena contraseña:

- Usar una frase larga y fácil de recordar, por ejemplo cuatro palabras sin relación entre sí.
- Combinar letras mayúsculas, minúsculas, números y símbolos.
- No usar datos personales, como nombres, fechas de nacimiento o el nombre de la empresa.
- No usar la misma contraseña en servicios personales y corporativos.

El sistema avisa por correo 14 días antes de que venza la contraseña. El cambio se hace en Mi NubeGestor > Seguridad > Cambiar contraseña o en el portal de autoservicio acceso.nubegestor.example.

## Gestor de contraseñas

NubeGestor ofrece a todas las personas un gestor de contraseñas corporativo, preinstalado en la laptop. Es la forma recomendada de guardar contraseñas de herramientas que no están conectadas al SSO. Las contraseñas compartidas por un equipo, por ejemplo de una cuenta de proveedor, se guardan en bóvedas compartidas dentro del gestor y nunca en documentos o en el chat.

## Qué hacer si se sospecha que una contraseña fue expuesta

Si una persona cree que alguien conoce su contraseña, por ejemplo porque la escribió en un sitio falso, debe:

1. Cambiar la contraseña de inmediato en el portal de autoservicio.
2. Llamar a la extensión 4000 para reportarlo como incidente de seguridad.
3. Revisar con Tech las sesiones abiertas y cerrar las que no reconozca.

## Bloqueo automático de pantalla

Las laptops se bloquean automáticamente después de 5 minutos sin uso. Para desbloquearlas se usa la contraseña o la huella digital. Se recomienda bloquear la pantalla manualmente cada vez que la persona se aleja del equipo.

## Retención de correos y documentos

Los correos corporativos se conservan durante 5 años. Los documentos de proyectos internos se conservan mientras el proyecto esté activo y 2 años después de su cierre. Estas reglas pueden ampliarse cuando la ley lo exige, por ejemplo para documentos contables, que administra Finance.

## Preguntas frecuentes sobre respaldos y contraseñas

**¿Cada cuánto se respalda la plataforma?** Todos los días, y cada respaldo se guarda durante 30 días.

**¿Cuántos caracteres debe tener mi contraseña?** Mínimo 12.

**¿Puedo volver a usar una contraseña anterior?** No se pueden reutilizar las últimas 5.

**Borré un archivo de la nube corporativa, ¿se puede recuperar?** Sí, desde la papelera durante 90 días.
