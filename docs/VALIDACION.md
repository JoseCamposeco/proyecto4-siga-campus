# Validación del proyecto

Fecha de verificación: 8 de octubre de 2026, Guatemala.

## Entorno local

- Windows 11, arquitectura x64.
- Python 3.14.2.
- PySide6 Essentials 6.12.0.
- PyInstaller 6.22.3.
- SQLite incluida con Python.

## Resultado de pruebas

**51 pruebas aprobadas, sin fallos.**

```text
python -m pytest -q
51 passed

python -m ruff check .
All checks passed!
```

| Área | Casos comprobados |
|---|---|
| Personas | Campos vacíos, código inválido, correo inválido, duplicados y edición |
| Cursos | Profesor obligatorio, reasignación, créditos y cupos válidos |
| Inscripciones | Duplicados, cupo, curso cerrado, claves foráneas y protección SQL |
| Evaluaciones | Suma de 100 %, nombres únicos y protección de planes con notas |
| Calificaciones | Límites 0/100, negativos, >100, NaN, infinito y decimales excesivos |
| Lotes | Validación previa y reversión completa ante errores |
| Cálculo | Ponderación, actualización tras modificar y límites de aprobación |
| Redondeo | La aprobación coincide con la nota final mostrada a dos decimales |
| Historial | Múltiples ciclos para un mismo código de curso |
| Cierre | Notas completas, correcciones auditadas y rechazo de notas vacías |
| Persistencia | Reapertura y respaldo íntegro de SQLite |
| Exportación | CSV con codificación UTF-8 y protección contra fórmulas |
| GUI | Carátula, validación y guardado del formulario, ocho módulos y edición de notas |
| Recursos | Presencia de los iconos utilizados por la aplicación |

## Revisión visual

Se capturaron los ocho módulos a 1360 x 860 y 1100 x 700, además de la carátula.
Se revisaron textos, tablas, navegación, controles y estados de aprobación.
La fuente Source Sans 3 se incorpora al programa para mantener el renderizado
consistente. Las tablas conservan tooltips y desplazamiento para datos extensos.

Capturas de referencia con datos ficticios en `capturas/`.

## Ejecutable

La compilación aísla PATH de bibliotecas de otras herramientas para evitar
incompatibilidades de DLL. La autoverificación del binario carga datos ficticios,
instancia las ocho páginas y comprueba el criterio de aprobación y la carátula.
El resultado está guardado en `validacion_ejecutable.json`.

No se requiere Python instalado para utilizar el ejecutable. La validación local
se realizó en Windows 11 x64; no se afirma haber probado cada versión de Windows.
