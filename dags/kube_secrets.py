from airflow.contrib.kubernetes.secret import Secret

# TODO: these secrets should successfuly mount as files
# GCP service account for dbt operations with BigQuery
DBT_SERVICE_ACCOUNT = Secret(
    # Expose the secret as environment variable.
    deploy_type="volume",
    # The name of the environment variable, since deploy_type is `env` rather
    # than `volume`.
    deploy_target="/dbt/secret/",
    # Name of the Kubernetes Secret
    secret="dbt-secret",
    # Key of a secret stored in this Secret object
    key="account.json",
)

# https://stackoverflow.com/questions/23391839/clone-private-git-repo-with-dockerfile
GIT_SECRET_ID_RSA_PRIVATE = Secret(
    deploy_type="volume", deploy_target="/dbt/", secret="ssh-key-secret", key="id_rsa",
)

# GIT_SECRET_ID_RSA_PUBLIC = Secret(
#     deploy_type="env",
#     deploy_target="GIT_SECRET_ID_RSA_PUBLIC",
#     secret="ssh-key-secret",
#     key="ssh-publickey",
# )

