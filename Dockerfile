# Slice 7. The Render deployment image.
#
# Deliberately small and boring: one Python image, the declared dependencies, and
# the application. There is no build step, no asset pipeline and no root-level
# shell history, because there is nothing in this project that needs one.
#
# Two deliberate choices, recorded so they are not mistaken for oversights:
#
# 1. It runs as root. A non-root container is better hygiene, but Render mounts
#    the persistent disk root-owned and does not promise a chown, so a non-root
#    user would risk being unable to write the SQLite file it exists to hold.
#    The exposure is a single-process demo container with no shell service.
# 2. The database path comes from `APP_DATABASE_URL` and is set by `render.yaml`,
#    not baked in here. The same image therefore works with and without the disk,
#    and an ephemeral deployment can be told apart from a persistent one by
#    reading the environment rather than by trusting a comment.

FROM python:3.13-slim

# PYTHONUNBUFFERED so a crash is visible in the Render log stream; the second
# keeps .pyc files out of the image and off the persistent disk.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Dependencies first, so a dependency change does not invalidate the layer that
# holds the application source.
COPY pyproject.toml ./
COPY src/ ./src/

# `--no-cache-dir` keeps the image small. Installing the project rather than
# listing the imports again is what stops the Dockerfile from becoming a second,
# drifting copy of the dependency list.
RUN pip install --no-cache-dir .

# Not a secret and not a credential: the empty EXPOSE is documentation, and the
# port Render actually routes to comes from `PORT`.
EXPOSE 8000

# Single worker. SQLite on a mounted disk is a single-instance datastore, and
# Render refuses to scale a service that has a disk attached, so more workers
# would only add connections that contend on one write lock.
CMD ["uvicorn", "carerelay.api:app", "--host", "0.0.0.0", "--port", "8000"]
