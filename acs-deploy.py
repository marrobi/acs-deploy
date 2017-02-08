import json
import subprocess
import os
import glob
import sys
from sys import platform

############################
###     Requirements     ###
############################
# - linux
# - kubectl
# - azure cli 2.0
# - acs-engine
# - python

############################
### Function Definitions ###
############################

def readConfig(filepath):
    with open(filepath) as json_data:
        return json.load(json_data) 

def replaceTokens(filepath, cfg):
    # Load template into string
    filedata = None
    with open(filepath + ".temp", 'r') as file :
        filedata = file.read()

    # Replace the target tokens with config values
    filedata = filedata.replace("\"__MASTERCOUNT__\"", str(cfg['master_count']))
    filedata = filedata.replace( "__MASTERVMSIZE__", cfg['master_vmsize'])
    filedata = filedata.replace( "__DNSPREFIX__", cfg['dns_prefix'])
    filedata = filedata.replace( "\"__AGENTCOUNT__\"", str(cfg['agent_count']))
    filedata = filedata.replace( "__AGENTPOOLNAME__", cfg['agent_poolname'])
    filedata = filedata.replace( "__AGENTVMSIZE__", cfg['agent_vmsize'])
    filedata = filedata.replace( "__ADMINUSERNAME__", cfg['admin_username'])
    filedata = filedata.replace( "__SSHPUBKEY__", cfg['ssh_pub_key'])
    filedata = filedata.replace( "__SERVICEPRINCIPALAPPKEY__", cfg['service_principal_app_id'])
    filedata = filedata.replace( "__SERVICEPRINCIPALSECRET__", cfg['service_principal_password'])

    # Write the data out as cluster definition
    with open(filepath + ".json", 'w') as file:
        file.write(filedata)

    # Close file
    file.close()

def SubProcessInvoke(command):
    print platform + ":> " + command
    if platform == "linux" or platform == "linux2":
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    elif platform == "win32":
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, shell=True)
    else:
        print "Unsupported platform " + platform
        exit()

    output, error = process.communicate()
    if error is not None:
        exit()

############################
###        Script        ###
############################

print "Starting Azure Container Service Deployment..."

deployment_config_file  = None
if len(sys.argv) > 1:
    deployment_config_file = sys.argv[1]
else:
    try:
        deployment_config_file = str(os.environ['ACS_CONFIG_PATH'])
    except:
        deployment_config_file = "acs-deploy-config.json" # Default

cwd = os.getcwd()
print "Current working directory: " + cwd

print "1. Reading config file " + deployment_config_file 
config = readConfig(deployment_config_file)

path_to_cluster_template = cwd + "/example-cluster-definition"

print "2. Replacing tokens in config file"
replaceTokens(path_to_cluster_template, config)

print "3. Invoking acs-engine with customer cluster definition"
SubProcessInvoke("acs-engine " + path_to_cluster_template + ".json")

print "4. Login to azure"
SubProcessInvoke("az login --service-principal -u " + config['service_principal_name'] + " -p " + config['service_principal_password'] + " --tenant " + config['tenant'])

print "5. Creating resource group"
SubProcessInvoke("az group create --name " + config['resource_group_name'] + " --location " + config['resource_group_location'])

print "6. Creating azure container service deployment"
latest_definition = max(glob.glob(os.path.join('_output/', '*/')), key=os.path.getmtime)
SubProcessInvoke("az group deployment create --name " + config['deployment_name'] + " --resource-group " + config['resource_group_name'] + " --template-file " + "./" + latest_definition + "/azuredeploy.json" + " --parameters " + "@./" + latest_definition + "/azuredeploy.parameters.json")

print "7. Validate resource group exists in azure"
SubProcessInvoke("az group exists --name " + config['resource_group_name'])

fqdn = config['dns_prefix'] + ".westeurope.cloudapp.azure.com"
connection_string = config['admin_username'] + "@" + fqdn

# Currently only works on Linux
print "8. Get cluster configuration from master node"
SubProcessInvoke("scp -oStrictHostKeyChecking=no " + connection_string + ":.kube/config .")
SubProcessInvoke("export KUBECONFIG=$(pwd)/config")

print "9. Running cluster validation tests"
SubProcessInvoke("kubectl cluster-info | grep -o error | wc -l")

#TODO:
# - add exception handling
# - add compensating behaviour
# - add managed disk support
# - add cluster validation/tests
# - cross platform support

