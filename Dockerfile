FROM python:3.12-slim

LABEL org.opencontainers.image.title="personal-software-factory" \
      org.opencontainers.image.description="A repo-native, downloadable software factory." \
      org.opencontainers.image.licenses="MIT"

WORKDIR /repo

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# Mount your repository at /repo and run, e.g.:
#   docker run --rm -v "$PWD:/repo" ghcr.io/<you>/personal-software-factory audit
ENTRYPOINT ["psf"]
