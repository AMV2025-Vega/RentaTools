from django.db import migrations

CREAR = """
CREATE FUNCTION auditoria_bloquear_cambios() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'auditoria_registroauditoria es append-only: UPDATE/DELETE no permitidos';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_auditoria_inmutable
BEFORE UPDATE OR DELETE ON auditoria_registroauditoria
FOR EACH ROW EXECUTE FUNCTION auditoria_bloquear_cambios();
"""

ELIMINAR = """
DROP TRIGGER IF EXISTS trg_auditoria_inmutable ON auditoria_registroauditoria;
DROP FUNCTION IF EXISTS auditoria_bloquear_cambios();
"""


class Migration(migrations.Migration):
    """La bitácora de auditoría es inmutable a nivel de base de datos (no solo en el código)."""

    dependencies = [("auditoria", "0001_initial")]
    operations = [migrations.RunSQL(CREAR, reverse_sql=ELIMINAR)]
