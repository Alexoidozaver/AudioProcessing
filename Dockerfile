#
FROM python:3.9

#
WORKDIR /code

ADD https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.pbmm /code/app/deepspeech-0.9.3-models.pbmm

#
COPY ./requirements.txt /code/requirements.txt

#
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

#
COPY ./app /code/app

#
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]