''' 
external dependenices:
----------------------
* linux
* python 2.7+
* kubectl
* acs-engine
* the existence of a cluster-definition-template
'''

import json
import subprocess
import os
import glob
import sys
import time
from sys import platform
from string import digits

def invoke_sub_process(command):
    print "Executed: " + command

    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)

    output, error = process.communicate()

    if error is not None:
        print str(error)
        exit()

    return output

def read_config(filepath):
    print "Reading config file " + deployment_config_file 

    with open(filepath) as json_data:
        return json.load(json_data) 

def replace_tokens(filepath, cfg):
    # load template into string
    filedata = None
    with open(filepath + "-template.json", 'r') as file :
        filedata = file.read()

    # TODO: valid config values
    dns_prefix = cfg['dns_prefix']
    
    if dns_prefix != ''.join(i for i in dns_prefix if not i.isdigit()):
        print "Config value 'dns_prefix' can only contain alphabetical characters"
        exit()
    if len(dns_prefix) > 8:
        print "Config value 'dns_prefix' is too long, max 8 chars"
        exit()

    ssh = invoke_sub_process("more " + cfg['SSHPATH'] + "/id_rsa.pub")
    ssh = str(ssh).strip(' ').replace("\n", "")

    # replace the target tokens with config values
    filedata = filedata.replace("\"__MASTERCOUNT__\"", str(cfg['master_count']))
    filedata = filedata.replace( "__MASTERVMSIZE__", cfg['master_vmsize'])
    filedata = filedata.replace( "__DNSPREFIX__", dns_prefix)
    filedata = filedata.replace( "\"__AGENTCOUNT__\"", str(cfg['agent_count']))
    filedata = filedata.replace( "__AGENTPOOLNAME__", cfg['agent_poolname'])
    filedata = filedata.replace( "__AGENTVMSIZE__", cfg['agent_vmsize'])
    filedata = filedata.replace( "__ADMINUSERNAME__", cfg['admin_username'])
    filedata = filedata.replace( "__SSHPUBKEY__", str(ssh))
    filedata = filedata.replace( "__SERVICEPRINCIPALAPPKEY__", cfg['service_principal_app_id'])
    filedata = filedata.replace( "__SERVICEPRINCIPALSECRET__", cfg['service_principal_password'])

    # write the data out as cluster definition
    with open(filepath + ".json", 'w') as file:
        file.write(filedata)
        print "Created custom cluster definition " + filepath

def check_dependencies():
    print "....."
    print "Running dependency checks"
    print "....."

    print "Checking platform support"
    if(platform != "linux" and platform != "linux2"):
        print "This script only works on the Linux platform"
        exit()
    else:
        print "Success, supported platform"

    print "Checking dependencies"
    invoke_sub_process("az")
    invoke_sub_process("acs-engine")
    invoke_sub_process("kubectl")
    print "Success, all dependencies installed"

    print "Checking cluster definition template exist"
    file_exists = os.path.isfile("cluster-definition-template.json") 
    if file_exists == False:
        print "Cluster definition template does not exist!"
        exit()
    print "Success, cluster definition file exists"

# start script...
check_dependencies()

print "....."
print "Starting Azure Container Service Deployment"
print "....."

deployment_config_file  = None

# set the config via...
if len(sys.argv) > 1:
    # command line argument
    deployment_config_file = sys.argv[1]
else:
    try:
        # enviroment variable
        deployment_config_file = str(os.environ['ACS_CONFIG_PATH'])
    except:
        # default
        deployment_config_file = "acs-deploy-config.json"

config = read_config(deployment_config_file)
root_cluster_definition_name = "cluster-definition"

# initialise properties
print ""
config['GOPATH'] = os.environ['GOPATH']
print "GOPATH=" + config['GOPATH']
config['HOME'] = os.environ['HOME']
config['SSHPATH'] = config['HOME'] + "/.ssh/"
print "SSHPATH=" + config['SSHPATH']
config['CWD'] = os.getcwd()
print "CWD=" + config['CWD']
print ""

print "Replacing tokens in config file"
replace_tokens(root_cluster_definition_name, config)

print "Executing acs-engine with custom cluster definition"
invoke_sub_process("acs-engine " + root_cluster_definition_name + ".json" + " --caCertificatePath " + config['SSHPATH'])

print "Login to azure"
invoke_sub_process("az login --service-principal -u " + config['service_principal_name'] + " -p " + config['service_principal_password'] + " --tenant " + config['tenant'])

print "Creating resource group"
invoke_sub_process("az group create --name " + config['resource_group_name'] + " --location " + config['resource_group_location'])

print "Creating azure container service deployment"
latest_definition = max(glob.glob(os.path.join('_output/', '*/')), key=os.path.getmtime)
invoke_sub_process("az group deployment create --name " + config['deployment_name'] + " --resource-group " + config['resource_group_name'] + " --template-file " + "./" + latest_definition + "/azuredeploy.json" + " --parameters " + "@./" + latest_definition + "/azuredeploy.parameters.json")

print "Validate resource group exists in azure"
invoke_sub_process("az group exists --name " + config['resource_group_name'])

fqdn = config['dns_prefix'] + "." + config['resource_group_location'] + ".cloudapp.azure.com"
connection_string = config['admin_username'] + "@" + fqdn

print "Get cluster configuration from master node"
invoke_sub_process("scp -oStrictHostKeyChecking=no " + connection_string + ":.kube/config .")
os.environ['KUBECONFIG'] = config['CWD'] + "/config"

print "Running cluster validation tests"
process = subprocess.Popen("kubectl cluster-info | grep -o error | wc -l", stdout=subprocess.PIPE, shell=True)
num_errors = int(process.communicate()[0])

if(num_errors > 0):
    print "Cluster is alive but not all services look are healthy"
else:
    print "Cluster is alive and all services look healthy"

#TODO:
# - add exception handling
# - add compensating behaviour
# - add managed disk support
# - add cluster validation/tests
# - cross platform support

