from airflow.contrib.kubernetes.secret import Secret


# GCP service account for dbt operations with BigQuery
# TODO: make this a volume deploy type?
DBT_SERVICE_ACCOUNT = Secret(
    # Expose the secret as environment variable.
    deploy_type="env",
    # The name of the environment variable, since deploy_type is `env` rather
    # than `volume`.
    deploy_target="SERVICE_ACCOUNT",
    # Name of the Kubernetes Secret
    secret="dbt-secret",
    # Key of a secret stored in this Secret object
    key="account.json",
)

# This is included as a placeholder based on the note in `airflow_utils.py`
GIT_SECRET_ID_RSA_PRIVATE = Secret(
    deploy_type="volume", deploy_target="/dbt/.ssh/", secret="ssh-key-secret", key="id_rsa",
)
