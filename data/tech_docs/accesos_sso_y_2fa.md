# Accesos, inicio de sesión único (SSO) y autenticación en dos pasos — NubeGestor

Este documento del equipo de Tech (Soporte de TI) explica cómo se accede a los sistemas internos de NubeGestor, qué hacer cuando una cuenta se bloquea y cómo configurar la autenticación en dos pasos. La mesa de ayuda de TI atiende en la extensión 4000 y en soporte-ti@nubegestor.example, de lunes a viernes de 8:00 a 19:00.

## Cuenta corporativa

Cada persona tiene una única cuenta corporativa con el formato nombre.apellido@nubegestor.example. Con esa cuenta se accede al correo, al chat interno, a Mi NubeGestor, al repositorio de código y al resto de las herramientas de trabajo.

La cuenta la crea Tech cuando HR avisa de un nuevo ingreso. Las credenciales iniciales se entregan junto con la laptop el primer día de trabajo y la contraseña temporal debe cambiarse en el primer inicio de sesión.

## Inicio de sesión único (SSO)

NubeGestor usa inicio de sesión único (SSO). Esto significa que la persona inicia sesión una vez con su cuenta corporativa y luego entra a todas las aplicaciones conectadas sin volver a escribir la contraseña.

Las aplicaciones conectadas al SSO aparecen en el panel acceso.nubegestor.example. Si una aplicación no aparece en el panel, la persona no tiene permiso para usarla. Los permisos adicionales se piden en Mi NubeGestor > Solicitudes > Acceso a aplicación, con la aprobación del responsable directo. Tech los configura en un plazo de 1 día hábil desde la aprobación.

La sesión de SSO dura 12 horas. Pasado ese tiempo se pide iniciar sesión de nuevo, con contraseña y segundo factor.

## Bloqueo de cuenta

La cuenta corporativa se bloquea tras 5 intentos fallidos de inicio de sesión. El bloqueo protege la cuenta contra intentos de adivinar la contraseña.

El desbloqueo se hace en el portal de autoservicio acceso.nubegestor.example o llamando a la extensión 4000. En el portal de autoservicio:

1. Elegir la opción "No puedo entrar a mi cuenta".
2. Escribir el correo corporativo.
3. Confirmar la identidad con el segundo factor (la app autenticadora) o con el código que se envía al teléfono personal registrado.
4. Definir una contraseña nueva que cumpla la política de contraseñas.

Si la persona no tiene acceso al segundo factor, por ejemplo porque cambió de teléfono, debe llamar a la extensión 4000. La mesa de ayuda verifica la identidad con una videollamada y preguntas de seguridad antes de desbloquear la cuenta.

Una cuenta que se bloquea más de 3 veces en una semana se revisa como posible incidente de seguridad.

## Autenticación en dos pasos (2FA)

La 2FA es obligatoria con app autenticadora (Google Authenticator o Microsoft Authenticator) para todas las cuentas corporativas. No se aceptan códigos por SMS como método principal porque son menos seguros.

La 2FA se configura en Mi NubeGestor > Seguridad > Autenticación en dos pasos. Los pasos son:

1. Instalar Google Authenticator o Microsoft Authenticator en el teléfono.
2. Ingresar a Mi NubeGestor > Seguridad > Autenticación en dos pasos y elegir "Configurar app autenticadora".
3. Escanear con la app el código QR que muestra la pantalla.
4. Escribir el código de 6 dígitos que genera la app para confirmar.
5. Guardar en un lugar seguro los 10 códigos de recuperación que muestra el sistema. Cada código sirve una sola vez.

La configuración de la 2FA es parte del primer día de trabajo y se hace junto con Tech al recibir la laptop.

## Cambio de teléfono

Antes de cambiar de teléfono hay que mover la app autenticadora al nuevo equipo. Desde Mi NubeGestor > Seguridad se puede registrar un segundo dispositivo antes de eliminar el anterior. Si el teléfono se perdió o se rompió, se usa un código de recuperación para entrar y registrar el nuevo teléfono. Si tampoco hay códigos de recuperación, se llama a la extensión 4000.

## Accesos de personas externas

Los contratistas y proveedores que necesitan acceso a sistemas internos reciben una cuenta de invitado con fecha de vencimiento. La solicita el responsable del proyecto en Mi NubeGestor > Solicitudes > Acceso externo. Las cuentas de invitado vencen como máximo a los 90 días y se pueden renovar.

## Revisión periódica de accesos

Cada trimestre Tech envía a los responsables la lista de permisos de su equipo para que confirmen cuáles siguen siendo necesarios. Los permisos que no se confirman en 10 días hábiles se retiran.

## Preguntas frecuentes sobre accesos

**No puedo entrar, ¿qué hago?** Si la cuenta está bloqueada por intentos fallidos, usar el portal de autoservicio acceso.nubegestor.example o llamar a la extensión 4000.

**¿Puedo usar SMS como segundo factor?** Solo como método de respaldo temporal. El método principal debe ser una app autenticadora.

**Necesito acceso a una herramienta nueva, ¿a quién se lo pido?** Se solicita en Mi NubeGestor > Solicitudes > Acceso a aplicación, con aprobación del responsable, y Tech lo configura.

**¿Puedo compartir mi cuenta con un compañero?** No. Las cuentas son personales e intransferibles.
