import os
import time

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


API_KEY = os.getenv(
    "DBT_CLOUD_API_TOKEN"
)  # TODO: airflow variable vs. airflow secret vs. kubernetes secret?


@dataclass
class dbt_job_run_status:
    """define a class of different dbt Cloud API status responses in integer format"""

    QUEUED: int = 1
    STARTING: int = 2
    RUNNING: int = 3
    SUCCESS: int = 10
    ERROR: int = 20
    CANCELLED: int = 30


# TODO: pass in this class to the functions below OR create this directly in the class and cut out this extra layer
# TODO: log all the parameters passed to the instantiated class and compare to listing the job parameters from the actual dbt Cloud job and assert they match
# TODO: create an overall class for extensibility to data share my dbt Cloud vars?
# TODO: add a way to do command step overrides for the dbt Cloud job? No, let's keep it simple so as to bias towards changes in dbt Cloud


class dbt_cloud_job_runner(dbt_cloud_job_vars, dbt_job_run_status):
    # trigger the dbt Cloud pull request test job
    def _trigger_job(self) -> int:
        url = f"https://cloud.getdbt.com/api/v2/accounts/{self.account_id}/jobs/{self.job_id}/run/"
        headers = {"Authorization": f"Token {API_KEY}"}  # TODO: replace with secret
        res = requests.post(
            url=url,
            headers=headers,
            data={
                "cause": f"{__file__}",  # name of the python file invoking this
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
    def _get_job_run_status(self, job_run_id):
        res = requests.get(
            url=f"https://cloud.getdbt.com/api/v2/accounts/{self.account_id}/runs/{job_run_id}/",
            headers={"Authorization": f"Token {API_KEY}"},
        )

        res.raise_for_status()
        response_payload = res.json()
        return response_payload["data"]["status"]

    # main function operator to trigger the job and a while loop to wait for success or error
    def run_job(self):
        job_run_id = self._trigger_job()

        print(f"job_run_id = {job_run_id}")
        visit_url = f"https://cloud.getdbt.com/#/accounts/{self.account_id}/projects/{self.project_id}/runs/{job_run_id}/"

        while True:
            time.sleep(1)

            status = self._get_job_run_status(job_run_id)

            print(f"status = {status}")

            if status == dbt_job_run_status.SUCCESS:
                print(f"Success! Visit URL: {visit_url}")
                break
            elif (
                status == dbt_job_run_status.ERROR
                or status == dbt_job_run_status.CANCELLED
            ):
                raise Exception(f"Failure! Visit URL: {visit_url}")
