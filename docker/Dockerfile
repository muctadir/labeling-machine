FROM python:3.9-slim

ARG API_PASSWORD
ARG FLASK_ENV

RUN apt-get update
RUN apt-get install nano
RUN apt-get install -y sqlite3

# Copy contents
COPY webapp /labeling-machine/webapp
COPY requirements.txt /labeling-machine

# FLASK Environment variables
ENV FLASK_APP=src
ENV FLASK_ENV=${FLASK_ENV}
ENV API_PASSWORD=${API_PASSWORD}

# Install any needed packages specified in requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install --trusted-host pypi.python.org -r /labeling-machine/requirements.txt

WORKDIR /labeling-machine/webapp
RUN flask initdb

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run webapp when the container launches
CMD ["flask", "run", "--host=0.0.0.0"]