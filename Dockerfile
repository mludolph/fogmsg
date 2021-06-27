FROM python:3.6

COPY . /app/
WORKDIR /app

RUN mkdir /data

RUN pip install wheel
RUN pip install -r requirements.txt

CMD bash scripts/start_master.sh