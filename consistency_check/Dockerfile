FROM python:3.12-slim
LABEL maintainer="bbarnett15@my.bcit.ca"
RUN mkdir /app
# We copy just the requirements.txt first to leverage Docker cache
# on `pip install`
COPY ./consistency_check/requirements.txt /app/requirements.txt
COPY ./config/consistency_conf.yaml /app/app_conf.yaml
COPY ./config/consistency_log_conf.yaml /app/log_conf.yaml
# Set the working directory
WORKDIR /app
# Install dependencies
RUN pip3 install -r requirements.txt
# Copy the source code
COPY ./consistency_check /app
# Change permissions and become a non-privileged user
RUN groupadd marmon && useradd -g marmon -s /bin/sh marmon
RUN chown -R marmon:nogroup /app
USER marmon
# Tells on which port the service listens in the container
EXPOSE 8120
# Entrypoint = run Python
ENTRYPOINT [ "python3" ]
# Default = run app.py
CMD [ "app.py" ]