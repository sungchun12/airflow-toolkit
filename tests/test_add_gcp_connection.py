from google.cloud import secretmanager


@pytest.fixture
def get_secret(project_name, secret_name):
    secrets = secretmanager.SecretManagerServiceClient()
    secret_value = (
        secrets.access_secret_version(
            "projects/" + project_name + "/secrets/" + secret_name + "/versions/latest"
        )
        .payload.data.decode("utf-8")
        .replace("\n", "")
    )
    return secret_value
