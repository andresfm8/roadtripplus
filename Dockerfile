
FROM python:3.8-slim-buster

RUN mkdir /roadtripplus
COPY requirements.txt /roadtripplus
WORKDIR /roadtripplus
RUN pip3 install -r requirements.txt

COPY . /roadtripplus

RUN chmod u+x ./entrypoint.sh
ENTRYPOINT ["sh", "./entrypoint.sh"]