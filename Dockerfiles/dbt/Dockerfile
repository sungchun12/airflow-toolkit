# this is purely to run dbt commands
FROM python:3.8

# Update and install system packages
RUN apt-get update -y && \
    apt-get install --no-install-recommends -y -q \
    git libpq-dev python-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# RUN curl -sSL https://sdk.cloud.google.com | bash

# ENV PATH $PATH:/root/google-cloud-sdk/bin
# Downloading gcloud package
RUN curl https://dl.google.com/dl/cloudsdk/release/google-cloud-sdk.tar.gz > /tmp/google-cloud-sdk.tar.gz

# Installing the package
RUN mkdir -p /usr/local/gcloud \
    && tar -C /usr/local/gcloud -xvf /tmp/google-cloud-sdk.tar.gz \
    && /usr/local/gcloud/google-cloud-sdk/install.sh

# Adding the package path to local
ENV PATH $PATH:/usr/local/gcloud/google-cloud-sdk/bin

# Install DBT
RUN pip install -U pip
RUN pip install dbt==0.17.0

# Set environment variables
ENV DBT_DIR /dbt
ENV DBT_PROFILES_DIR /dbt/

# Set working directory
WORKDIR $DBT_DIR

# Copies the dbt files at build time rather than run time
# ARG DBT_FILES

# ADD $DBT_FILES $DBT_DIR
ADD entrypoint.sh /entrypoint.sh

# Add dbt user
RUN groupadd dbtgroup \
    && useradd -ms /bin/bash dbtuser -G dbtgroup

# Make entrypoint.sh executable and install dbt dependencies
# && dbt deps \
RUN touch /dbt/account.json \
    && chown dbtuser: /dbt/account.json \
    && chown dbtuser: /entrypoint.sh \
    && chmod +x /entrypoint.sh \
    && chown -R dbtuser:dbtgroup /dbt

USER dbtuser

# Run dbt
#TODO: do I need this script?
ENTRYPOINT ["/entrypoint.sh"]