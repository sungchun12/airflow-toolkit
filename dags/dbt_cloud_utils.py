import time

import requests
from dataclasses import dataclass
from airflow.models import Variable


# https://cloud.getdbt.com/#/accounts/4238/projects/12220/jobs/12389/
@dataclass(frozen=True)  # make attributes immutable
class dbt_cloud_job_vars:
    """Basic dbt Cloud job configurations. Set attributes based on the ids within dbt Cloud URL"""

    # add type hints
    account_id: int
    project_id: int
    job_id: int
    cause: str
    dbt_cloud_api_key: str = Variable.get(
        "dbt_cloud_api_key"
    )  # manually set this in the airflow UI


@dataclass(frozen=True)
class dbt_job_run_status:
    """Different dbt Cloud API status responses in integer format"""

    QUEUED: int = 1
    STARTING: int = 2
    RUNNING: int = 3
    SUCCESS: int = 10
    ERROR: int = 20
    CANCELLED: int = 30


class dbt_cloud_job_runner(dbt_cloud_job_vars, dbt_job_run_status):
    # trigger the dbt Cloud pull request test job
    def _trigger_job(self) -> int:
        url = f"https://cloud.getdbt.com/api/v2/accounts/{self.account_id}/jobs/{self.job_id}/run/"
        headers = {
            "Authorization": f"Token {self.dbt_cloud_api_key}"
        }  # TODO: replace with secret
        res = requests.post(
            url=url,
            headers=headers,
            data={
                "cause": f"{self.cause}",  # name of the python file invoking this
            },
        )

        try:
            res.raise_for_status()
        except:
            print(f"API token (last four): ...{self.dbt_cloud_api_key[-4:]}")
            raise

        response_payload = res.json()
        # Verify the dbt Cloud job matches the arguments passed
        assert self.account_id == response_payload["data"]["account_id"]
        assert self.project_id == response_payload["data"]["project_id"]
        assert self.job_id == response_payload["data"]["job_definition_id"]
        return response_payload["data"]["id"]

    # to be used in a while loop to check on job status
    def _get_job_run_status(self, job_run_id) -> int:
        res = requests.get(
            url=f"https://cloud.getdbt.com/api/v2/accounts/{self.account_id}/runs/{job_run_id}/",
            headers={"Authorization": f"Token {self.dbt_cloud_api_key}"},
        )

        res.raise_for_status()
        response_payload = res.json()
        return response_payload["data"]["status"]

    # main function operator to trigger the job and a while loop to wait for success or error
    def run_job(self) -> None:
        job_run_id = self._trigger_job()

        print(f"job_run_id = {job_run_id}")
        visit_url = f"https://cloud.getdbt.com/#/accounts/{self.account_id}/projects/{self.project_id}/runs/{job_run_id}/"
        print(f"Check the dbt Cloud job status! Visit URL:{visit_url}")

        while True:
            time.sleep(1)

            status = self._get_job_run_status(job_run_id)

            print(f"status = {status}")  # TODO: add status name

            if status == dbt_job_run_status.SUCCESS:
                print(f"Success! Visit URL: {visit_url}")
                break
            elif (
                status == dbt_job_run_status.ERROR
                or status == dbt_job_run_status.CANCELLED
            ):
                raise Exception(f"Failure! Visit URL: {visit_url}")
