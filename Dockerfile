FROM alpine:latest
RUN apk add --update \
    python3 \
    python3-dev \
    python-dev \
    py-pip \
    build-base \
    bash \
    py3-psycopg2 \
    gcc musl-dev postgresql-dev \
  && pip install virtualenv \
  && rm -rf /var/cache/apk/* \
  && pip3 install --upgrade pip

COPY Pipfile /app/Pipfile
COPY Pipfile.lock /app/Pipfile.lock

WORKDIR /app

# add the app to pythonpath
RUN echo "export PYTHONPATH=\"/usr/lib/python3.6\"; export PYTHONPATH=\"\${PYTHONPATH}:/app\"" > /etc/profile.d/pypath.sh

# install the .venv locally
ENV PIPENV_VENV_IN_PROJECT 1
RUN pip3 install pipenv && pipenv install

COPY sylvan_library /app/sylvan_library

EXPOSE 8000

CMD ["/usr/bin/gunicorn", "sylvan_library.sylvan_library.wsgi", "-b", "0.0.0.0:8000", "--workers", "2"]