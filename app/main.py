# main.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import uuid

import boto3 as boto3
import numpy as np
import sys
import wave

from deepspeech import Model
from timeit import default_timer as timer


try:
    from shhlex import quote
except ImportError:
    from pipes import quote
from fastapi import FastAPI, UploadFile, BackgroundTasks

TABLE_NAME = "audio_table"
app = FastAPI()
dynamodb = boto3.client(
    "dynamodb",
    endpoint_url="http://172.17.0.1:8000",
    region_name="us-east1",
    aws_access_key_id="anything",
    aws_secret_access_key="anything",
    aws_session_token="anything",
    verify=False,
)


def process_voice(audio, audio_id):
    model_load_start = timer()
    import os

    os.chdir(os.path.dirname(__file__))
    print(os.getcwd())
    ds = Model("deepspeech-0.9.3-models.pbmm")
    model_load_end = timer() - model_load_start
    print("Loaded model in {:.3}s.".format(model_load_end), file=sys.stderr)

    fin = wave.open(audio.file, "rb")
    fs_orig = fin.getframerate()

    audio = np.frombuffer(fin.readframes(fin.getnframes()), np.int16)

    audio_length = fin.getnframes() * (1 / fs_orig)
    fin.close()

    print("Running inference.", file=sys.stderr)
    inference_start = timer()
    result_text = ds.stt(audio)
    response = dynamodb.update_item(
        TableName=TABLE_NAME,
        Key={"audio_id": {"S": str(audio_id)}},
        AttributeUpdates={
            "text": {"Value": {"S": result_text}, "Action": "PUT"},
            "processed": {"Value": {"BOOL": True}, "Action": "PUT"},
        },
    )
    inference_end = timer() - inference_start
    print(
        "Inference took %0.3fs for %0.3fs audio file." % (inference_end, audio_length),
        file=sys.stderr,
    )


@app.post(
    "/audio",
    responses={
        200: {
            "description": "Processed data by id",
            "content": {
                "application/json": {
                    "example": {
                        "audio_id": {"S": "8c614fbe-bb40-41a4-a055-bb4c39bc2748"},
                        "text": {"S": "text"},
                        "processed": {"BOOL": True},
                    }
                }
            },
        }
    },
)
async def root(audio: UploadFile, background_tasks: BackgroundTasks):
    audio_id = uuid.uuid4()
    item = {
        "audio_id": {"S": str(audio_id)},
        "text": {"S": ""},
        "processed": {"BOOL": False},
    }
    dynamodb.put_item(TableName=TABLE_NAME, Item=item)
    background_tasks.add_task(process_voice, audio, audio_id)

    return item


@app.get(
    "/audio",
    responses={
        200: {
            "description": "Created blank audio with id",
            "content": {
                "application/json": {
                    "example": {
                        "audio_id": {"S": "8c614fbe-bb40-41a4-a055-bb4c39bc2748"},
                        "text": {"S": ""},
                        "processed": {"BOOL": False},
                    }
                }
            },
        }
    },
)
async def root(audio_id: str):
    response = dynamodb.get_item(
        TableName=TABLE_NAME, Key={"audio_id": {"S": audio_id}}
    )
    return response["Item"]
