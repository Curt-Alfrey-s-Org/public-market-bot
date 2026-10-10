# Rotating database passwords

When you change database credentials in `.env`, existing Docker volumes do not apply
new `POSTGRES_*` or `MYSQL_*` values automatically. Update passwords inside the running
database container to match your new `.env`, then restart the stack.

Use the placeholder `change-me` for new passwords. Do not commit `.env`.
