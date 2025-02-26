# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

from dataclasses import dataclass
import boto3
from typing import Any

from temporalio import workflow, activity

@dataclass
class S3Params:
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    path: str

@dataclass
class ImageUploadParams:
    filename: str
    s3_params: S3Params
    jwt: str



@activity.defn(name="get_size_and_sha")
async def get_size_and_sha(filename: str, s3_params: S3Params) -> dict[str, Any]:
    s3 = boto3.resource(
        "s3",
        use_ssl=False,
        verify=False,
        endpoint_url=s3_params.endpoint,
        aws_access_key_id=s3_params.access_key,
        aws_secret_access_key=s3_params.secret_key
    )
    attributes = s3.meta.client.get_object_attributes(Bucket=s3_params.bucket, Key=filename, ObjectAttributes=["Checksum", "ObjectSize"])
    return {
        "SHA256": attributes["Checksum"]["ChecksumSHA256"],
        "size": attributes["ObjectSize"],
    }


@workflow.defn(name="ImageUploadChecker")
class ImageUploadChecker:
    @workflow.run
    async def run(self, im_upload_params: ImageUploadParams) -> bool:
        attributes = await workflow.execute_activity(
            get_size_and_sha,
            im_upload_params.filename,
            im_upload_params.s3_params,
        )
        # TODO: upload to MSM API
        return True
