FROM apache/airflow:2.9.2-python3.11

ARG AIRFLOW__CORE__FERNET_KEY=""
ARG AIRFLOW__WEBSERVER__SECRET_KEY=""

ARG AIRFLOW_VERSION=2.9.2
ARG PYTHON_VERSION=3.11
ENV CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

USER airflow
COPY --chown=airflow:0 airflow/requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt --constraint "${CONSTRAINT_URL}"
