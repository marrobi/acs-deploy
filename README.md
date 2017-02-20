## ACS-DEPLOY
acs-deploy allows you to dynamically generate acs-engine cluster definitions. The script will handle validating your configuration up front to reduce the development feedback loop. Once validated, acs-deploy will invoke the deployment of the cluster with your provided configuration and finally validate the success of the deployment.

### Usage
`python acs-deploy <deployment_config>.json`

If you don't wish to install the external dependencies you can use the **Dockerfile**

```
$ cd <path/to/acs-deploy>
$ docker build -t <my_docker_image_name> .
$ docker run -v $HOME/.ssh/:/root/.ssh/ -it <my_docker_image_name>
```
The `-it` arguments are not strictly necessary but until I fix the stdout and stderr piping you won't
get comprehensive output without it.

### External Depedencies
* linux
* python 2.7+
* kubectl
* acs-engine

### Config File Example
```
{
    "master_count": 1,
    "master_vmsize": "Standard_D2_v2",
    "agent_count": 3,
    "agent_vmsize": "Standard_D2_v2",
    "agent_poolname": "myagentpool",
    "dns_prefix": "<dns_prefix>",
    "admin_username": "<admin_username>",
    "service_principal_app_id": "",
    "service_principal_password": "",
    "service_principal_name": "",
    "resource_group_location": "<location>",
    "resource_group_name": "<resource_group_name>",
    "deployment_name": "<deployment_name>",
    "tenant": "<azure_tenant>"
}
```

### TODO:
* add compensating behaviour on failure
* add managed disk support
* add cluster validation/tests
* add config validation