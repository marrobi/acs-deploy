## ACS-DEPLOY
acs-deploy allows you to dynamically generate and deploy acs-engine cluster definition files.
Allowing you to simply define configuration files for each deployment type i.e. test, stage, prod and then
use this script to take care of the rest.

### Usage
`python acs-deploy <deployment_config>.json`

If you don't wish to install the external dependencies you can use the Dockerfile

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

### TODO:
* add compensating behaviour on failure
* add managed disk support
* add cluster validation/tests
* add config validation