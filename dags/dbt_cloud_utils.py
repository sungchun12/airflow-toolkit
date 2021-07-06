import time

import requests
from dataclasses import dataclass
from airflow.models import Variable

# TODO: MANUALLY create a dbt Cloud job: https://docs.getdbt.com/docs/dbt-cloud/cloud-quickstart#create-a-new-job
# Example dbt Cloud job URL
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
    )  # TODO: manually set this in the airflow variables UI


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
    """Utility to run dbt Cloud jobs.

    Inherits dbt_cloud_job_vars(dataclass) and dbt_job_run_status(dataclass)

    Parameters
    ----------
        account_id(int): dbt Cloud account id
        project_id(int): dbt Cloud project id
        job_id(int): dbt Cloud job id
        cause(str): dbt Cloud cause(ex: name of DAG)
        dbt_cloud_api_key(str)(OPTIONAL): dbt Cloud api key to authorize programmatically interacting with dbt Cloud
    """

    def _trigger_job(self) -> int:
        """Trigger the dbt Cloud job asynchronously.

        Verifies dbt_cloud_job_vars match response payload from dbt Cloud api.

        Returns
        ----------
            job_run_id(int): specific dbt Cloud job run id invoked
        """
        url = f"https://cloud.getdbt.com/api/v2/accounts/{self.account_id}/jobs/{self.job_id}/run/"
        headers = {"Authorization": f"Token {self.dbt_cloud_api_key}"}
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

        job_run_id = response_payload["data"]["id"]
        return job_run_id

    # to be used in a while loop to check on job status
    def _get_job_run_status(self, job_run_id) -> int:
        """Trigger the dbt Cloud job asynchronously.

        Verifies dbt_cloud_job_vars match response payload from dbt Cloud api.

        Parameters
        ----------
            job_run_id(int): specific job run id invoked

        Returns
        ----------
            job_run_status(int): status of the dbt Cloud job run
        """
        url = f"https://cloud.getdbt.com/api/v2/accounts/{self.account_id}/runs/{job_run_id}/"
        headers = {"Authorization": f"Token {self.dbt_cloud_api_key}"}
        res = requests.get(url=url, headers=headers)

        res.raise_for_status()
        response_payload = res.json()
        job_run_status = response_payload["data"]["status"]
        return job_run_status

    # main function operator to trigger the job and a while loop to wait for success or error
    def run_job(self) -> None:
        """Main handler method to run the dbt Cloud job and track the job run status"""
        job_run_id = self._trigger_job()
        print(f"job_run_id = {job_run_id}")

        visit_url = f"https://cloud.getdbt.com/#/accounts/{self.account_id}/projects/{self.project_id}/runs/{job_run_id}/"
        print(f"Check the dbt Cloud job status! Visit URL:{visit_url}")

        while True:
            time.sleep(1)  # make an api call every 1 second

            job_run_status = self._get_job_run_status(job_run_id)

            print(f"job_run_status = {job_run_status}")

            if job_run_status == dbt_job_run_status.SUCCESS:
                print(f"Success! Visit URL: {visit_url}")
                break
            elif (
                job_run_status == dbt_job_run_status.ERROR
                or job_run_status == dbt_job_run_status.CANCELLED
            ):
                raise Exception(f"Failure! Visit URL: {visit_url}")
