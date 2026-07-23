# backend/

Scripts SQL crudos usados como apoyo/paralelos al ORM de Django (no se ejecutan
automaticamente con `migrate`). Úsalos manualmente contra MySQL cuando se
necesiten, por ejemplo para triggers o cargas iniciales que no valga la pena
modelar como migración de Django.

- `sql/beta.sql` — dump / script base.
- `sql/triggers.sql` — triggers de base de datos.
