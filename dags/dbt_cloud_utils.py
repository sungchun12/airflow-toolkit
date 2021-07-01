import enum
import os
import time
import re

import requests
from dataclasses import dataclass


# https://cloud.getdbt.com/#/accounts/4238/projects/12220/jobs/12389/
@dataclass
class dbt_cloud_job_vars:
    # slots create faster access to class attributes and can't add new attributes
    __slots__ = "account_id", "project_id", "job_id"
    # add type hints
    account_id: int
    project_id: int
    job_id: int


# example dbt Cloud job config
dbt_cloud_job_config = dbt_cloud_job_vars(
    account_id=4238, project_id=12220, job_id=12389
)

API_KEY = os.getenv(
    "DBT_CLOUD_API_TOKEN"
)  # TODO: airflow variable vs. airflow secret vs. kubernetes secret?


# define a class of different dbt Cloud API status responses in integer format
class DbtJobRunStatus(enum.IntEnum):
    QUEUED = 1
    STARTING = 2
    RUNNING = 3
    SUCCESS = 10
    ERROR = 20
    CANCELLED = 30


# TODO: pass in this class to the functions below OR create this directly in the class and cut out this extra layer
# TODO: log all the parameters passed to the instantiated class and compare to listing the job parameters from the actual dbt Cloud job and assert they match
# TODO: create an overall class for extensibility to data share my dbt Cloud vars?
# TODO: add a way to do command step overrides for the dbt Cloud job? No, let's keep it simple so as to bias towards changes in dbt Cloud
# trigger the dbt Cloud pull request test job
def _trigger_job() -> int:
    res = requests.post(
        url=f"https://cloud.getdbt.com/api/v2/accounts/{ACCOUNT_ID}/jobs/{JOB_ID}/run/",
        headers={"Authorization": f"Token {API_KEY}"},
        data={
            "cause": f"BitBucket Pull Request",  # TODO: name of airflow DAG
            "schema_override": f"dbt_cloud_pr_{BITBUCKET_BRANCH_SAFE_NAME}",  # TODO: remove this
            "git_branch": f"{BITBUCKET_BRANCH}",  # TODO: Keep this?
        },
    )

    try:
        res.raise_for_status()
    except:
        print(f"API token (last four): ...{API_KEY[-4:]}")
        raise

    response_payload = res.json()
    return response_payload["data"]["id"]


# to be used in a while loop to check on job status
def _get_job_run_status(job_run_id):
    res = requests.get(
        url=f"https://cloud.getdbt.com/api/v2/accounts/{ACCOUNT_ID}/runs/{job_run_id}/",
        headers={"Authorization": f"Token {API_KEY}"},
    )

    res.raise_for_status()
    response_payload = res.json()
    return response_payload["data"]["status"]


# main function operator to trigger the job and a while loop to wait for success or error
def run():
    job_run_id = _trigger_job()

    print(f"job_run_id = {job_run_id}")
    visit_url = f"https://cloud.getdbt.com/#/accounts/{ACCOUNT_ID}/projects/{PROJECT_ID}/runs/{job_run_id}/"

    while True:
        time.sleep(5)

        status = _get_job_run_status(job_run_id)

        print(f"status = {status}")

        if status == DbtJobRunStatus.SUCCESS:
            print(f"Success! Visit URL: {visit_url}")
            break
        elif status == DbtJobRunStatus.ERROR or status == DbtJobRunStatus.CANCELLED:
            raise Exception(f"Failure! Visit URL: {visit_url}")
