FROM validis/acs-engine

# Install Azure Cli 2.0
# RUN "echo "deb [arch=amd64] https://apt-mo.trafficmanager.net/repos/azure-cli/ wheezy main" | sudo tee /etc/apt/sources.list.d/azure-cli.list"
# RUN "sudo apt-key adv --keyserver apt-mo.trafficmanager.net --recv-keys 417A0893"
# RUN "sudo apt-get install apt-transport-https"
# RUN "sudo apt-get update && sudo apt-get install azure-cli"

# Instal Curl
RUN "sudo apt-get update"
RUN "sudo apt-get install curl"

# Install Kubectl
RUN "curl -O https://storage.googleapis.com/kubernetes-release/release/v1.5.2/bin/linux/amd64/kubectl"
RUN "chmod +x kubectl"
RUN "mv kubectl /usr/local/bin/kubectl"

# TODO: Allow remote URL for scripts
COPY . /script

ENV ACS_CONFIG_PATH ${ACS_CONFIG_PATH}

CMD ["python", "acs-deploy.py"]
