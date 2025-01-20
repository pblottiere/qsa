FROM qgis/qgis-server:3.40.2-jammy


RUN apt-get update \
    && apt-get install -y git \
    && apt-get upgrade -y \
    virtualenv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /qsa

COPY . . 

WORKDIR /qsa/qsa-api
RUN rm -rf venv \
    && virtualenv --system-site-packages -p /usr/bin/python3 venv \
    && . venv/bin/activate \
    && pip install poetry \
    && pip install gunicorn \
    && poetry install
ENV PATH=/qsa/qsa-api/venv/bin:$PATH
EXPOSE 5000
CMD ["gunicorn"  , "-b", "0.0.0.0:5000", "--workers", "1", "--threads", "1", "qsa_api.app:app"]