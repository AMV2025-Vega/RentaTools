"""
Gestión del catálogo de traducciones (sin depender de xgettext/msgfmt).

  python scripts/i18n.py        → extrae los msgid (es) de plantillas y código, exige que TODOS
                                  tengan traducción al inglés y escribe locale/en/LC_MESSAGES/django.{po,mo}.
Falla (exit 1) si falta alguna traducción: así nunca queda un texto sin traducir.
"""
import re, sys
from pathlib import Path
import polib

BASE = Path(__file__).resolve().parent.parent
EN = {
 # --- plantillas / JS ---
 "Acciones": "Actions", "Activa": "Active", "Activar": "Activate",
 "Alquila la herramienta que necesitas, sin comprarla": "Rent the tool you need, without buying it",
 "Alquiler": "Rental", "Aún no has publicado herramientas.": "You haven't listed any tools yet.",
 "Aún no tienes reservas.": "You have no bookings yet.", "Buscar": "Search",
 "Calculando cotización…": "Calculating quote…", "Cancelada": "Cancelled", "Cancelar": "Cancel",
 "Cargando…": "Loading…", "Categoría": "Category", "Catálogo": "Catalog", "Cobertura máxima": "Maximum coverage",
 "Confirmada": "Confirmed", "Contraseña": "Password", "Correo electrónico": "Email", "Creando cuenta…": "Creating account…",
 "Crear cuenta": "Create account", "Descargar reporte (CSV)": "Download report (CSV)", "Descripción": "Description",
 "Desde": "From", "Detalle de herramienta": "Tool details", "Días": "Days", "día": "day", "días": "days",
 "El día de inicio y el de fin cuentan como días de alquiler.": "Both the start and end days count as rental days.",
 "El reporte está tardando; intenta de nuevo en un momento.": "The report is taking longer than expected; please try again shortly.",
 "El servicio de seguros no está disponible ahora; el total no incluye seguro.": "The insurance service is unavailable right now; the total does not include insurance.",
 "Elige las fechas de inicio y fin.": "Choose the start and end dates.", "En mantenimiento": "Under maintenance",
 "Encuentra equipos de otros usuarios, consulta su disponibilidad por fechas y reserva en minutos.": "Find equipment from other users, check its availability by date and book in minutes.",
 "Equivale a": "Equivalent to", "Esta herramienta no tiene reservas próximas.": "This tool has no upcoming bookings.",
 "Estado": "Status", "Fechas": "Dates", "Fechas ocupadas": "Booked dates", "Finalizada": "Completed",
 "Generando tu reporte…": "Generating your report…", "Hasta": "To", "Herramienta": "Tool", "Herramienta publicada.": "Tool listed.",
 "Ingresando…": "Signing in…", "Ingresar": "Sign in", "Mis herramientas": "My tools", "Mis reservas": "My bookings",
 "Mínimo 8 caracteres, no solo números.": "At least 8 characters, not only numbers.",
 "Necesitas iniciar sesión para reservar.": "You need to sign in to book.",
 "No hay herramientas que coincidan con tu búsqueda.": "No tools match your search.",
 "No se pudo conectar con el servidor. Intenta de nuevo.": "Could not reach the server. Please try again.",
 "No se pudo generar el reporte.": "The report could not be generated.",
 "No se pudo obtener la tasa de cambio; no se muestra el valor en USD.": "The exchange rate is unavailable; the USD value is not shown.",
 "Nombre": "Name", "Ocurrió un error inesperado.": "An unexpected error occurred.", "Pendiente de pago": "Payment pending",
 "Poner en mantenimiento": "Set to maintenance", "Precio por día (COP)": "Price per day (COP)",
 "Proyecto de Arquitectura de Software 2026 · Alquiler de herramientas entre particulares": "Software Architecture 2026 project · Peer-to-peer tool rental",
 "Publicando…": "Publishing…", "Publicar": "Publish", "Publicar herramienta": "List a tool",
 "Reporte listo: se está descargando.": "Report ready: downloading.", "Reserva cancelada.": "Booking cancelled.",
 "Reserva y cotización": "Booking and quote", "Reservando…": "Booking…", "Reservar": "Book", "Salir": "Sign out",
 "Saltar al contenido": "Skip to content", "Seguro opcional": "Optional insurance", "Sin foto": "No photo",
 "Tasa: 1 USD = {cop} COP (actualizada {fecha})": "Rate: 1 USD = {cop} COP (updated {fecha})",
 "Teléfono (opcional)": "Phone (optional)", "Todas las categorías": "All categories", "Total": "Total",
 "URL de la foto (opcional)": "Photo URL (optional)", "Usuario": "Username", "Ver": "View", "Volver al catálogo": "Back to catalog",
 "{h} herramientas activas · {r} reservas registradas": "{h} active tools · {r} bookings made",
 "¡Reserva creada! Te llevamos a tus reservas.": "Booking created! Taking you to your bookings.",
 "¿Cancelar esta reserva?": "Cancel this booking?", "¿No tienes cuenta?": "Don't have an account?", "¿Ya tienes cuenta?": "Already have an account?",
 "Filtrar herramientas": "Filter tools", "Taladro, guadaña…": "Drill, lawn mower…", "Inicio": "Home",
 "Navegación principal": "Main navigation", "Idioma": "Language",
 # --- errores de la API ---
 "La herramienta no existe.": "The tool does not exist.", "La reserva no existe.": "The booking does not exist.",
 "La categoría no existe.": "The category does not exist.", "Usuario y correo son obligatorios.": "Username and email are required.",
 "El nombre de la herramienta es obligatorio.": "The tool name is required.",
 "El precio por día debe ser mayor que cero.": "The price per day must be greater than zero.",
 "El estado indicado no es válido.": "The given status is not valid.", "El cliente es obligatorio.": "The customer is required.",
 "La herramienta es obligatoria.": "The tool is required.",
 "La herramienta no está disponible para alquiler.": "The tool is not available for rental.",
 "No puedes reservar tu propia herramienta.": "You cannot book your own tool.",
 "Las fechas de inicio y fin son obligatorias.": "Start and end dates are required.",
 "La fecha de fin no puede ser anterior a la de inicio.": "The end date cannot be before the start date.",
 "La fecha de inicio no puede estar en el pasado.": "The start date cannot be in the past.",
 "La reserva excede el máximo de días permitido.": "The booking exceeds the maximum number of days allowed.",
 "Faltan datos para construir la reserva.": "Some data needed to build the booking is missing.",
 "El nombre de usuario ya está en uso.": "That username is already taken.", "El correo ya está registrado.": "That email is already registered.",
 "La herramienta ya está reservada en alguna de esas fechas.": "The tool is already booked on some of those dates.",
 "No se puede cancelar una reserva que ya no está vigente.": "A booking that is no longer active cannot be cancelled.",
 "La operación no es válida para el estado actual de la reserva.": "The operation is not valid for the booking's current status.",
 "Solo el propietario puede cambiar el estado de la herramienta.": "Only the owner can change the tool's status.",
 "Solo quien hizo la reserva puede cancelarla.": "Only the person who made the booking can cancel it.",
 "Ese reporte pertenece a otro usuario.": "That report belongs to another user.",
 "El servicio de reportes no está disponible en este momento.": "The reports service is unavailable at the moment.",
 "El servicio no está disponible en este momento.": "The service is unavailable at the moment.",
 "Usuario o contraseña incorrectos.": "Incorrect username or password.",
 # --- notificaciones ---
 "Reserva registrada": "Booking registered",
 "Hola %(nombre)s, tu reserva #%(id)s de '%(herramienta)s' (%(inicio)s a %(fin)s) quedó pendiente de pago por %(total)s %(moneda)s.":
   "Hi %(nombre)s, your booking #%(id)s for '%(herramienta)s' (%(inicio)s to %(fin)s) is pending payment: %(total)s %(moneda)s.",
 "Reserva cancelada": "Booking cancelled",
 "Hola %(nombre)s, tu reserva #%(id)s fue cancelada.": "Hi %(nombre)s, your booking #%(id)s was cancelled.",
}

