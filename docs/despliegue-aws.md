# Despliegue en AWS EC2 (Amazon Linux 2023)

Objetivo: una instancia EC2 que ejecuta todo con Docker Compose; **solo el puerto 80 es público**.

## 1. Crear la instancia
1. EC2 → *Launch instance* → AMI **Amazon Linux 2023**, tipo **t3.small** (2 GB; una t3.micro también sirve con el swap del script).
2. Par de llaves: crea/descarga un `.pem`.
3. Almacenamiento: 20 GB gp3.
4. **Security Group** (`sg-rentatools`), reglas de entrada:

| Tipo | Puerto | Origen | Motivo |
|---|---|---|---|
| HTTP | 80 | 0.0.0.0/0 | Único punto de entrada (Nginx) |
| SSH | 22 | **Mi IP** (/32) | Administración, nunca abierto al mundo |

   No agregues 5432, 6379, 5000 ni 5001: PostgreSQL, Redis, costo y aliado solo existen dentro de las redes Docker.
5. *Elastic IP*: asígnala a la instancia para que la dirección no cambie al reiniciar.

## 2. Preparar el servidor (una vez)
```bash
ssh -i llave.pem ec2-user@<IP-ELASTICA>
git clone https://github.com/<usuario>/<repo>.git RentaTools && cd RentaTools
bash scripts/aws/bootstrap-ec2.sh
exit                      # volver a entrar para aplicar el grupo docker
```

## 3. Configurar y desplegar
```bash
ssh -i llave.pem ec2-user@<IP-ELASTICA>
cd RentaTools
cp .env.example .env && nano .env
```
Cambia en `.env`:
* `POSTGRES_PASSWORD`, `DJANGO_SECRET_KEY` (`python3 -c "import secrets;print(secrets.token_urlsafe(50))"`), `ALIADO_API_KEY`.
* `DJANGO_ALLOWED_HOSTS=<IP-ELASTICA>,localhost,127.0.0.1,django`
* `DJANGO_CSRF_TRUSTED_ORIGINS=http://<IP-ELASTICA>`
* `ENV_TYPE=production` solo si configuraste SMTP; si no, déjalo en `development` (las notificaciones salen en el log del worker).

```bash
bash scripts/aws/deploy.sh
```
El script construye las imágenes Alpine, levanta los 7 servicios, espera al healthcheck y corre la prueba de humo.

## 4. Verificar desde tu computador
```powershell
# Navegador:  http://<IP-ELASTICA>/
bash scripts/aws/smoke-test.sh http://<IP-ELASTICA>     # (Git Bash/WSL)
```
Comprobaciones manuales útiles: `docker compose ps` (todo *healthy*), `docker compose logs -f worker` (notificaciones asíncronas),
y desde fuera `nmap -p 22,80,5000,5001,5432,6379 <IP>` → solo 80 abierto.

## 5. Actualizar después de un push
```bash
cd RentaTools && bash scripts/aws/deploy.sh
```

## Problemas frecuentes
| Síntoma | Causa / solución |
|---|---|
| `Bad Request (400)` en el navegador | Falta la IP en `DJANGO_ALLOWED_HOSTS` |
| 403 CSRF al ingresar | `DJANGO_CSRF_TRUSTED_ORIGINS` debe ser `http://<IP>` (con esquema) |
| No abre el sitio | Security Group sin regla 80, o instancia sin IP pública |
| `permission denied` de docker | Cierra y reabre la sesión SSH tras el bootstrap |
| Build se queda sin memoria | Verifica el swap (`swapon --show`) o usa t3.small |
| USD no aparece | Sin salida a `open.er-api.com`: el sistema degrada y avisa (diseño resiliente) |
