# Gym-LMF

MVP para la gestión de usuarios, consulta de membresías y control de acceso a un gimnasio mediante códigos QR temporales de un solo uso.

Proyecto académico desarrollado de forma individual para integrar arquitectura de microservicios, contenedores, pruebas automatizadas, análisis de seguridad y entrega continua.

## Estado del proyecto

El entorno local cuenta con un flujo CI/CD funcional. Un cambio enviado a `main` inicia Jenkins, ejecuta las verificaciones, construye las imágenes, las carga en Kind y actualiza los manifiestos de `deploy/local`. Argo CD detecta los cambios y sincroniza Kubernetes.

La sincronización automática se verificó con el build 14, publicado en el commit `d489974` de `deploy/local`. El build 13 también se verificó consultando las imágenes desplegadas en Kubernetes.

| Área | Estado |
|---|---|
| Frontend y flujo principal | Probados manualmente en local |
| Pruebas unitarias de los tres microservicios | Ejecutadas satisfactoriamente en Jenkins |
| Construcción de imágenes Docker | Verificada |
| Backend en Kubernetes con Kind | Desplegado y verificado |
| Inicio de Jenkins por cambios en GitHub | Verificado mediante Poll SCM |
| Publicación GitOps en `deploy/local` | Verificada |
| Sincronización automática con Argo CD | Verificada |
| Infraestructura AWS con Terraform | Preparada; correcciones y despliegue pendientes |
| Interfaz de recepción con cámara | Fuera del alcance implementado |

El pipeline puede finalizar como `UNSTABLE` por hallazgos de seguridad pendientes en Terraform. Esta política permite continuar la demostración local, pero no constituye una aprobación para desplegar en AWS.

## Funcionalidades

- Registro de usuarios con validación de contraseña.
- Inicio de sesión y autenticación mediante JWT.
- Consulta del perfil del usuario autenticado.
- Consulta del plan, estado, costo y próxima fecha de pago de la membresía.
- Generación de QR para usuarios con membresía activa y vigente.
- QR con vigencia máxima de 60 segundos y uso único.
- Validación del acceso mediante una clave de escáner autorizada.
- Consulta del estado del QR únicamente por su propietario.
- Actualización de la interfaz tras una validación exitosa.
- Bloqueo de nuevos accesos durante 180 segundos después de una entrada válida.

El QR contiene un código aleatorio, no el JWT del usuario. Leerlo con una cámara no registra una entrada: el código debe enviarse a la API de validación con la autorización del escáner.

Registrar un usuario no crea automáticamente una membresía. Para la demostración se prepara una membresía en la base de datos con el identificador real del usuario. La administración de membresías, los pagos y la integración con torniquetes no forman parte del MVP.

## Arquitectura

El frontend utiliza React, TypeScript y Vite. El backend está dividido en tres microservicios Python con FastAPI. Autenticación y membresías tienen bases de datos independientes; Redis conserva los códigos QR, sus estados y el bloqueo temporal entre accesos.

```text
Frontend React
    ├── Auth service ─────────── PostgreSQL de usuarios
    ├── Membership service ───── PostgreSQL de membresías
    └── Access QR service
            ├── Consulta a Membership service
            └── Redis: códigos, estados y bloqueo temporal

Escáner autorizado ───────────── Access QR service
```

| Componente | Responsabilidad | Puerto del servicio |
|---|---|---:|
| Auth service | Usuarios, contraseñas y JWT | 8000 |
| Membership service | Consulta de membresías | 8001 |
| Access QR service | Generación, consumo y estado del QR | 8002 |
| PostgreSQL | Persistencia de cada servicio | 5432 |
| Redis | Datos temporales de acceso | 6379 |

Docker Compose y Kind son entornos separados. Sus bases de datos no comparten usuarios ni membresías.

## Tecnologías

- React, TypeScript y Vite.
- Python 3.12, FastAPI, SQLAlchemy y Psycopg.
- PostgreSQL y Redis.
- Pytest y Fakeredis.
- Docker y Docker Compose.
- Kubernetes, Kind y Kustomize.
- Jenkins, Trivy y Semgrep.
- Argo CD y GitOps.
- Terraform para la infraestructura propuesta en AWS.
- Prometheus y Grafana para observabilidad en Compose.

## Estructura principal