def extraer() -> set[str]:
    ids = set()
    for f in (BASE / "apps").rglob("*.html"):
        for m in re.finditer(r"\{%\s*(?:trans|translate)\s+(\"([^\"]*)\"|'([^']*)')", f.read_text(encoding="utf-8")):
            ids.add(m.group(2) if m.group(2) is not None else m.group(3))
    call = re.compile(r"""\b(?:gettext_lazy|gettext_noop|gettext|_)\(\s*((?:"(?:[^"\\]|\\.)*"\s*)+)\)""")
    for f in (BASE / "apps").rglob("*.py"):
        if "tests" in f.parts: continue
        for m in call.finditer(f.read_text(encoding="utf-8")):
            ids.add("".join(re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))))
    return ids

def main() -> int:
    ids = extraer()
    faltan = sorted(i for i in ids if i not in EN)
    sobran = sorted(i for i in EN if i not in ids)
    if faltan:
        print("SIN TRADUCCIÓN:", *faltan, sep="\n  "); return 1
    if sobran:
        print("Aviso: traducciones sin uso:", *sobran, sep="\n  ")
    po = polib.POFile()
    po.metadata = {"Project-Id-Version": "RentaTools", "Language": "en", "MIME-Version": "1.0",
                   "Content-Type": "text/plain; charset=UTF-8", "Content-Transfer-Encoding": "8bit"}
    for i in sorted(ids):
        po.append(polib.POEntry(msgid=i, msgstr=EN[i], flags=["python-brace-format"] if "{" in i and "%(" not in i else (["python-format"] if "%(" in i else [])))
    out = BASE / "locale" / "en" / "LC_MESSAGES"; out.mkdir(parents=True, exist_ok=True)
    po.save(str(out / "django.po")); po.save_as_mofile(str(out / "django.mo"))
    print(f"OK: {len(ids)} textos traducidos → {out}"); return 0

if __name__ == "__main__":
    sys.exit(main())
