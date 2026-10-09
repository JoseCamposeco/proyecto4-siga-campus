# Manual de usuario

## Inicio y carátula

Abrir `SIGA-Campus.exe`. La carátula contiene los cuatro integrantes, la carrera,
el curso y el docente proporcionados. **Editar carátula** permite completar la
universidad y equipo. En **Integrantes y carnés**, escribir una persona por línea
y añadir su carné en la misma línea. **Entrar al sistema** abre el resumen.

## Primer registro

1. En **Profesores**, pulsar **Registrar profesor**. Completar código, nombre,
   correo válido y especialidad. El código debe ser único.
2. En **Estudiantes**, registrar carné, nombre, correo y carrera. El carné es único.
3. En **Cursos**, registrar código, nombre, ciclo, profesor, créditos y cupo.
   El profesor se selecciona entre los ya registrados.
4. Seleccionar un curso y usar **Editar** para cambiar sus datos o profesor.

Las búsquedas filtran por los datos de cada directorio. Doble clic permite editar
personas o consultar inscritos de un curso. Los datos extensos de las tablas
pueden consultarse con sus tooltips y barras de desplazamiento.

## Evaluaciones

Cada curso inicia con cuatro evaluaciones: 20 %, 20 %, 20 % y 40 %.
En **Cursos**, seleccionar el curso y pulsar **Evaluaciones**. Se pueden cambiar
los nombres y porcentajes, agregar o quitar evaluaciones. Hay un máximo de 12.
La suma debe ser exactamente 100 %. Después de guardar notas, el plan queda
protegido para conservar el significado de las calificaciones existentes.

## Inscripciones

En **Inscripciones**, elegir el curso y estudiante y pulsar **Inscribir estudiante**.
Se muestra el profesor, cupo, inscritos y resultados. El sistema rechaza una
segunda inscripción del mismo estudiante al mismo curso y ciclo, los cursos
cerrados y los cursos que alcanzaron su cupo.

Un estudiante puede tener varios cursos. Un curso puede ofrecerse en distintos
ciclos, conservando su código y su historial por separado.

## Registrar y modificar notas

En **Calificaciones**, seleccionar un curso. Hacer doble clic en una celda de
evaluación o seleccionar la celda y empezar a escribir. Introducir notas de 0 a
100 con máximo dos decimales. **Guardar notas** valida todo el conjunto antes
de escribirlo: si una nota es inválida, no se guarda ninguna de ese lote.

Para corregir una nota, editar la celda y guardar otra vez. El resultado se
recalcula automáticamente y el cambio queda registrado. Una celda vacía significa
nota pendiente; una celda con `0` significa nota registrada de cero puntos.
Al cambiar de curso, salir del módulo o cerrar la ventana con cambios pendientes,
se ofrece guardar, descartar o cancelar.

La nota mostrada es el acumulado ponderado. Cuando faltan evaluaciones, el
resultado es PENDIENTE. Con todas las evaluaciones registradas, una nota final
de al menos 70 determina APROBADO; una menor determina REPROBADO. El criterio
puede ajustarse en Configuración y todos los resultados se recalculan.

## Historial y reportes

En **Estudiantes**, seleccionar una persona y pulsar **Historial académico**,
o usar directamente el módulo **Historial académico**. Muestra todos los cursos
por ciclo, profesor, créditos, notas y estado, además de los créditos ganados.
El promedio general usa solo cursos completos y pondera por créditos.

**Exportar** genera un CSV compatible con Excel. Las cadenas que podrían
interpretarse como fórmulas se protegen antes de exportar.

## Cierre y respaldos

En **Cursos**, **Cerrar** exige alumnos inscritos y todas las notas completas.
Después del cierre no se permiten nuevas inscripciones ni cambios al plan o
datos del curso. Se pueden corregir notas existentes sin dejarlas vacías.

En **Configuración**, **Guardar respaldo** crea una copia completa de SQLite.
La ubicación de la base activa está visible en el mismo módulo. Para abrir un
respaldo como base independiente, copiarlo a una carpeta con el nombre `siga.db`
y ejecutar `SIGA-Campus.exe --data-dir "ruta-de-la-carpeta"`.

## Datos de demostración

**Cargar demostración** solo aparece con la base vacía y requiere confirmación.
Genera 8 estudiantes, 3 profesores, 4 cursos y 27 inscripciones ficticias,
con resultados aprobados, reprobados y pendientes. Para una presentación separada,
usar `--data-dir` con una carpeta nueva. No se mezclan datos demo en una base existente.

## Errores

Los errores esperados aparecen en el formulario o en una notificación y permiten
corregir el dato. Un error inesperado genera `errores.log` en la carpeta de datos.
No hay conexión de red ni envío de los datos académicos a GitHub.
