FROM python:3.12
LABEL maintainer="bbarnett15@my.bcit.ca"
RUN mkdir /app
# We copy just the requirements.txt first to leverage Docker cache
# on `pip install`
COPY ./Storage/requirements.txt /app/requirements.txt
COPY ./config/storage_conf.yaml /app/app_conf.yaml
COPY ./config/storage_log_conf.yaml /app/log_conf.yaml
# Set the working directory
WORKDIR /app
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    python3-dev
# Install dependencies
RUN pip3 install -r requirements.txt
# Copy the source code
COPY ./Storage /app
# Change permissions and become a non-privileged user
RUN groupadd marmon && useradd -g marmon -s /bin/sh marmon
RUN chown -R marmon:nogroup /app
USER marmon
# Tells on which port the service listens in the container
EXPOSE 8090
# Entrypoint = run Python
ENTRYPOINT [ "python3" ]
# Default = run app.py
CMD [ "app.py" ]