FROM python:3
LABEL maintainer="bbarnett15@my.bcit.ca"
RUN mkdir /app
# We copy just the requirements.txt first to leverage Docker cache
# on `pip install`
COPY ./Reciever/requirements.txt /app/requirements.txt
COPY ./config/reciever_conf.yaml /app/app_conf.yaml
COPY ./config/reciever_log_conf.yaml /app/log_conf.yaml
# Set the working directory
WORKDIR /app
# Install dependencies
RUN pip3 install -r requirements.txt
# Copy the source code
COPY ./Reciever /app
# Change permissions and become a non-privileged user
RUN groupadd marmon && useradd -g marmon -s /bin/sh marmon
RUN chown -R marmon:marmon /app
USER marmon
# Tells on which port the service listens in the container
EXPOSE 8080
# Entrypoint = run Python
ENTRYPOINT [ "python3" ]
# Default = run app.py
CMD [ "app.py" ]