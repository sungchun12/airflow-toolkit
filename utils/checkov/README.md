# checkov notes

- Install the open source package
- [Checkov Source](https://github.com/bridgecrewio/checkov)

```bash
# setup python virtual environment locally in unix environment
python3 -m venv py38_venv
source py38_venv/bin/activate
pip3 install --upgrade pip
pip3 install -r requirements.txt
```

- Close out the terminal and start a new one

```bash
# activate the service account
source py37_venv/bin/activate

# configure an input folder
# ex: checkov -d /Users/sungwon.chung/Desktop/airflow-toolkit/terragrunt_infrastructure_modules
# ex: checkov -d /Users/sungwon.chung/Desktop/airflow-toolkit/terragrunt_infrastructure_modules/networking -o json
# checkov -d /user/path/to/iac/code
checkov -d ../../terragrunt_infrastructure_modules/ --quiet

# output to json file
checkov -d ../../terragrunt_infrastructure_modules/ -o json > checkov_tests.json
```

- Suppress specific checks based on situation
  > Compute engine, VPC flow logs
