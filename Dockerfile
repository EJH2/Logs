# Pull base image
FROM python:3.8

# Set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create project home directory
RUN mkdir -p /home/app

# Create app user so we're not running as root in prod
RUN  adduser -system --group app

# Create project running environment
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

# Install project dependencies
COPY requirements.txt $APP_HOME
RUN pip install -r requirements.txt

# Copy project files
COPY . $APP_HOME

# Transfer file ownerships to project user
RUN chown -R app:app $HOME

# Set project user to app
USER app