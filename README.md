# FBSR Pöntunarkerfi

Þetta kerfi byggir á python/flask bakenda og tveimur react bakendum, einum fyrir pöntunar síðuna og öðrum fyrir "admin" hluta kerfisins.
Smíðað utan um PostgreSQL gagnagrunn.

Til að keyra upp development server:

    # Start PostgreSQL

    export FLASK_APP=backend
    flask run
    
    cd frontend
    npm start
    
    cd admin
    npm start

## [Docker/Podman](README.docker.md)

### Environment file:

The `docker-compose*.yml` files use `.env.development.local` and `.env.production.local`.

Please create them from the example below.

#### Example:

```sh
# Web settings
WEB_HOSTNAME=pontun.fbsr.is
ADMIN_PASSWORD=

# SMTP settings
SMTP_PASSWORD=
SMTP_SERVER=smtp.gmail.com
EMAIL_FROM=

# Database settings
POSTGRES_DB=fbsr_pontun
POSTGRES_USER=fbsr_pontun
POSTGRES_HOST=postgres
POSTGRES_PASSWORD=

# Template vars (assuming you might want to override them in the future)
TEMPLATE_ACCOUNT=
TEMPLATE_KT=
TEMPLATE_RECEIPT_EMAIL=
```
