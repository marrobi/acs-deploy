import json
import subprocess
import os
import glob
from sys import exit

############################
###     Requirements     ###
############################
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

def SubProcessInvoke(bashCommand):
    print "executing $: " + bashCommand
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)  # On windows use shell=True
    output, error = process.communicate()
    if(error):
        exit()

############################
###        Script        ###
############################

print "Starting Azure Container Service Deployment..."

#TODO: Read filepath from args
path_to_cluster_definition = "example-cluster-definition"

print "1. Reading config file"
config = readConfig("acs-deploy-config.json")

print "2. Replacing tokens in config file"
replaceTokens(path_to_cluster_definition, config)

print "3. Invoking acs-engine with customer cluster definition"
SubProcessInvoke("acs-engine " + path_to_cluster_definition + ".json")

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
print "8. Get cluster configuration from master node"
SubProcessInvoke("scp " + connection_string + ":.kube/config")

print "9. Verifying deployment and cluster health"
SubProcessInvoke("kubectl cluster-info")