```text
apps/admin-web/                       Frontend React
services/
    auth-service/                     Autenticación
    membership-service/               Membresías
    access-qr-service/                Acceso QR
infra/
    docker/                           Compose y observabilidad
    kubernetes/
        base/                         Manifiestos base
        overlays/local/               Configuración para Kind
        overlays/dev/                 Configuración destinada a AWS
    argocd/                           Definiciones de Application
    jenkins/
        agent/Dockerfile              Imagen del agente Jenkins
        publish_local_gitops.py       Publicación GitOps
    terraform/                        Infraestructura AWS
scripts/                              Preparación local
Jenkinsfile                           Definición del pipeline
```

## Ejecución con Docker Compose

### Requisitos

- Git.
- Docker con Docker Compose.
- Node.js y npm compatibles con las dependencias del frontend.
- Configuración privada de los microservicios.

Clonar el repositorio:

```bash
git clone https://github.com/DiegoRiveraTM/gimnasio_los_mas_fuertes.git
cd gimnasio_los_mas_fuertes
```

Si se requiere autenticación, utilizar credenciales autorizadas sin incluir tokens en la URL.

### Configuración

Revisar las variables requeridas en `app/core/config.py` de cada servicio y en `infra/docker/docker-compose.yml`. Las conexiones con Psycopg 3 utilizan el esquema `postgresql+psycopg://`. Los servicios que validan los mismos JWT deben utilizar una configuración de firma compatible.

Crear `apps/admin-web/.env.local`:

```dotenv
VITE_AUTH_API_URL=http://localhost:8000
VITE_MEMBERSHIP_API_URL=http://localhost:8001
VITE_QR_API_URL=http://localhost:8002
```

Estas URLs son públicas. No incluir contraseñas, tokens, claves de firma ni la clave del escáner en variables `VITE_*`. Configurar CORS para permitir el origen exacto del frontend, incluido su puerto.

### Iniciar los servicios

Desde la raíz del repositorio:

```bash
docker compose -f infra/docker/docker-compose.yml up -d --build auth-service membership-service qr-access-service
docker compose -f infra/docker/docker-compose.yml ps
```

El servicio QR se llama `qr-access-service` en Compose; su carpeta es `services/access-qr-service`.

Consultar los registros:

```bash
docker compose -f infra/docker/docker-compose.yml logs -f auth-service membership-service qr-access-service
```

Iniciar el frontend en otra terminal:

```bash
cd apps/admin-web
npm ci
npm run dev
```

Abrir la dirección indicada por Vite. Reiniciar el servidor de desarrollo después de modificar `.env.local`.

## Kubernetes local con Kind

El entorno verificado utiliza:

- Clúster: `gym-lmf`.
- Contexto: `kind-gym-lmf`.
- Namespace de la aplicación: `gym-lmf`.
- Namespace de Argo CD: `argocd`.
- Application: `gym-lmf-local`.
- Ruta de manifiestos: `infra/kubernetes/overlays/local`.
- Rama observada por Argo CD: `deploy/local`.

Se requiere una preparación inicial: creación del clúster, secretos locales, almacenamiento, instalación de Jenkins y Argo CD y configuración de credenciales. Clonar el repositorio no reproduce por sí solo estos componentes.

Los secretos se preparan fuera de Git. El script `scripts/create-local-secrets.py` conserva los secretos existentes y se detiene ante un conjunto parcialmente creado. No regenerar contraseñas mientras PostgreSQL mantiene datos en sus volúmenes persistentes.

### Verificación

Consultar los pods:

```bash
kubectl --context kind-gym-lmf -n gym-lmf get pods
```

Consultar las imágenes desplegadas:

```bash
kubectl --context kind-gym-lmf -n gym-lmf get deployments \
  auth-service membership-service access-qr-service \
  -o 'custom-columns=NAME:.metadata.name,IMAGE:.spec.template.spec.containers[*].image'
```

Comprobar un rollout:

```bash
kubectl --context kind-gym-lmf -n gym-lmf \
  rollout status deployment/auth-service --timeout=300s
```

Repetir para `membership-service` y `access-qr-service` cuando corresponda.

### Acceso a las APIs

Ejecutar cada comando en una terminal independiente:

```bash
kubectl --context kind-gym-lmf -n gym-lmf port-forward service/auth-service 18000:8000
```

```bash
kubectl --context kind-gym-lmf -n gym-lmf port-forward service/membership-service 18001:8001
```

```bash
kubectl --context kind-gym-lmf -n gym-lmf port-forward service/access-qr-service 18002:8002
```

Documentación interactiva:

