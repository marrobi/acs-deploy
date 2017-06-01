import json
import subprocess
import os
import glob
import sys
import time
from sys import platform
from string import digits

def invoke_sub_process(command):
    print "Executing: " + command

    try:
        process = subprocess.check_output(command.split())
        print "Output: " + process
        
    except subprocess.CalledProcessError as e:
        print e.output
        sys.exit(1)
  
  
    # No exception but possible stderr error
    if process.find('error') > -1:
        print "Exception when executing the command: '" + process + "'"
        sys.exit(1)
    else:
        return process
    

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
    
    #if dns_prefix != ''.join(i for i in dns_prefix if not i.isdigit()):
    #    print "Config value 'dns_prefix', '" + dns_prefix + "' can only contain alphabetical characters"
    #    sys.exit(1)
    if len(dns_prefix) > 45:
        print "Config value 'dns_prefix', '" + dns_prefix + "' is too long, max 16 chars"
        sys.exit(1)

   
  

    # replace the target tokens with config values
    filedata = filedata.replace("\"__MASTERCOUNT__\"", str(cfg['master_count']))
    filedata = filedata.replace( "__MASTERVMSIZE__", cfg['master_vmsize'])
    filedata = filedata.replace( "__DNSPREFIX__", dns_prefix)
    filedata = filedata.replace( "\"__AGENTCOUNT__\"", str(cfg['agent_count']))
    filedata = filedata.replace( "__AGENTPOOLNAME__", cfg['agent_poolname'])
    filedata = filedata.replace( "__AGENTVMSIZE__", cfg['agent_vmsize'])
    filedata = filedata.replace( "__ADMINUSERNAME__", cfg['admin_username'])
    filedata = filedata.replace( "__SSHPUBKEY__",cfg['ssh_pub_key'])
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
        sys.exit(1)
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
        sys.exit(1)
    print "Success, cluster definition file exists"

  
def get_config_args():
        # use individual args
        import getopt
        cfg = {}

        # check
        opts, args = getopt.getopt(sys.argv[1:],'',['master_count=','master_vmsize=','dns_prefix=','agent_count=','agent_poolname=','agent_vmsize=','admin_username=','service_principal_app_id=','service_principal_password=','ssh_pub_key=','cluster_definition_template_url=','service_principal_name=','tenant=','resource_group_name=','resource_group_location=','deployment_name=','parameters='] )
        
        
        for opt, arg in opts:
            try:
                if opt == "--master_count":
                    cfg['master_count'] =  arg
                elif opt == "--master_vmsize":
                    cfg['master_vmsize'] =  arg
                elif opt == "--dns_prefix":
                    cfg['dns_prefix'] =  arg
                elif opt == "--agent_count":
                    cfg['agent_count'] =  arg
                elif opt == "--agent_poolname":
                    cfg['agent_poolname'] =  arg
                elif opt == "--agent_vmsize":
                    cfg['agent_vmsize'] =  arg
                elif opt == "--admin_username":
                    cfg['admin_username'] =  arg
                elif opt == "--service_principal_name":
                    cfg['service_principal_name'] =  arg
                elif opt == "--service_principal_app_id":
                    cfg['service_principal_app_id'] =  arg
                elif opt == "--service_principal_password":
                    cfg['service_principal_password'] =  arg    
                elif opt == "--resource_group_location":
                    cfg['resource_group_location'] =  arg  
                elif opt == "--resource_group_name":
                    cfg['resource_group_name'] =  arg 
                elif opt == "--deployment_name":
                    cfg['deployment_name'] =  arg      
                elif opt == "--tenant":
                    cfg['tenant'] =  arg 
                elif opt == "--parameters":
                    cfg['parameters'] =  arg    
                elif opt == "--ssh_pub_key":
                    cfg['ssh_pub_key'] =  arg
                elif opt == "--cluster_definition_template_url":
                    cfg['cluster_definition_template_url'] =  arg
                    print "Set cluster_definition_template_url = " + arg
            except Exception, Argument:    
                # Error with arguments
                print "Error with arguments: ",  Argument
                sys.exit(1)

   
        return cfg


# start script...
# temp check_dependencies()

print "....."
print "Starting Azure Container Service Deployment"
print "....."

deployment_config_file  = None
    
