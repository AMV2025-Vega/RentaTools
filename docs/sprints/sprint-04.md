# Sprint 4 — Frontend e internacionalización (ES/EN)

## Qué se entrega
- **App `web`** (plantillas Django + JS vanilla, sin CDN): catálogo con filtros, detalle con cotización en vivo,
  mis reservas (cancelar, reporte CSV asíncrono), publicar herramienta, ingreso y registro.
- El frontend **solo consume la API REST** (`/api/...`); no toca la base de datos ni el dominio → listo para el Strangler.
- **i18n con gettext**: msgid en español, catálogo `locale/en/LC_MESSAGES/django.po/.mo`.
  Cubre plantillas, textos de JS (inyectados por el servidor en `window.I18N`), mensajes de error de la API
  (por `codigo`) y plantillas de notificación (idioma del usuario). Cero textos quemados.
- Selector ES/EN (`/i18n/setlang/`, cookie) y fechas/moneda con `Intl` según idioma.
- **UX/Usabilidad**: enlace "saltar al contenido", etiquetas en todos los campos, `aria-live` en mensajes,
  foco visible, objetivos táctiles ≥44px, responsive (probado a 390px), estados de carga/vacío/error,
  botones bloqueados mientras se envía, avisos claros cuando el aliado o la API de tasas fallan.
- **Seguridad frontend**: el DOM se construye con `textContent` (la descripción `<b>` se ve como texto), CSRF en
  toda petición mutante, `next` solo admite rutas internas.

## Cómo mantener las traducciones
`python scripts/i18n.py` (requiere `pip install polib`): extrae todos los textos, **falla si falta una traducción**
y regenera `django.po/.mo`. Para añadir un idioma, agregar su diccionario en el script.

## Verificación
- 81 pruebas del monolito (11 nuevas: páginas, login_required, cambio de idioma, errores y notificaciones en inglés,
  catálogo completo).
- Prueba real en Chromium (Playwright): registro → publicar → cotizar (alquiler + seguro del aliado) → reservar →
  reporte CSV vía Celery → doble reserva rechazada con 409 traducido ES/EN → vista móvil. Sin errores de JS.
- Bug encontrado y corregido en la prueba: el botón quedaba en "Publicando…" (helper `busy`) y los listeners
  del formulario de detalle se registraban tras una petición de red.

## Limitaciones conocidas
- Los nombres de categorías vienen de la base de datos y no se traducen (son datos, no interfaz).
- La conversión a USD no se pudo probar en el sandbox (sin salida a open.er-api.com); en AWS se verá la tasa real.