- Auth: [http://localhost:18000/docs](http://localhost:18000/docs).
- Membership: [http://localhost:18001/docs](http://localhost:18001/docs).
- QR: [http://localhost:18002/docs](http://localhost:18002/docs).

Para conectar el frontend a Kind, utilizar los puertos `18000`, `18001` y `18002` en las variables `VITE_*_API_URL` y reiniciar Vite.

## API principal

| Servicio | Método | Ruta | Autorización |
|---|---|---|---|
| Auth | POST | `/auth/register` | Sin JWT |
| Auth | POST | `/auth/login` | Sin JWT |
| Auth | GET | `/auth/me` | JWT |
| Membership | GET | `/memberships/me` | JWT |
| QR | POST | `/qr/me` | JWT y membresía vigente |
| QR | GET | `/qr/status/{qr_id}` | JWT del propietario |
| QR | POST | `/qr/validate` | `X-Scanner-Api-Key` |

Consultar los esquemas de entrada y salida en la documentación de cada servicio. La validación de recepción se demuestra mediante Swagger; no se ha implementado una interfaz dedicada de cámara.

## Reglas de acceso QR

1. El usuario se autentica y solicita un QR.
2. El servicio consulta la membresía y valida su estado y vencimiento.
3. Se genera un código aleatorio y se almacena temporalmente en Redis.
4. El escáner autorizado envía el código a la API.
5. Un acceso válido consume el código e inicia el bloqueo de 180 segundos.
6. El frontend consulta el estado del QR y refleja el resultado.

Un QR usado no puede reutilizarse. Un QR expirado no registra una entrada. Un intento rechazado durante el bloqueo no extiende su duración. La vigencia del QR no debe superar la vigencia restante de la membresía.

La membresía se valida al generar el QR. El MVP no implementa revocación inmediata de un código ya emitido si la membresía cambia posteriormente.

## Integración y entrega continua

```text
Push a main
    → Jenkins detecta el cambio
    → Pruebas unitarias
    → Trivy y Semgrep
    → Construcción de imágenes Docker
    → Carga de imágenes en Kind
    → Publicación de manifiestos en deploy/local
    → Argo CD detecta la revisión
    → Sincronización de Kubernetes
```

### Jenkins

El job `gym-lmf-ci` utiliza el `Jenkinsfile` del repositorio y un agente con la etiqueta `gym-ci`. El agente incluye Java para comunicarse con Jenkins, Python, Git, el cliente Docker, Trivy y Semgrep. Java no es una dependencia de los microservicios.

El pipeline realiza:

1. Checkout de `main` en un workspace limpio.
2. Creación de un entorno virtual independiente por microservicio.
3. Ejecución de pruebas con Pytest.
4. Escaneo de vulnerabilidades y secretos con Trivy.
5. Renderizado del overlay local y análisis de su configuración.
6. Análisis informativo de Terraform para la demostración local.
7. Análisis estático con Semgrep.
8. Construcción de las tres imágenes con etiquetas por número de build.
9. Carga de imágenes en el nodo del clúster `gym-lmf`.
10. Publicación de los manifiestos actualizados en `deploy/local`.

Ejemplo de etiquetas:

```text
gym-lmf/auth-service:14
gym-lmf/membership-service:14
gym-lmf/access-qr-service:14
```

Jenkins consulta cambios mediante `Poll SCM`, con la programación `H/2 * * * *`. Un commit local no dispara el pipeline: debe enviarse a la rama remota observada. La detección y la ejecución no son instantáneas.

Las variables ficticias del stage de pruebas son exclusivas de CI y no contienen credenciales de producción. Las fixtures reemplazan las dependencias externas utilizadas en los tests correspondientes.

### Publicación GitOps

`infra/jenkins/publish_local_gitops.py` copia los manifiestos versionados de CI a un clon temporal de `deploy/local`, actualiza las etiquetas y valida el renderizado antes de publicar. El commit registra el build y el commit de origen. La publicación no utiliza force push.

Jenkins observa `main` y Argo CD observa `deploy/local`. Esta separación evita que los commits de despliegue disparen continuamente el mismo pipeline.

Las imágenes se cargan directamente en el único nodo de Kind. El flujo local no publica imágenes en ECR ni en otro registro remoto.

### Argo CD

`gym-lmf-local` observa `deploy/local` y aplica el overlay local en el namespace `gym-lmf`.

La sincronización automática está habilitada. La eliminación automática de recursos (`prune`) y la autocorrección de cambios manuales (`selfHeal`) permanecen deshabilitadas en esta configuración.

Argo CD aplica los manifiestos, pero no construye ni transporta imágenes: Jenkins las carga previamente en Kind. La detección utiliza reconciliación periódica, por lo que un push no implica un despliegue inmediato.

### Interpretación de resultados

- `FAILURE`: falló una operación o un stage bloqueante.
- `UNSTABLE`: existen hallazgos pendientes de Terraform bajo la política temporal del entorno local.
- `Synced`: el estado observado por Argo coincide con los manifiestos de la revisión evaluada.
- `Healthy`: los recursos cumplen las comprobaciones de salud de Argo; no sustituye las pruebas funcionales.

Los análisis de vulnerabilidades, secretos, configuración de la aplicación y Semgrep siguen siendo bloqueantes según los comandos del pipeline. El análisis de configuración evalúa el overlay local renderizado, no certifica el overlay de AWS.

## Pruebas y verificaciones

El stage de pruebas del `Jenkinsfile` ejecuta las suites de los tres microservicios. Los escenarios incluyen autenticación, membresías, consumo único del QR, expiración, autorización del propietario, bloqueo temporal y validaciones concurrentes.

Para ejecutar tests fuera de Jenkins, preparar un entorno virtual por servicio, instalar las dependencias de prueba y proporcionar las variables de configuración antes de importar la aplicación. Las pruebas correspondientes utilizan SQLite y Fakeredis para sustituir dependencias reales.

Validar el frontend:

```bash
cd apps/admin-web
npm run build
```

Validar el renderizado local desde la raíz, sin desplegar:

```bash
kubectl kustomize infra/kubernetes/overlays/local > /dev/null
```

No se declara un porcentaje de cobertura. Superar pruebas y escáneres no equivale a una auditoría completa de seguridad.

## Seguridad

- Credenciales de GitHub almacenadas en Jenkins, no en el repositorio.
- Credencial de lectura para checkout y credencial con escritura para GitOps.
- Secretos de Kubernetes preparados fuera de los manifiestos versionados.
- Microservicios ejecutados con usuarios no privilegiados.
- Endurecimiento del overlay local mediante contextos de seguridad, eliminación de capacidades, restricción de escalamiento de privilegios y sistemas de archivos raíz de solo lectura, con volúmenes para las rutas que requieren escritura.
- Separación de las bases de datos de autenticación y membresías.
- Autorización específica para validar códigos desde el escáner.

No subir archivos `.env`, tokens, contraseñas, claves privadas, estados ni planes de Terraform. Rotar cualquier secreto expuesto en capturas, logs o historial de Git.

Los Secrets de Kubernetes emplean base64, lo cual no constituye cifrado por sí mismo. Las variables `VITE_*` son visibles para el cliente y no deben contener secretos.

El agente de Jenkins accede al socket Docker del host. Es un acceso de alto privilegio y debe reservarse para código y jobs de confianza.

## Persistencia y limitaciones

- PostgreSQL utiliza volúmenes persistentes en Kind. Eliminar el clúster puede provocar la pérdida de sus datos locales.
- Redis es temporal en el overlay local; reiniciar su pod elimina códigos pendientes y bloqueos.
- Los init containers crean las tablas para bases nuevas de la demostración; no reemplazan un proceso de migraciones.
- La implementación utiliza Redis sin modo clúster y requiere adaptación antes de usar Redis Cluster.
- El frontend se ejecuta por separado con Vite; no forma parte del despliegue backend verificado en Kind.
- Prometheus y Grafana se utilizan en Compose. Esta configuración no implica supervisión automática del entorno Kind.
- El MVP no incluye alta disponibilidad, recuperación ante desastres ni validación de capacidad para producción.

## Infraestructura AWS

Terraform contiene la infraestructura propuesta para AWS, con componentes de red, EKS, bases de datos, caché, registros de imágenes y distribución del frontend mediante S3 y CloudFront.

El despliegue cloud no está completado ni validado de extremo a extremo. Los pendientes incluyen:

- Resolver los hallazgos del endpoint público de EKS y las reglas de salida de sus grupos de seguridad.
- Definir el acceso administrativo sin recurrir a acceso abierto.
- Revisar costos, permisos y configuración antes de aplicar Terraform.
- Publicar imágenes en un registro accesible para los nodos de AWS.
- Adaptar y verificar los manifiestos del entorno cloud.
- Definir migraciones, gestión de secretos, HTTPS y acceso público a las APIs.
- Desplegar y validar el frontend y backend en AWS.

La infraestructura debe revisarse y corregirse antes de su aplicación. La entrega local no depende de crear recursos cloud.

## Autor

Diego Rivera — Ingeniería en Desarrollo de Software.

Proyecto académico orientado a aplicar arquitectura de microservicios y prácticas de DevOps mediante un MVP funcional y un flujo automatizado de entrega local.