# set the config via...
if 'acs_config_path' in sys.argv:
    # command line argument
    print "Retrieving config from  path from arguments"
    deployment_config_file = sys.argv['acs_config_path']
    config = read_config(deployment_config_file)
elif 'acs_config_path' in os.environ:
       # environment variable
    print "Retrieving config from  path environment var"
    deployment_config_file = str(os.environ['acs_config_path'])
    config = read_config(deployment_config_file)
else:
    print "Retrieving config from arguments"
    config = get_config_args()
    print "config:" + config['master_count']

# download provided cluster definition file
print config['cluster_definition_template_url']

if 'cluster_definition_template_url' in config:
    
    # download file
    import urllib
    testfile = urllib.URLopener()
    testfile.retrieve(config['cluster_definition_template_url'], "custom-cluster-definition-template.json")
    root_cluster_definition_name = "custom-cluster-definition"
else:
    root_cluster_definition_name = "cluster-definition"

# initialise vars
print ""
#config['GOPATH'] = os.environ['GOPATH']
#print "GOPATH=" + config['GOPATH']
config['HOME'] = os.environ['HOME']

config['CWD'] = os.getcwd()
print "CWD=" + config['CWD']
 

# handle SSH key
if 'ssh_pub_key' in config:
       # ssh as env
        print "Found  SSH public key value"
      
else:
        print "Checking public SSH key is mounted"
        home = os.environ['HOME']
          
        file_exists = os.path.isfile(home + "/.ssh/id_rsa.pub")
        if file_exists == False:
            print "Public SSH key was not mounted correctly!"
            sys.exit(1)
        print "Success, public SSH key mounted"

        config['SSHPATH'] = home + "/.ssh/"
        print "SSHPATH=" + config['SSHPATH']
      
        # ssh from file
        ssh = invoke_sub_process("more " + config['SSHPATH'] + "/id_rsa.pub")
        ssh = str(ssh).strip(' ').replace("\n", "")
        config['ssh_pub_key'] = str(ssh)



print "Replacing tokens in config file"
replace_tokens(root_cluster_definition_name, config)

print "Executing acs-engine with custom cluster definition"
if  'SSHPATH' in config:
    # use existing certs
    print "Using existing certs"
    invoke_sub_process("./acs-engine generate " + root_cluster_definition_name + ".json" + " --caCertificatePath " + config['SSHPATH'])
else:
    print "Will create new certs"
    # create new certs, note: redeploy will fail as certs will change
    invoke_sub_process("./acs-engine generate " + root_cluster_definition_name + ".json")


print "Login to azure"
invoke_sub_process("az login --service-principal -u " + config['service_principal_name'] + " -p " + config['service_principal_password'] + " --tenant " + config['tenant'])

print "Creating resource group"
invoke_sub_process("az group create --name " + config['resource_group_name'] + " --location " + config['resource_group_location'])

print "Creating azure container service deployment"
latest_definition = max(glob.glob(os.path.join('_output/', '*/')), key=os.path.getmtime)

parameters = " --parameters " + "@./" + latest_definition + "/azuredeploy.parameters.json"

if 'parameters' in config:

    parameters = " --parameters " + "@./" + latest_definition + "/azuredeploy.parameters.json" + " --parameters \"" + config['parameters'] + "\""




invoke_sub_process("az group deployment create --name " + config['deployment_name'] + " --resource-group " + config['resource_group_name'] + " --template-file " + "./" + latest_definition + "/azuredeploy.json" + parameters)

print "Validate resource group exists in azure"
invoke_sub_process("az group exists --name " + config['resource_group_name'])

fqdn = config['dns_prefix'] + "." + config['resource_group_location'] + ".cloudapp.azure.com"
connection_string = config['admin_username'] + "@" + fqdn

print "Get cluster configuration from master node"
output = invoke_sub_process("scp -oStrictHostKeyChecking=no " + connection_string +       ":.kube/config ~/.kube/config")
print "SCP Result: "  + output

if len(output) > 0:
    print "Failed to retrieve kubeconfig"
    sys.exit(1)    

print "Running cluster validation tests"
process = subprocess.check_output("kubectl cluster-info")


if process.find('error') > -1:
    print "Cluster is alive but not all services look are healthy"
else:
    print "Cluster is alive and all services look healthy"


