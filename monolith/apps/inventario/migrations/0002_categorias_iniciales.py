from django.db import migrations

CATEGORIAS = [
    ("Construcción", "Taladros, mezcladoras, andamios y equipo de obra"),
    ("Jardinería", "Guadañas, podadoras, motosierras y sopladoras"),
    ("Electricidad", "Multímetros, pulidoras, soldadores y extensiones"),
    ("Carpintería", "Sierras, lijadoras, rúters y cepillos"),
    ("Limpieza", "Hidrolavadoras, aspiradoras industriales y lavadoras de alfombra"),
]


def crear(apps, _schema_editor):
    Categoria = apps.get_model("inventario", "Categoria")
    for nombre, descripcion in CATEGORIAS:
        Categoria.objects.get_or_create(nombre=nombre, defaults={"descripcion": descripcion})


def borrar(apps, _schema_editor):
    apps.get_model("inventario", "Categoria").objects.filter(nombre__in=[c[0] for c in CATEGORIAS]).delete()


class Migration(migrations.Migration):
    dependencies = [("inventario", "0001_initial")]
    operations = [migrations.RunPython(crear, borrar)]
