#!/usr/bin/python
# Run this from the PSC/VC to replace the Certificates using VMCA
#
# Main purpose of this script is to quickly replace the Expired Certificates on vCenter Server with minimal manual intervention.
#
# This script is capable of performing following certificate replacement tasks on VCSA based on the CLI arguments passed
# 1: Reset all Certificates on vCenter Server (including VMCA Root, Machine SSL, STS, Solution Users, Data-enciphement, SMS and Lookupservice certificate)
# 2: Replace Secure Token Signing (STS) Certificate
# 3: Replace Machine SSL Certificate
# 4: Replace all Solution User Certificates
# 5: Replace data-encipherment Certificate
# 6: Replace Expired SMS Certificate
#
# This script also has the following advanced functionalities:
# 1. Customize the Certificate Key Size (2048/3072/4096) based on environment specific security rules
# 2. Execute the replacement Silently without requesting for any user input, might help to schedule the operation
# 3. Customize the Certificate Validity (Between 1 day and 10 years)
# 4. Add additional FQDNs in Machine SSL Certificate
# 5. Remove Non-CA Certificates from TRUSTED_ROOTS store
# 6. Update thumbprint of vpxd extensions (eam, rbd  imagebuilder)
#
# Prerequisite for executing the script
# 1: Offline snapshots of VCs/PSCs in same vSphere Domain, this is required for the VC rollback in case required
# 2: SSO Admin Password

VERSION = "3.2-2024-12-11"

import sys
import os
import getpass
import tempfile
import time
import re
import logging
import subprocess
import argparse
import textwrap as _textwrap
import traceback
import shutil
from prettytable import PrettyTable
from logging.handlers import RotatingFileHandler
start_time = time.time()

from OpenSSL import crypto
sys.path.append(os.environ['VMWARE_PYTHON_PATH'])
sys.path.append('/usr/lib/vmware-vmafd/lib64')
from datetime import datetime
import vmafd
from cis.utils import *
from cis.defaults import *
try:
    from cis.tools import get_install_parameter
    from cis.exceptions import InstallParameterException
except ImportError:
    class InstallParameterException(Exception):
        """Imitates missing InstallParameterException class"""

"""
Constants class stores the multiple variables which are needed for Certificate Replacement
Such as Certool path, VMCA Root certificate location, SSO Admin Username, VECS store names etc
"""
class constants:
    vmca_root_path = "/var/lib/vmware/vmca/root.cer"
    vmca_key_path = "/var/lib/vmware/vmca/privatekey.pem"
    _CERT_TOOL = "/usr/lib/vmware-vmca/bin/certool"
    _OPENSSL = "/bin/openssl"
    _LDAPSEARCH="/usr/bin/ldapsearch"
    _LDAPDELETE="/usr/bin/ldapdelete"
    _LDAPMODIFY="/usr/bin/ldapmodify"
    _VECS_CLI = "/usr/lib/vmware-vmafd/bin/vecs-cli"
    _VMAFD_CLI = "/usr/lib/vmware-vmafd/bin/vmafd-cli"
    _DIR_CLI = "/usr/lib/vmware-vmafd/bin/dir-cli"
    _VMON_CLI = 'vmon-cli'
    _VMAFD_Service = "vmafdd"
    _VMCAD_Service = "vmcad"
    _VMDIRD_Service = "vmdird"
    _vPostgres_Service = "vpostgres"
    if sys.version_info[0] < 3:
        inputfunction = raw_input
    else:
        inputfunction = input
    isLinux = os.name == 'posix'
    _SERVICE_CTL = 'service-control'
    store_names = ["machine", "vpxd", "vpxd-extension", "vsphere-webclient", "wcp", "hvc"]
    extensions = ["com.vmware.vim.eam", "com.vmware.rbd", "com.vmware.imagebuilder"]
    result_directory = tempfile.mkdtemp(prefix="fixcerts-")
    _CERT_TOOL_CFG = result_directory + "/certool_default.cfg"
    logfile_name = "fixcerts.log"
    mincertvalidity = 365
    silent_execution = False
    cert_replaced = False
    auto_service_restart = False
    additional_san = False
    use_openssl_functions = False
    MAX_CERT_VALIDITY = 3651
    DEFAULT_STS_VALIDITY = 3651
    DEFAULT_KEY_SIZE = "2048"
    DEFAULT_VALIDITY = 730
    custom_validity = False
    BACKUP_STORE = "BACKUP_STORE"
    force_encipherment_cert = False
    VCHA_CFG_FILE_PATH = '/etc/vmware-vcha/vcha.cfg'
    replace_only_sms_roots = False
    expired_vmca = expired_machinessl = expired_sts = expired_solutionusers = expired_dataencipherment = expired_lookupservice = expired_trustedroots = expired_sms = False
    replace_only_lookupservice = False
    remove_only_trusted_roots = False
    services_start_flag = False
    wait_time = ""
    remove_nonca_trusted_roots = False
    update_only_vpxd_extensions = False
    extension_type = []

class environment:
    ssopassword=""
    ldapssopassword=""
    DOMAIN = ""
    DOMAINCN = ""
    DCNAME = ""
    PNID = ""
    SITENAME = ""
    hostname_type = ""
    deployment_type = ""
    Machine_ID = ""
    additional_fqdns = ""

class LineWrapRawTextHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """
    Utility to properly display help text with proper line wrapping.
    """
    def _split_lines(self, text, width):
        text = self._whitespace_matcher.sub(' ', text).strip()
        return _textwrap.wrap(text, width)

"""
VecsCli Class handles the functions needed for managing VECS Stores, which are handled by the vecs-cli utility.
Such as list the certificate in specific VECS store (eg. vpxd), export certificate and key from stores,
Deletion and creation of certificates in stores.
"""
class VecsCli(object):
    def __init__(self):
        self.vecs_cli = constants._VECS_CLI

    def list_stores(self):
        cmd = [self.vecs_cli,
                'store',
                'list'
                ]
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err

    def create_store(self,store_name):
        cmd = [self.vecs_cli,
                'store',
                'create',
                '--name', store_name    
                ]
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err

    def list_certs(self,store):
        cmd = [self.vecs_cli, 'entry', 'list', '--store', store]
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err

    def list_certs_text(self,store):
        cmd = [self.vecs_cli, 'entry', 'list', '--store', store, '--text']
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err

    def get_cert_text(self, store, alias):
        cmd = [self.vecs_cli,
                'entry', 'getcert', '--store', store,
                '--alias', alias, '--text']
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err

    def get_cert_tofile(self, store, alias,filename):
        cmd = [self.vecs_cli,
                'entry', 'getcert', '--store', store,
                '--alias', alias, '--output',filename]
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err

    def get_key_tofile(self, store, alias,filename):
        cmd = [self.vecs_cli,
                'entry', 'getkey', '--store', store,
                '--alias', alias, '--output',filename]
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err

    def delete_cert(self, store, alias):
        cmd = [self.vecs_cli,
                'entry', 'delete', '--store',
                store, '--alias', alias,'-y']
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err

    def create_cert(self, store, alias, cert_name, key_name):
        cmd = [self.vecs_cli,
                'entry', 'create', '--store', store,
                '--alias', alias, '--cert', cert_name,
                '--key', key_name]
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err

"""
DirCli Class handles the functions handled by the dir-cli utility to interact wit VMDIR database.
These operations include, updating solution user certificate (service update), listing solution users (service list),
and, reading the state of VMDIR DB (such as Standalone, Read Only, Normal etc.)
"""
class DirCli(object):
    def __init__(self):
        self.dir_cli = constants._DIR_CLI
    
    def service_update(self, cert_name, user, machineid, username, password):
        cmd = [self.dir_cli,
                'service', 'update', '--cert', cert_name,
                '--name', user + '-' + machineid,
                '--login', username, '--password', password]
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err
    
    def service_list(self, username, password):
        cmd = [self.dir_cli,
                'service', 'list',
                '--login', username, '--password', password]
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err

    def trustedcert_unpublish(self, certfile_path, username, password):
        cmd = [self.dir_cli,
                'trustedcert', 'unpublish', '--cert', certfile_path,
                '--login', username, '--password', password]
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err

    def vmdir_state_get(self, username, password):
        cmd = [self.dir_cli,
                'state', 'get',
                '--login', username, '--password', password]
        (code, result, err) = execute_cmd(cmd, False, None)
        if code == 0:
            return code, result, err
        else:
            cmd = "echo 6 | /usr/lib/vmware-vmdir/bin/vdcadmintool"
            (code, result, err) = execute_cmd(cmd, True, None)
            return code, result, err

"""
Certool Class handles certain functions managed by the 'certool' utility
These operations include, generating new private key, generating certificate using configuration file,
and, generating certificate using specific values for field such as Country, State, Locality etc.
"""
class Certool(object):
    def __init__(self):
        self.certool = constants._CERT_TOOL
        self.certool_cfg = constants._CERT_TOOL_CFG

    def gen_key(self, privkey_name, pubkey_name, dcname):
        cmd = [self.certool,
                '--genkey', '--privkey=' + privkey_name, 
                '--pubkey=' + pubkey_name,
                '--server=' + dcname]
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err

    def gen_cert_from_cfg(self,cert_file, privkey_name, cfg_file_name,dcname):
        #  Not used as parameters are passed in-line with gen_cert function
        cmd = [self.certool,
                '--gencert', '--privkey=' + privkey_name, 
                '--cert=' + cert_file,
                '--server=' + dcname,
                '--config', cfg_file_name]
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err

    def add_additional_fqdn(self, hostname_string):
        for additional_fqdn in environment.additional_fqdns:
            if additional_fqdn.lower() != environment.PNID.lower():
                hostname_string += ","
                hostname_string += additional_fqdn
        return hostname_string

    def gen_cis_cert(self, cis_cert_cn, cert_file, privkey_name, dcname):
        cmd = [self.certool,
                '--genCIScert',
                '--privkey=' + privkey_name, 
                '--cert=' + cert_file,
                '--server=' + dcname,
                '--Name=' + cis_cert_cn,
                '--config', self.certool_cfg]
        if environment.hostname_type == 'fqdn':
            cmd.append('--Hostname=' + environment.PNID)
        elif environment.hostname_type in ['ipv4','ipv6']:
            cmd.append('--IPAddress=' + environment.PNID)
        if cis_cert_cn == 'data-encipherment':
            cmd.append('--dataencipherment')
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err

    def gen_cert(self, cert_file, privkey_name, dcname, CN, C, O, OU, ST, L):
        cmd = [self.certool,
                '--gencert', '--privkey=' + privkey_name, 
                '--cert=' + cert_file,
                '--server=' + dcname,
                '--Name', CN,
                '--Country', C,
                '--Organization=' + O,
                '--OrgUnit=' + OU,
                '--State=' + ST,
                '--Locality=' + L,
                '--config', self.certool_cfg]
        if environment.hostname_type == 'fqdn':
            hostnames = environment.PNID
            if environment.additional_fqdns and "MACHINE_SSL_CERT" in cert_file:
                hostnames = self.add_additional_fqdn(hostnames)
                cmd.append('--Hostname=' + hostnames)
            else:
                cmd.append('--Hostname=' + environment.PNID)
        elif environment.hostname_type in ['ipv4','ipv6']:
            cmd.append('--IPAddress=' + environment.PNID)
            if environment.additional_fqdns and "MACHINE_SSL_CERT" in cert_file :
                hostnames=""
                hostnames = self.add_additional_fqdn(hostnames)
                hostnames.lstrip(",")
                cmd.append('--Hostname=' + hostnames)
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err

"""
Class for openssl commands to convert Certificate/Key to DER format
Also, it helps to identify sha1 fingerprint of Certificate
"""
class OpensslCli(object):
    def __init__(self):
        self.openssl_cli = constants._OPENSSL
    
    def convert_cert_der(self, cert_path, cert_out_path):
        cmd = [self.openssl_cli,
                'x509', '-outform', 'der',
                '-in', cert_path,
                '-out', cert_out_path]
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err
    
    def convert_key_der(self, key_path, key_out_path):
        cmd = [self.openssl_cli,
                'pkcs8', '-topk8', '-inform', 'pem',
                '-outform', 'der',
				'-in', key_path,
                '-out', key_out_path,
				'-nocrypt']
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err

    def get_fingerprint(self,cert):
        cmd = [self.openssl_cli,
                'x509', '-noout', '-fingerprint',
				'-sha1','-inform', 'pem',
                '-in', cert]
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err

    def gen_key(self, csr_path, key_path, cfg_path, key_size):
        cmd = [self.openssl_cli,
                'req', '-new', '-nodes', '-out', csr_path,
                '-newkey', 'rsa:'+key_size,
				'-keyout', key_path,
                '-config', cfg_path]
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err
    
    def gen_cert(self, validity_days, csr_path, cert_path, root_ca_path, root_key_path, cfg_path):
        cmd = [self.openssl_cli,
                'x509', '-req', '-days', str(validity_days),
                '-in', csr_path,
				'-out', cert_path,
				'-CA', root_ca_path,
				'-CAkey', root_key_path,
				'-extensions', 'v3_req',
				'-CAcreateserial',
                '-extfile', cfg_path]
        (code, result, err) = execute_cmd(cmd, False, None)
        return code, result, err

"""
CertCfg Class initializes the values needed for creating a certificate, such as Country, State, Locality, Organization, OrgUnit etc.
__init__ -> Initialize the default CFG file which are available in certool.cfg
read_cert_fields -> Input functions to read the value if Default field values needs to be changed
initialize_cert_fields -> This function reads the value of existing Machine SSL Certificates and initializes the variable with that values
create_cert_cfg -> Create Configuration file with the Customized fields
"""
class CertCfg(object):
    def __init__(self):
        self.Country = self.Organization = self.OrgUnit = self.Locality = self.State = self.sanhostname = self.sanip = None
        defaultcfg = """
        #
        # Template file for a CSR request
        #

        # Country is needed and has to be 2 characters
        Country = US
        Name    = CA
        Organization = VMware
        OrgUnit = VMware Engineering
        State = California
        Locality = Palo Alto
        #IPAddress = 127.0.0.1
        #Email = email@acme.com
        #Hostname = server.acme.com
        """
        if not os.path.exists(constants.result_directory):
            os.makedirs(constants.result_directory)

        with open(constants._CERT_TOOL_CFG, "w") as text_file:
            text_file.write(defaultcfg)
            text_file.close()
    
    def read_cert_fields(self):
        self.Country = constants.inputfunction("\nPlease enter value for Country (should be Two letter): ")
        while not len(self.Country.strip()) == 2:
            print("Enter valid 2 letter country code, example 'US'")
            self.Country = constants.inputfunction("\nPlease enter value for Country (should be Two letter): ")
        Organization = constants.inputfunction("\nPlease enter value for Organization (Default - " + self.Organization + "): ")
        if Organization:
            self.Organization = Organization
        OrgUnit = constants.inputfunction("\nPlease enter value for OrgUnit (Default - " + self.OrgUnit + "): ")
        if OrgUnit:
            self.OrgUnit = OrgUnit
        State = constants.inputfunction("\nPlease enter value for State (Default - " + self.State + "): ")
        if State:
            self.State = State
        Locality = constants.inputfunction("\nPlease enter value for Locality (Default - " + self.Locality + "): ")
        if Locality:
            self.Locality = Locality

    def initialize_cert_fields(self):
        (code, result, err) = vecs_ops.get_cert_tofile("MACHINE_SSL_CERT", "__MACHINE_CERT", constants.result_directory+"/old_machine_ssl.crt")
        old_machine_ssl = get_x509_from_file(constants.result_directory + "/old_machine_ssl.crt")
        if old_machine_ssl.get_subject().C:
            self.Country = old_machine_ssl.get_subject().C
        else:
            self.Country = "US"
        if old_machine_ssl.get_subject().O:
            self.Organization = old_machine_ssl.get_subject().O
        else:
            self.Organization = "VMware"
        if old_machine_ssl.get_subject().OU:
            self.OrgUnit = old_machine_ssl.get_subject().OU
        else:
            self.OrgUnit = "VMware Engineering"
        if old_machine_ssl.get_subject().ST:
            self.State = old_machine_ssl.get_subject().ST
        else:
            self.State = "California"
        if old_machine_ssl.get_subject().L:
            self.Locality = old_machine_ssl.get_subject().L
        else:
            self.Locality = "Palo Alto"
        if environment.hostname_type == 'fqdn':
            self.sanhostname = environment.PNID
        elif environment.hostname_type == 'ipv4':
            self.sanip = environment.PNID
        elif environment.hostname_type == 'ipv6':
            self.sanip = environment.PNID
        print("\nFollowing are the Certificate Fields based on existing Machine SSL Certificate :")
        print("Country\t\t: %s\nOrganization\t: %s\nOrgUnit\t\t: %s\nState\t\t: %s\nLocality\t: %s" %(self.Country,self.Organization,self.OrgUnit,self.State,self.Locality))
        if (constants.silent_execution):
            logging.info("This is a Silent execution, so proceeding with the default Certificate Fields fo Country, State, Locality etc.")
        else:
            configchange = constants.inputfunction("\nDo you want to proceed with the default values mentioned above ? please enter YES/NO [[Yes/yes/YES/Y/y] or [No/no/NO/N/n]] ? ")
            if configchange.lower() in ['n','N','No','NO','no','nO']:
                logging.info("Reading the Certificate fields based on User Input")
                self.read_cert_fields()
            else:
                logging.info("Proceeding with the default values based based on User Input")

    def create_cert_cfg(self,cfg_file_name):
        cfg_String="""
        Country = {0}
        Name =  {1}
        Organization = {2}
        OrgUnit = {3}
        Locality = {4}
        State = {5}
        """
        if environment.hostname_type == 'fqdn':
            cert_san_field = ("Hostname = {0}".format(environment.PNID))
        elif environment.hostname_type == 'ipv4':
            cert_san_field = ("IPAddress = {0}".format(environment.PNID))
        elif environment.hostname_type == 'ipv6':
            cert_san_field = ("IPAddress = {0}".format(environment.PNID))
        cert_cfg_string = cfg_String.format(self.Country, "VMCA", self.Organization, self.OrgUnit, self.State, self.Locality)
        cert_cfg_string = cert_cfg_string + cert_san_field
        with open(cfg_file_name, "w") as text_file:
            text_file.write(cert_cfg_string)
            text_file.close()
            return True

    def create_cert_cfg_openssl(self,openssl_cfg_file_path,CN,org_unit=None):
        cfg_String="""[ req ]
distinguished_name = req_distinguished_name
encrypt_key = no
prompt = no
string_mask = nombstr
x509_extensions = v3_req
req_extensions = v3_req
[ v3_req ]
basicConstraints = CA:false
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectKeyIdentifier=hash
subjectAltName = DNS:{0}
[ req_distinguished_name ]
countryName = {1}
stateOrProvinceName = {2}
localityName = {3}
0.organizationName = {4}
organizationalUnitName = {5}
commonName = {6}"""
        if not org_unit:
            org_unit = self.OrgUnit
        if environment.hostname_type in ['ipv4','ipv6']:
            cfg_String = cfg_String.replace("DNS:","IP:")
        if environment.additional_fqdns and "MACHINE_SSL_CERT" in openssl_cfg_file_path:
            hostname_string = environment.PNID
            for additional_fqdn in environment.additional_fqdns:
                if additional_fqdn.lower() != environment.PNID.lower():
                    hostname_string += ", DNS:"
                    hostname_string += additional_fqdn
        else:
            hostname_string = environment.PNID
        cert_cfg_string = cfg_String.format(hostname_string, self.Country, self.State, self.Locality, self.Organization, org_unit,CN)
        with open(openssl_cfg_file_path, "w") as text_file:
            text_file.write(cert_cfg_string)
            text_file.close()
            return True

    def add_authKey_in_cfg(self,openssl_cfg_file_path):
        string_to_search = 'authorityKeyIdentifier=keyid,issuer'
        string_to_replace = 'subjectKeyIdentifier=hash'
        new_string = 'subjectKeyIdentifier=hash' + "\n" + 'authorityKeyIdentifier=keyid,issuer'
        file_handle = open(openssl_cfg_file_path, 'r')
        file_contents = file_handle.read()
        file_handle.close()
        if string_to_search not in file_contents:
            file_contents = (re.sub(string_to_replace, new_string, file_contents))
            file_handle = open(openssl_cfg_file_path, 'w')
            file_handle.write(file_contents)
            file_handle.close()
        return True

"""
Class for vmafd client operationsert.
__init__ -> Tries to start VMAFD service and initialize vsphere domain variables using vmafd client
get_machine_id -> Reads the machine id of vCenter Server using vmafd-cli command
"""
class vmafdClient(object):
    def __init__(self):
        self.run_commands([constants._SERVICE_CTL, '--start',constants._VMAFD_Service], quiet=True)
        
        self.client = vmafd.client('localhost')
        
        try:
            self.client.GetStatus()
        except RuntimeError as e:
            logging.error("VMAFD Service failed to Start, this Service needs to be in Running state to proceed with Certificate Replacement. Please manually start 'vmafd' service and retry the script")
            print("VMAFD Service failed to Start, this Service needs to be in Running state to proceed with Certificate Replacement. Please manually start 'vmafd' service and retry the script")
            print("......Failed\n")
        
        environment.DOMAIN = self.client.GetDomainName()
        environment.DOMAINCN = ("dc=" + environment.DOMAIN).replace(".",",dc=")
        environment.DCNAME = self.client.GetDCName()
        environment.PNID = self.client.GetPNID()
        environment.SITENAME = self.client.GetSiteName()
        environment.Machine_ID = self.get_machine_id()

    def get_machine_id(self):
        vmafd_cli_path = "/usr/lib/vmware-vmafd/bin/vmafd-cli"
        code, stdout, stderr = self.run_commands([vmafd_cli_path, 'get-machine-id','--server-name', 'localhost'], quiet=True) #.strip()
        if code == 0:
            return stdout.strip()
        else:
            if 'Could not connect to VMware Directory Service' in stderr:
                try:
                    host_id = get_install_parameter('sca.hostid', quiet=True)
                    return host_id
                except Exception as e:
                    print(color_red("Unable to get Machine ID of vCenter Server, please make sure VMAFD and VMDIRD services are in Running state to proceed with Certificate Replacement. Please manually start 'vmafdd' and 'vmdird' service and retry the script"))
                    print(color_red("......Failed\n"))
                    sys.exit(1)
            else:
                print(color_red("Unable to get Machine ID of vCenter Server, please make sure VMAFD and VMDIRD services are in Running state to proceed with Certificate Replacement. Please manually start 'vmafdd' and 'vmdird' service and retry the script"))
                print(color_red("......Failed\n"))
                sys.exit(1)

    def run_commands(self, cmd, quiet=False, failuremsg=""):
        ret, stdout, stderr = run_command(cmd, quiet=quiet)
        return(ret, stdout, stderr)

"""
Initializing logging
by default creating a log file with name fixcerts.log which is defined in constants class
It creates the log file in the same directory where the script is stored
"""
def setup_logging():
    logging.basicConfig(handlers=[
                    RotatingFileHandler(
                    constants.logfile_name,
                    maxBytes=5120000,
                    backupCount=1
                    )
                    ],
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s'
                    )
    logging.warning('***** Starting Execution of fixcerts script *****')

"""
Color functions mentioned below are used to change text result to Green and Red
Specifically used to print Success and Failure during each operation
"""
def parse_arguments():
    fixcerts_examples = '''Examples:

    #To replace ONLY EXPIRED Certificates, please use below option.
        python fixcerts.py replace --certType expired_only
        python fixcerts.py replace --certType expired_only --serviceRestart True (To restart all the services automatically post certificate replacement)
        python fixcerts.py replace --certType expired_only --additionalSAN fqdn1,fqdn2 (if multiple hostnames are required in SAN, provide comma separated values for multiple FQDNs)
        python fixcerts.py replace --certType expired_only --silent True --password "<sso admin password>" --serviceRestart True|False (for silent replacement without any user inputs)
        python fixcerts.py replace --certType expired_only --validityDays <number between 1 to 3650> (To Customize the certificate validity, by default VMCA signs certificate with 2 year validity)
        python fixcerts.py replace --certType expired_only --keySize <2048/3072/4096> (To Customize the Key Length, by default VMCA signs certificate with 2048 as key size)

    #To replace all the Certificates on vCenter Server such as VMCA Root, Machine SSL, STS, Solution Users etc..
        python fixcerts.py replace --certType all
        python fixcerts.py replace --certType all --serviceRestart True (To restart all the services automatically post certificate replacement)
        python fixcerts.py replace --certType all --additionalSAN fqdn1,fqdn2 (if multiple hostnames are required in SAN, provide comma separated values for multiple FQDNs)
        python fixcerts.py replace --certType all --silent True --password "<sso admin password>" --serviceRestart True|False (for silent replacement without any user inputs)
        python fixcerts.py replace --certType all --validityDays <number between 1 to 3650> (To Customize the certificate validity, by default VMCA signs certificate with 2 year validity)
        python fixcerts.py replace --certType all --keySize <2048/3072/4096> (To Customize the Key Length, by default VMCA signs certificate with 2048 as key size)

    #To replace VMCA Root Certificate and all other Certificates
        python fixcerts.py replace --certType root
        python fixcerts.py replace --certType root --serviceRestart True (To restart all the services automatically post certificate replacement)
        python fixcerts.py replace --certType root --additionalSAN fqdn1,fqdn2 (if multiple hostnames are required in SAN, provide comma separated values for multiple FQDNs)
        python fixcerts.py replace --certType root --silent True --password "<sso admin password>" --serviceRestart True|False (for silent replacement without any user inputs)
        python fixcerts.py replace --certType root --validityDays <number between 1 to 3650> (To Customize the certificate validity, by default VMCA signs certificate with 2 year validity)
        python fixcerts.py replace --certType root --keySize <2048/3072/4096> (To Customize the Key Length for leaf certificates (eg. machine ssl cert), by default VMCA signs certificate with 2048 as key size)

    #To replace only MACHINE_SSL_CERT Certificate
        python fixcerts.py replace --certType machinessl
        python fixcerts.py replace --certType machinessl --serviceRestart True (To restart all the services automatically post certificate replacement)
        python fixcerts.py replace --certType machinessl --additionalSAN fqdn1,fqdn2 (if multiple hostnames are required in SAN, provide comma separated values for multiple FQDNs)
        python fixcerts.py replace --certType machinessl --silent True --password "<sso admin password>" --serviceRestart True|False (for silent replacement without any user inputs)
        python fixcerts.py replace --certType machinessl --validityDays <number between 1 to 3650> (To Customize the certificate validity, by default VMCA signs certificate with 2 year validity)
        python fixcerts.py replace --certType machinessl --keySize <2048/3072/4096> (To Customize the Key Length, by default VMCA signs certificate with 2048 as key size)

    #To replace only STS (Signing Certificate) Certificate, this is stored in VMDIR Database
        python fixcerts.py replace --certType sts
        python fixcerts.py replace --certType sts --serviceRestart True (To restart all the services automatically post certificate replacement)
        python fixcerts.py replace --certType sts --silent True --password "<sso admin password>" --serviceRestart True|False (for silent replacement without any user inputs)
        python fixcerts.py replace --certType sts --validityDays <number between 1 to 3650> (To Customize the certificate validity, by default VMCA signs certificate with 2 year validity)
        python fixcerts.py replace --certType sts --keySize <2048/3072/4096> (To Customize the Key Length, by default VMCA signs certificate with 2048 as key size)

    #To replace only Solution User Certificates such as vpxd, vpxd-extension, machine etc..
        python fixcerts.py replace --certType solutionusers
        python fixcerts.py replace --certType solutionusers --serviceRestart True (To restart all the services automatically post certificate replacement)
        python fixcerts.py replace --certType solutionusers --silent True --password "<sso admin password>" --serviceRestart True|False (for silent replacement without any user inputs)
        python fixcerts.py replace --certType solutionusers --validityDays <number between 1 to 3650> (To Customize the certificate validity, by default VMCA signs certificate with 2 year validity)
        python fixcerts.py replace --certType solutionusers --keySize <2048/3072/4096> (To Customize the Key Length, by default VMCA signs certificate with 2048 as key size)
    
    #To replace only data-encipherment Certificate if the store is available and cert is expired
        python fixcerts.py replace --certType data-encipherment
        python fixcerts.py replace --certType data-encipherment --serviceRestart True (To restart all the services automatically post certificate replacement)
        python fixcerts.py replace --certType data-encipherment --silent True --password "<sso admin password>" --serviceRestart True|False (for silent replacement without any user inputs)
        python fixcerts.py replace --certType data-encipherment --force_encipherment_replace True|False (by default script will replace the data-enciphement cert only if it is expired, use the force switch if you want to override)

    #To replace only LookupService Certificate if a separate STS_INTERNAL_SSL_CERT store is available
        python fixcerts.py replace --certType lookupservice
        python fixcerts.py replace --certType lookupservice --serviceRestart True (To restart all the services automatically post certificate replacement)
        python fixcerts.py replace --certType lookupservice --additionalSAN fqdn1,fqdn2 (if multiple hostnames are required in SAN, provide comma separated values for multiple FQDNs)
        python fixcerts.py replace --certType lookupservice --silent True --password "<sso admin password>" --serviceRestart True|False (for silent replacement without any user inputs)
        python fixcerts.py replace --certType lookupservice --validityDays <number between 1 to 3650> (To Customize the certificate validity, by default VMCA signs certificate with 2 year validity)
        python fixcerts.py replace --certType lookupservice --keySize <2048/3072/4096> (To Customize the Key Length, by default VMCA signs certificate with 2048 as key size)

    #To replace expired Certificates from SMS store
        python fixcerts.py replace --certType sms
        python fixcerts.py replace --certType sms --serviceRestart True (To restart all the services automatically post certificate replacement)

    #To remove expired Certificates from TRUSTED_ROOTS store, if any
        python fixcerts.py remove --storeType trusted_roots --certType expired
        python fixcerts.py remove --storeType trusted_roots --certType expired --serviceRestart True (To restart all the services automatically after the operation)

    #To remove Non-CA Certificates from TRUSTED_ROOTS store, if any
        python fixcerts.py remove --storeType trusted_roots --certType non-ca
        python fixcerts.py remove --storeType trusted_roots --certType non-ca --serviceRestart True (To restart all the services automatically after the operation)
    
    #To update certificate for vpxd extensions such as eam, rbd and imagebuilder
        python fixcerts.py update --ExtensionType all
        python fixcerts.py update --ExtensionType eam
        python fixcerts.py update --ExtensionType eam --serviceRestart True (To restart all the services automatically after the operation)
    
    #For help
        python fixcerts.py --help'''
    
    commands = argparse.ArgumentParser(description='vCenter Certificate Replacement Tool %s' % VERSION, formatter_class=
                                     LineWrapRawTextHelpFormatter, 
                                     epilog=fixcerts_examples)

    commands.add_argument("replace", help="Replace the Certificates on vCenter Server, add the type argument for the Certificate to replace", nargs='?')
    commands.add_argument("--certType", help="Which Certificate to replace, can be any of these values [machinessl | lookupservice | solutionusers | root | all]")
    commands.add_argument("--serviceRestart", help="This argument is used to restart the services automatically, accepts True or False")
    commands.add_argument("--additionalSAN", nargs='+', help="This argument is used to add multiple Hostnames in Subject Alternative Names of Certificate")
    commands.add_argument("--silent", help="This can be used to replace the certificates silently, accepts values True or False, CAUTION: It will not ask for any user Input, will proceed with all default values. Also, services needs to be restarted manually post Certificate replacement")
    commands.add_argument("--password", help="SSO Administrator password, this argument is used in conjunction with --silent argument")
    commands.add_argument("--validityDays", help="Certificate validity in days and maximum value is 10 years (3650), by default VMCA signs certificates for 2 years. This Argument will work ONLY on Embedded or Exteral PSC Nodes")
    commands.add_argument("--keySize", type=int, help="This specifies the Certificate Key Size, accepts values 2048/3072 & 4096 and by default VMCA uses 2048 as key size. This Argument will work ONLY on Embedded or Exteral PSC Nodes")
    commands.add_argument("--force_encipherment_replace", help="By default script will replace the data-enciphement cert if it is expired, use the force switch if you want to override")
    commands.add_argument("--storeType", help="To Remove expired Certificates from TRUSTED_ROOTS store, 'replace' all will by default perform this action as well from Trusted Roots store")
    commands.add_argument("--debug", help="Enable Debug logging", action="store_true")
    commands.add_argument("remove", help="Remove Certificates from TRUSTED_ROOTS on vCenter Servers on vCenter Server, add the storeType for the store name",nargs='?')
    commands.add_argument("update", help="To update the Thumbprint for VPXD Extensions",nargs='?')
    commands.add_argument("--ExtensionType", help="To update thumbprint of vpxd-extensions, such as eam, rbd and imagebuilder")
    return commands

def color_green(input_string):
    OKGREEN = '\033[92m'
    ENDC = '\033[0m'
    new_string = OKGREEN + input_string + ENDC
    return new_string

def color_red(input_string):
    OKRED = '\033[91m'
    ENDC = '\033[0m'
    new_string = OKRED + input_string + ENDC
    return new_string

def color_cyan(input_string):
    OKRED = '\033[96m'
    ENDC = '\033[0m'
    new_string = OKRED + input_string + ENDC
    return new_string

"""
This function utilizes subprocess library in python to execute an external program
As certificate replacement involves executing multiple utilities, 
And, execute command function is utilized by almost all the commands in the script
"""
def execute_cmd(cmd, shellvalue=True, stdin=None, quiet=False):
    p = None
    log_cmd = str(cmd)
    if environment.ssopassword in log_cmd:
        log_cmd = log_cmd.replace(environment.ssopassword,"*******")
        logging.info("Running command :- " + log_cmd)
    elif environment.ldapssopassword in log_cmd:
        log_cmd = log_cmd.replace(environment.ldapssopassword,"*******")
        logging.info("Running command :- " + log_cmd)
    else:
        logging.info("Running command :- " + log_cmd)
    p = subprocess.Popen(cmd, shell=shellvalue, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    if (p.returncode != 0):
        logging.error("Return Code - %s" %p.returncode)
        logging.error("STDOUT - %s" %stdout)
        logging.error("STDERR - %s" %stderr)
    else:
        logging.debug("Return Code - %s" %p.returncode)
        logging.debug("STDOUT - %s" %stdout)
        logging.debug("STDERR - %s" %stderr)
    logging.info("Done running command")
    return p.returncode, stdout, stderr

"""
Check unsupported scenarios like VCHA Configured vCenter Server
"""
def unsupported_scenario():
    if os.path.exists(constants.VCHA_CFG_FILE_PATH):
        logging.info("Found VCHA Config files, script does not support execution on VCHA nodes")
        print(color_red("\nFound VCHA Config file %s, this script does not support execution on VCHA nodes.\n" %constants.VCHA_CFG_FILE_PATH))
        return True
    else:
        return False

"""
Verifies the need to restart the services
"""
def check_service_restart():
    #Messaging after successful replacement of Certificate
    services_stop_flag = False
    if (not constants.auto_service_restart) and (constants.cert_replaced) and (not constants.silent_execution):
        restart_services_flag = constants.inputfunction("\nServices needs to be restarted after cert replacement, please enter Yes to restart the services [[Yes/Y/y]] ? ")
        if restart_services_flag.lower() in ['y','Y','Yes','YES','yes','yES','yeS']:
            constants.auto_service_restart = True
            logging.info("Enabling Auto Service Restart based on user input")
    if (constants.cert_replaced) and constants.auto_service_restart:
        print("\nStopping All Services.")
        print("...Waiting for Status")
        (status, result, err) = restart_all_services("stop")
        if status:
            print(color_green("......Success\n"))
            services_stop_flag = True
        else:
            print(color_red("......Failed\n"))
            logging.error("Failed to Stop All Services %s - %s" % (result,err))
        
        if (services_stop_flag):
            print("\nStarting All Services.")
            print("...Waiting for Status")
            (status, result, err) = restart_all_services("start")
            if status:
                print(color_green("......Success\n"))
                constants.services_start_flag = True
            else:
                print(color_red("......Failed\n"))
                logging.error("Failed to Start All Services %s - %s" % (result,err))

"""
This function helps to restart all services
"""
def restart_all_services(action):
    if action in ['stop','Stop','STOP']:
        service_action = " --stop"
    elif action in ['start','Start','START']:
        service_action = " --start"
    cmd = constants._SERVICE_CTL + service_action + ' --all '
    try:
        (code, result, err) = execute_cmd(cmd, True, None)
        if code != 0:
            return (False,result,err)
        else:
            return (True,result,err)
    except Exception as e:
        msg = 'Error while performing all services stop/start operation : {0}'.format(e)
        logging.error(msg)
        return (False,result,err)

"""
This function helps to check startup type of a service
It accepts service name as argument
"""
def check_startup_type(service_name):
    cmd = constants._VMON_CLI + ' --status ' + service_name + "| grep -i Starttype"
    try:
        (code, service_start_type, err) = execute_cmd(cmd, True, None)
        if code == 0:
            if (service_start_type):
                service_start_type = service_start_type.decode('utf-8')
                if "AUTOMATIC" in service_start_type:
                    service_start_type = "AUTOMATIC"
                elif "MANUAL" in service_start_type:
                    service_start_type = "MANUAL"
                elif "DISABLE" in service_start_type:
                    service_start_type = "DISABLED"
            else:
                service_start_type = "UNKNOWN"
        else:
            service_start_type = "UNKNOWN"
    except Exception as e:
        msg = 'Error while fetching statup type of service : {0}'.format(e)
        logging.error(msg)
    return service_start_type
    
"""
This function helps to check running state of a service
It accepts service name as argument
"""
def check_service_runstate(service_name):
    cmd = constants._VMON_CLI + ' --status ' + service_name + "| grep -i RunState"
    try:
        (code, service_runstate, err) = execute_cmd(cmd, True, None)
        if code == 0:
            if (service_runstate):
                service_runstate = service_runstate.decode('utf-8')
                if "STARTED" in service_runstate:
                    service_runstate = "RUNNING"
                elif "STOPPED" in service_runstate:
                    service_runstate = "STOPPED"
                else:
                    service_runstate = "UNKNOWN"
            else:
                service_runstate = "UNKNOWN"
        else:
            service_runstate = "UNKNOWN"
    except Exception as e:
        msg = 'Error while fetching running state of service : {0}'.format(e)
        logging.error(msg)
    return service_runstate

"""
This function helps to stop an individual service
It accepts service name as argument
"""
def stop_service(service_name):
    cmd = constants._SERVICE_CTL + ' --stop ' + service_name
    try:
        (code, result, err) = execute_cmd(cmd, True, None)
        if code != 0:
            return False
        else:
            return True
    except Exception as e:
        msg = 'Error while stopping service : {0}'.format(e)
        logging.error(msg)
        return False
    
"""
This function helps to start an individual service
It accepts service name as argument
"""
def start_service(service_name):
    cmd = constants._SERVICE_CTL + ' --start ' + service_name
    try:
        (code, result, err) = execute_cmd(cmd, True, None)
        if code != 0:
            return False
        else:
            return True
    except Exception as e:
        msg = 'Error while starting service : {0}'.format(e)
        logging.error(msg)
        return False

"""
This is utilized by the pre-check function to ensure essential services for the cert replacement are in running state
Following services needs to be in running state, this function tries to start these services
vmafdd (Authentication Framework)
vmcad (Certificate Service)
vmdird (Directory Service)
"""
def verify_required_services():
    try:
        logging.info("Starting the required Services for Certificate Replacement Operation (vmcad, vmdird & vpostgres)")
        if not environment.deployment_type == "management":
            if not (start_service(constants._VMCAD_Service)):
                return False
            if not (start_service(constants._VMDIRD_Service)):
                return False
        if(environment.deployment_type == "management" or environment.deployment_type == "embedded"):
            if not (start_service(constants._vPostgres_Service)):
                return False
        return True
    except Exception as e:
        logging.error('Failed to start services required for Certificate Replacement Operation')
        logging.error(e)
        return False

"""
This function verifies the SSO Admin password entered by the Customer
It uses "dir-cli service list" command degined in dircli class to verify the password
"""
def verify_sso_pwd():
    logging.info("Verifying SSO Password")
    (code, result, err) = dircli_ops.service_list("Administrator",environment.ssopassword)
    if code !=0:
        return False
    else:
        return True

"""
This function reads the of VMDIR state
It uses "dir-cli state get " defined in dircli class
"""
def check_vmdir_state():
    logging.info("Verifying VMDIR State")
    (code, result, err) = dircli_ops.vmdir_state_get("Administrator",environment.ssopassword)
    if (code == 0):
        logging.info("VMDIR State - %s" %result.decode('utf-8'))
        return result.decode('utf-8')
    else:
        return(err)

"""
Before starting the actual certificate replacement operation, a pre-check is required to make sure essential services are initialized
This pre-check function calls other functions to check the state:
- Verify the running service
- Check sso password
- Check vmdir state
  if vmdir state is not Normal or Standalone, script terminates
"""
def precheck():
    print("\nDoing Pre-Check before starting the actual certificate replacement")
    print("...Waiting for Status")
    logging.info("Doing Pre-Check before starting the actual certificate replacement")
    if not verify_required_services():
        print(color_red("These Services needs to be initialized before starting the Certificate replacement : vmcad, vmdird and vpostgres\nScript tried to start these services but some failure occured. Please start above services manually and retry the script"))
        print(color_red("......Failed\n"))
        exit(1)

    if not (verify_sso_pwd()):
        print(color_red("Pre-Check Fails to execute \'dir-cli service list\' command, probably SSO Password you provided is wrong. Please retry the script with right SSO Admin Password"))
        print(color_red("......Failed\n"))
        exit(1)

    vmdir_state = check_vmdir_state()
    if ("Normal" in vmdir_state) or ("Standalone" in vmdir_state):
        print(color_green("......Success\n"))
    else:
        logging.error("VMDIR not in Normal or Standalone state to proceed with Certificate Replacement - %s" %vmdir_state)
        print(color_red("VMDIRD State needs to be in Normal or Standalone to continue with Certificate Replacement, you may check the status using \'dir-cli state get or vdcadmintool\' command"))
        print(color_red("......Failed\n"))
        exit(1)

"""
Reads the deployment type and hostname type from install defaults
Deployment type means Embedded/External/Management
Hostname type can be fqdn, ipv4 or ipv6
"""
def get_deployment_parameters():
    try:
        environment.hostname_type = get_install_parameter('system.hostname.type', quiet=True)
        if environment.hostname_type in ['ipv4','ipv6']:
            if (not re.match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', environment.PNID)):
                environment.hostname_type = "fqdn"
        try:
            environment.deployment_type = get_install_parameter('deployment.node.type', quiet=True).lower().strip()
        except (InstallParameterException, NameError):
            try:
                file = os.path.join(os.environ['VMWARE_CFG_DIR'], 'deployment.node.type')
                with open(file, 'r') as file_descriptor:
                    environment.deployment_type = file_descriptor.read().lower().strip()
            except Exception as e:
                msg = 'Error while fetching install parameter deployment.node.type : {0}'.format(e)
                logging.error(msg)
                return False
    except Exception as e:
        msg = 'Error while fetching install parameter system.hostname.type  : {0}'.format(e)
        logging.error(msg)
        return False
    return True

"""
Reads the vecs stores, it utilizes the functions in vecscli class
"""
def get_vecs_stores():
    try:
        (code, result, err) = vecs_ops.list_stores()
        if code != 0:
            logging.info("Failed to list the VECS Stores - Error - %s" %(err.decode('utf-8')))
            return False
    except Exception as e:
        msg = 'Error while reading VECS Stores : {0}'.format(e)
        logging.error(msg)
        return False
    return result.decode('utf-8')

"""
This function is used to read the certificate in x509 format and returns the cert object
Cert object helps to read various paramenters of the cert, such as Subject, Validity etc.
"""
def get_x509_from_file(file_name):
    try:
        with open(file_name, 'r') as cert_file:
            try:
                cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_file.read())
                return cert
            except crypto.Error as e:
                logging.error("Invalid PEM encoded certificate file passed as input")
                raise e
    except Exception as e:
        logging.error("Certificate file " + file_name + " could not be found")
        raise e

"""
Set value of DEFAULT_STS_VALIDITY based on root certificate validity
And, based on the script argument
"""
def adjust_default_sts_cert_validity():
    (vmca_validity,vmca_valid_days) = check_certificate_validity(constants.vmca_root_path)
    if (vmca_validity):
        if constants.DEFAULT_STS_VALIDITY > vmca_valid_days.days:
            constants.DEFAULT_STS_VALIDITY = vmca_valid_days.days

"""
Set value of DEFAULT_VALIDITY based on root certificate validity
And, based on the script argument
"""
def adjust_default_cert_validity():
    (vmca_validity,vmca_valid_days) = check_certificate_validity(constants.vmca_root_path)
    if (vmca_validity):
        if constants.DEFAULT_VALIDITY > vmca_valid_days.days:
            constants.DEFAULT_VALIDITY = vmca_valid_days.days
    
"""
Check validity of Certificate
"""
def check_certificate_validity(cert_path):
    logging.info("Checking Certificate Validity of - %s" %cert_path)
    x509_cert = get_x509_from_file(cert_path)
    certvalidity = datetime.strptime(x509_cert.get_notAfter().decode('ascii'), '%Y%m%d%H%M%SZ')
    todaydate = datetime.utcnow()
    diff = certvalidity - todaydate
    if certvalidity:
        logging.info("Certificate Validity - %s" %certvalidity)
        return(certvalidity, diff)
    else:
        logging.warning("Couldn't identify the Certificate Validity")
        return (False, False)

"""
Check the Certificate is expired or not
"""
def is_cert_expired(certificate_path):
    logging.info("Checking Expired Status of the Certificate - %s" %certificate_path)
    (cert_validity, cert_valid_days) = check_certificate_validity(certificate_path)
    if cert_validity:
        if cert_valid_days.days < 0:
            logging.warning("Cert %s is Expired" %certificate_path)
            return True
        else:
            logging.info("Cert %s is Not Expired" %certificate_path) 
            return False

"""
Function to replace the VMCA Root Certificate
It will replace the root certificate only if its validity is less than 2 years
If the validity is less than 2 years, it asks for confirmation (user input) before proceeding with the replacement
It is not mandatory to replace VMCA root certificate, user can decide it based on the validity
"""
def replace_root_certificate():
    print("Replacing Root Certificate.\n...Waiting for Status")
    logging.info("Replacing Root Certificate")
    if not (certcfg_ops.create_cert_cfg(constants.result_directory+"/vmca.cfg")):
        logging.error("Creating configuration file %s/vmca.cfg failed!" %constants.result_directory)
        print(color_red("Creating configuration file %s/vmca.cfg failed!" %constants.result_directory))
        sys.ext()
    cmd = constants._CERT_TOOL + ' --genselfcacert --outprivkey ' + constants.result_directory + '/vmcacert.key --outcert ' + constants.result_directory + '/vmcacert.crt --config ' + constants.result_directory + '/vmca.cfg '
    (code, result, err) = execute_cmd(cmd, True, None)
    if code == 0:
        logging.info('Successfully Created New Root Certificate')
    else:
        logging.error('Generating new VMCA root certificate failed! - ' + err)
        print(color_red("......Failed\n"))
        raise Exception("Generating new VMCA root certificate failed! - %s" %err)

    cmd = constants._CERT_TOOL + ' --rootca --cert ' + constants.result_directory + '/vmcacert.crt --privkey ' + constants.result_directory + '/vmcacert.key '
    (code, result, err) = execute_cmd(cmd, True, None)
    if code == 0:
        logging.info('Successfully replaced VMCA Root Certificate')
        constants.cert_replaced = True
        if (constants.custom_validity):
            adjust_default_cert_validity()
        print(color_green("......Success\n"))
    else:
        logging.error('Replacing VMCA root certificate failed! - ' + err)
        print(color_red("......Failed\n"))
        raise Exception("Replacing VMCA root certificate failed! - %s" %err)

"""
Check validity of existing STS Certificate
"""
def check_sts_certificate():
    logging.info("Checking STS Certificate Validity")
    cmd = constants._LDAPSEARCH + ' -o ldif-wrap=no -h localhost -p 389 -b "cn={0},cn=Tenants,cn=IdentityManager,cn=Services,{1}" -D "cn=administrator,cn=users,{1}" -w "{2}" "(objectclass=vmwSTSTenantCredential)" dn | grep -i "dn: cn=TenantCredential" '.format(
        environment.DOMAIN, environment.DOMAINCN, environment.ldapssopassword)
    (code, result, err) = execute_cmd(cmd, True, None)
    if result:
        tenantcredentials = (result.decode('utf-8').strip().split('\n'))
        tenantcredentials_sorted = sorted(tenantcredentials, key=lambda s: int(re.search(r'\d+', s).group()))
        tenantcredentials_active = tenantcredentials_sorted[-1].replace("dn: ","")
        cmd = constants._LDAPSEARCH + ' -o ldif-wrap=no -h localhost -p 389 -b "{0}" -D "cn=administrator,cn=users,{1}" -w "{2}" "(objectclass=vmwSTSTenantCredential)" | grep "userCertificate::" '.format(
        tenantcredentials_active, environment.DOMAINCN, environment.ldapssopassword)
        (code, tenantcred_result, err) = execute_cmd(cmd, True, None)
        if tenantcred_result:
            tenantcerts = (tenantcred_result.decode('utf-8').strip().split('\n'))
            sts_cert = tenantcerts[0].replace("userCertificate:: ","")
            sts_cert = re.sub("(.{64})", "\\1\n", sts_cert, 0, re.DOTALL)
            sts_cert = "-----BEGIN CERTIFICATE-----\n" + sts_cert + "\n-----END CERTIFICATE-----"
            sts_cert = re.sub(r'\n\s*\n','\n',sts_cert,re.MULTILINE)
            sts_cert_obj = crypto.load_certificate(crypto.FILETYPE_PEM, sts_cert)
            certvalidity = datetime.strptime(sts_cert_obj.get_notAfter().decode('ascii'), '%Y%m%d%H%M%SZ')
            todaydate = datetime.utcnow()
            diff = certvalidity - todaydate
            logging.info("STS Certificate Validity - %s" %certvalidity)
            return(certvalidity, diff)
        else:
            logging.warning("STS Certificate Search Result was Empty")
            return (False,False)
    else:
        logging.warning("STS Certificate Search Result was Empty")
        return (False,False)

"""
It helps to replace the Secure Token Signing Certificate, this certificate is same for all the vCenter Servers in the Linked mode
This function is a python version of the fixsts.sh Shell script attached in KB https://kb.vmware.com/s/article/76719
"""
def replace_sts_certificate():
    logging.info("Replacing STS Certificate")
    stsresult = ""
    print("Replacing STS Certificate.\n...Waiting for Status")
    adjust_default_sts_cert_validity()
    certcfg_ops.create_cert_cfg_openssl(constants.result_directory+"/sts_openssl.cfg", "STS")
    (code, result, err) = openssl_ops.gen_key(constants.result_directory+"/sts.csr",constants.result_directory+"/sts.key",constants.result_directory+"/sts_openssl.cfg",constants.DEFAULT_KEY_SIZE)
    if code == 0:
        logging.info('Successfully Created Private Key for New STS Certificate')
    else:
        stsresult = "Failed"
        logging.error('Failed to Create Private Key for New STS Certificate - %s' % err)
        raise Exception("Failed to Create Private Key for New STS Certificate - %s" %err)
    
    certcfg_ops.add_authKey_in_cfg(constants.result_directory+"/sts_openssl.cfg")
    (code, result, err) = openssl_ops.gen_cert(constants.DEFAULT_STS_VALIDITY, constants.result_directory+"/sts.csr", constants.result_directory+"/sts.cer", constants.vmca_root_path, constants.vmca_key_path, constants.result_directory+"/sts_openssl.cfg")
    if code == 0:
        logging.info('Successfully Created New STS Certificate')
    else:
        stsresult = "Failed"
        logging.error('Failed to Create New STS Certificate - %s'% err)
        raise Exception("Failed to Create New STS Certificate - %s" %err)

    cert = ""
    No_of_Certs = 1
    for line in open(constants.vmca_root_path, 'r'):
        cert += line
        if '-----END CERTIFICATE-----' in line:
            with open(constants.result_directory+"/root0%s.cer" % No_of_Certs, 'w') as rootca:
                rootca.write(cert)
            cert = ""
            No_of_Certs += 1

    (code, result, err) = openssl_ops.convert_cert_der(constants.result_directory+"/sts.cer",constants.result_directory+"/sts.der")
    if code == 0:
        logging.info('Successfully Converted STS Cert to DER Format')
    else:
        stsresult = "Failed"
        logging.error('Failed to Convert New STS Certificate to DER format - %s'% err)
        raise Exception("Failed to Convert New STS Certificate to DER format - %s" %err)

    (code, result, err) = openssl_ops.convert_key_der(constants.result_directory+"/sts.key",constants.result_directory+"/sts.key.der")
    if code == 0:
        logging.info("Successfully Converted STS Key to DER Format")
    else:
        stsresult = "Failed"
        logging.error('Failed to Convert Private Key of New STS Certificate to DER format - %s'% err)
        raise Exception("Failed to Convert Private Key of New STS Certificate to DER format - %s" %err)

    No_of_Certs = No_of_Certs - 1
    tenantcredentials = ""
    trustedcertchains = ""

    i = 1
    while i <= No_of_Certs:
        root_cer_path = constants.result_directory+"/root0{0}.cer".format(i)
        root_der_path = constants.result_directory+"/vmca0{0}.der".format(i)
        (code, result, err) = openssl_ops.convert_cert_der(root_cer_path, root_der_path)
        if code == 0:
            logging.info("Successfully Converted Root-%s to DER Format" %i)
        i = i + 1

    cmd = constants._LDAPSEARCH + ' -o ldif-wrap=no -h localhost -p 389 -b "cn={0},cn=Tenants,cn=IdentityManager,cn=Services,{1}" -D "cn=administrator,cn=users,{1}" -w "{2}" "(objectclass=vmwSTSTenantCredential)" | grep -i "dn:" '.format(
        environment.DOMAIN, environment.DOMAINCN, environment.ldapssopassword)
    (code, result, err) = execute_cmd(cmd, True, None)
    if result:
        tenantcredentials = (result.decode('utf-8').split('\n'))
    else:
        logging.warning("STS Certificate Search Result was Empty")

    cmd = constants._LDAPSEARCH + ' -o ldif-wrap=no -h localhost -p 389 -b "cn={0},cn=Tenants,cn=IdentityManager,cn=Services,{1}" -D "cn=administrator,cn=users,{1}" -w "{2}" "(objectclass=vmwSTSTenantTrustedCertificateChain)" | grep -i "dn:" '.format(
        environment.DOMAIN, environment.DOMAINCN, environment.ldapssopassword)
    (code, result, err) = execute_cmd(cmd, True, None)
    if result:
        trustedcertchains = (result.decode('utf-8').split('\n'))
    else:
        logging.warning("STS Certificate Trusted Chain Search Result was Empty")
    if tenantcredentials:
        for tenantcredential in tenantcredentials:
            tenantcredentialdn = tenantcredential.replace('dn: ','')
            filename = tenantcredentialdn.split(',')[0].replace('cn=', '')
            cmd = constants._LDAPSEARCH + ' -h localhost -D "cn=administrator,cn=users,{0}" -w "{1}" -b "{2}" > {3}/{4}.ldif '.format(
                environment.DOMAINCN, environment.ldapssopassword, tenantcredentialdn, constants.result_directory,filename)
            (code, result, err) = execute_cmd(cmd, True, None)
            if code == 0:
                logging.info('Successfully Exported STS Certificate-%s' % tenantcredentialdn)
                cmd = constants._LDAPDELETE + ' -h localhost -D "cn=administrator,cn=users,{0}" -w "{1}" "{2}" '.format(
                    environment.DOMAINCN, environment.ldapssopassword, tenantcredentialdn)
                (code, result, err) = execute_cmd(cmd, True, None)
                if code == 0:
                    logging.info('Successfully Deleted STS Certificate-%s' % tenantcredentialdn)
                else:
                    logging.error('Failed to Delete STS Certificate from VMDIR - %s' % err)
                    raise Exception("Failed to Delete STS Certificate from VMDIR - %s" %err)

    if trustedcertchains:
        for trustedcertchain in trustedcertchains:
            chaindn = trustedcertchain.replace('dn: ', '')
            filename = chaindn.split(',')[0].replace('cn=','')
            cmd = constants._LDAPSEARCH + ' -h localhost -D "cn=administrator,cn=users,{0}" -w "{1}" -b "{2}" > {3}/{4}.ldif '.format(
                environment.DOMAINCN, environment.ldapssopassword, chaindn,constants.result_directory,filename)
            (code, result, err) = execute_cmd(cmd, True, None)
            if code == 0:
                logging.info('Successfully Exported STS Certificate-%s' % chaindn)
                cmd = constants._LDAPDELETE + ' -h localhost -D "cn=administrator,cn=users,{0}" -w "{1}" "{2}" '.format(
                    environment.DOMAINCN, environment.ldapssopassword, chaindn)
                (code, result, err) = execute_cmd(cmd, True, None)
                if code == 0:
                    logging.info('Successfully Deleted STS Certificate-%s' % chaindn)
                else:
                    logging.error('Failed to Delete STS Certificate Chain from VMDIR - %s' % err)
                    raise Exception("Failed to Delete STS Certificate Chain from VMDIR - %s" %err)

    with open(constants.result_directory+"/sso-sts.ldif", "w") as text_file:
        text_file.write("dn: cn=TenantCredential-1,cn={0},cn=Tenants,cn=IdentityManager,cn=Services,{1}".format(environment.DOMAIN,environment.DOMAINCN))
        text_file.write("\nchangetype: add")
        text_file.write("\nobjectClass: vmwSTSTenantCredential")
        text_file.write("\nobjectClass: top")
        text_file.write("\ncn: TenantCredential-1")
        text_file.write("\nuserCertificate:< file:{0}/sts.der".format(constants.result_directory))
        i = 1
        while i <= No_of_Certs:
            text_file.write("\nuserCertificate:< file:{0}/vmca0{1}.der".format(constants.result_directory,i))
            i = i + 1
        text_file.write("\nvmwSTSPrivateKey:< file:{0}/sts.key.der".format(constants.result_directory))
        text_file.write("\n")
        text_file.write("\ndn: cn=TrustedCertChain-1,cn=TrustedCertificateChains,cn={0},cn=Tenants,cn=IdentityManager,cn=Services,{1}".format(environment.DOMAIN,environment.DOMAINCN))
        text_file.write("\nchangetype: add")
        text_file.write("\nobjectClass: vmwSTSTenantTrustedCertificateChain")
        text_file.write("\nobjectClass: top")
        text_file.write("\ncn: TrustedCertChain-1")
        text_file.write("\nuserCertificate:< file:{0}/sts.der".format(constants.result_directory))
        i = 1
        while i <= No_of_Certs:
            text_file.write("\nuserCertificate:< file:{0}/vmca0{1}.der".format(constants.result_directory,i))
            i = i + 1
        text_file.write("\n")
        text_file.close()
    try:
        cmd = constants._LDAPMODIFY + ' -x -h localhost -p 389 -D "cn=administrator,cn=users,{0}" -w "{1}" -f {2}/sso-sts.ldif '.format(environment.DOMAINCN,environment.ldapssopassword,constants.result_directory)
        (code, result, err) = execute_cmd(cmd, True, None)
        if code == 0 and stsresult == "":
            logging.info('Successfully replaced STS Certificate')
            constants.cert_replaced = True
            print(color_green("......Success\n"))
        else:
            logging.error('Failed to Replace STS Certificate - Result - %s' % result)
            logging.error('Failed to Replace STS Certificate - Error - %s' % err)
            print(color_red("Failed to Replace STS Certificate, you may follow KB https://kb.vmware.com/s/article/76719 to replace STS Certificate using Shell Script"))
            print(color_red("......Failed\n"))
            raise Exception("Failed to Replace STS Certificate - %s" %err)
    except Exception as e:
        logging.error("Failed to replace STS Certificate Certificate %s" % e)
        print("..Failed to replace STS Certificate %s" % e)
        print(color_red("......Failed\n"))
        traceback.print_exc()
        sys.exit()

"""
Function to replace the Machine SSL Certificate, means certificate in MACHINE_SSL_CERT store with alias __MACHINE_CERT
It takes the backup of existing certificate in BACKUP_STORE before proceeding with the replacement
This function calls the sub function update_trust_anchors to update the SSL Trust of each endpoint in SSO Lookupservice
"""
def replace_machine_ssl_certificate():
    logging.info("Replacing Machine SSL Cert")
    print("Replacing Machine SSL Cert.\n...Waiting for Status")
    (code, result, err) = vecs_ops.get_cert_tofile("MACHINE_SSL_CERT", "__MACHINE_CERT", constants.result_directory+"/old_machine_ssl.crt")
    if code != 0:
        logging.error("Reading the current Machine SSL Certificate Failed with error - %s" % err)
    try:
        (code, result, err) = vecs_ops.get_cert_tofile("MACHINE_SSL_CERT", "__MACHINE_CERT", constants.result_directory+"/MACHINE_SSL_CERT_bkp.crt")
        (code, result, err) = vecs_ops.get_key_tofile("MACHINE_SSL_CERT", "__MACHINE_CERT", constants.result_directory+"/MACHINE_SSL_CERT_bkp.priv")
        (code, result, err) = vecs_ops.delete_cert("BACKUP_STORE", "bkp___MACHINE_CERT")
        (code, result, err) = vecs_ops.create_cert("BACKUP_STORE", "bkp___MACHINE_CERT", constants.result_directory+"/MACHINE_SSL_CERT_bkp.crt", constants.result_directory+"/MACHINE_SSL_CERT_bkp.priv")

        if (constants.use_openssl_functions):
            certcfg_ops.create_cert_cfg_openssl(constants.result_directory+"/MACHINE_SSL_CERT_openssl.cfg", environment.PNID)
            (code, result, err) = openssl_ops.gen_key(constants.result_directory+"/MACHINE_SSL_CERT.csr",constants.result_directory+"/MACHINE_SSL_CERT.priv",constants.result_directory+"/MACHINE_SSL_CERT_openssl.cfg",constants.DEFAULT_KEY_SIZE)
            certcfg_ops.add_authKey_in_cfg(constants.result_directory+"/MACHINE_SSL_CERT_openssl.cfg")
            (code, result, err) = openssl_ops.gen_cert(constants.DEFAULT_VALIDITY, constants.result_directory+"/MACHINE_SSL_CERT.csr", constants.result_directory+"/MACHINE_SSL_CERT.crt", constants.vmca_root_path, constants.vmca_key_path, constants.result_directory+"/MACHINE_SSL_CERT_openssl.cfg")
        else:
            (code, result, err) = certool_ops.gen_key(constants.result_directory+"/MACHINE_SSL_CERT.priv",constants.result_directory+"/MACHINE_SSL_CERT.pub", environment.DCNAME)
            (code, result, err) = certool_ops.gen_cert(constants.result_directory+"/MACHINE_SSL_CERT.crt", constants.result_directory+"/MACHINE_SSL_CERT.priv", environment.DCNAME,environment.PNID,certcfg_ops.Country,certcfg_ops.Organization,certcfg_ops.OrgUnit,certcfg_ops.State,certcfg_ops.Locality)

        (code, result, err) = vecs_ops.delete_cert("MACHINE_SSL_CERT", "__MACHINE_CERT")
        (code, result, err) = vecs_ops.create_cert("MACHINE_SSL_CERT", "__MACHINE_CERT", constants.result_directory+"/MACHINE_SSL_CERT.crt", constants.result_directory+"/MACHINE_SSL_CERT.priv")
        if code == 0:
            print(color_green("......Success\n"))
            constants.cert_replaced = True
        else:
            print(color_red("......Failed\n"))
            logging.error("Failed to replace Machine SSL Certificate %s" % err)
            raise Exception("Failed to replace Machine SSL Certificate - %s" %err)
        update_trust_anchors()
        logging.info("Successfully replaced Machine SSL Certificate")
    except Exception as e:
        logging.error("Failed to replace Machine SSL Certificate %s" % e)
        print("..Failed to replace Machine SSL Certificate %s" % e)
        print(color_red("......Failed\n"))
        traceback.print_exc()
        sys.exit()

"""
Sub function to update the Trust Anchors of each endpoint in SSO Lookupservice, this function will be initiated by update_trust_anchors
This function uses ldapsearch and ldapmodify commands to update each endpoint which belongs to the VC where script is executed
"""
def update_endpoints(RegistrationClass,SSLTrustClass):
    logging.info("Updating Trust Anchors" + RegistrationClass)
    logging.info("Listing Services")
    new_machine_ssl = get_x509_from_file(constants.result_directory+"/MACHINE_SSL_CERT.crt")
    cert = crypto.dump_certificate(crypto.FILETYPE_PEM, new_machine_ssl).decode('utf-8').replace("\n","").replace("-----BEGIN CERTIFICATE-----","").replace("-----END CERTIFICATE-----","")
    cmd = '/usr/bin/ldapsearch -o ldif-wrap=no -h {0} -p 389 -s sub -b "cn=ServiceRegistrations,' \
          'cn=LookupService,cn={1},cn=Sites,cn=Configuration,{2}" -D "cn=administrator,' \
          'cn=users,{2}" -w "{3}" "(objectclass={4})" '.format(environment.DCNAME,environment.SITENAME,environment.DOMAINCN,environment.ldapssopassword,RegistrationClass)
    (code, result, err) = execute_cmd(cmd, True, None)
    if code != 0:
        logging.error("Listing the Endpoints failed to update the Trust Anchor, script cannot continue further - Error - %s" % err)
        return False
    endpointresults = (result.decode('utf-8').split('\n'))
    nodeendpoints = []
    i = 0
    while i < len(endpointresults):
        if endpointresults[i].startswith('dn: cn=Endpoint'):
            servicedn = endpointresults[i].split(',',1)[1]
            for j in range(i + 1, len(endpointresults)):
                i = i + 1
                if endpointresults[j].startswith('dn: cn=Endpoint') and servicedn not in nodeendpoints:
                    break
                elif endpointresults[j].startswith('vmwLKUPURI') and environment.PNID.lower() in endpointresults[j].lower():
                    if servicedn not in nodeendpoints:
                        nodeendpoints.append(servicedn)
                    break
                else:
                    continue
        else:
            i = i + 1
            continue
    for nodeendpoint in nodeendpoints:
        logging.info(nodeendpoint)
        cmd = '/usr/bin/ldapsearch -o ldif-wrap=no -h {0} -p 389 -s sub -b "{1}" -D "cn=administrator,' \
              'cn=users,{2}" -w "{3}" "(objectclass={4})" '.format(environment.DCNAME,nodeendpoint,environment.DOMAINCN,environment.ldapssopassword,RegistrationClass)
        (code, result, err) = execute_cmd(cmd, True, None)
        if code != 0:
            logging.error("Listing the Endpoints failed to update the Trust Anchor, script cannot continue further - Error - %s" % err)
            return False
        endpoints = (result.decode('utf-8').split('\n'))
        for endpoint in endpoints:
            if endpoint.startswith('dn: cn=Endpoint'):
                with open(constants.result_directory+"/servicereg.ldif", "w") as text_file:
                    text_file.write("{0}".format(endpoint))
                    text_file.write("\nchangetype: modify")
                    text_file.write("\nreplace: {0}".format(SSLTrustClass))
                    if SSLTrustClass == "vmwLKUPSslTrustAnchor":
                        text_file.write("\n{0}:< file:{1}".format(SSLTrustClass, constants.result_directory+"/MACHINE_SSL_CERT.der"))
                    else:
                        text_file.write("\n{0}: {1}".format(SSLTrustClass, cert))
                cmd = constants._LDAPMODIFY + ' -x -h {0} -p 389 -D "cn=administrator,cn=users,{1}" -w "{2}" -f {3}/servicereg.ldif '.format(environment.DCNAME,environment.DOMAINCN, environment.ldapssopassword,constants.result_directory)
                (code, result, err) = execute_cmd(cmd, True, None)
                if code != 0:
                    logging.error("Listing the Endpoints failed to update the Trust Anchor, script cannot continue further - Error - %s" % err)
                    return False
    return True

"""
Function to update the Trust Anchors in SSO Lookupservice during Machine SSL Certificate Replacement
It utilizes function update_endpoints to connect to VMDIR DB and read the values of each endpoint
"""
def update_trust_anchors():
    logging.info("Updating Trust Anchors")
    print("Updating SSL Trust of Services with new Machine SSL Certificate.\n...Waiting for Status")
    (code, result, err) = openssl_ops.convert_cert_der(constants.result_directory+"/MACHINE_SSL_CERT.crt",constants.result_directory+"/MACHINE_SSL_CERT.der")
    if code == 0:
        logging.info('Successfully Converted Machine SSL Certificate to DER Format for Trust Anchor Update')
    else:
        logging.error("Error while converting Machine SSL Certificate to DER format for Trust Anchor Update - %s" %err)
        print(color_red("......Failed\n"))
        raise Exception("Error while converting Machine SSL Certificate to DER format for Trust Anchor Update - %s" %err)
    if not (update_endpoints("vmwLKUPEndpointRegistration","vmwLKUPEndpointSslTrust")):
        logging.error("Error while updating SSL Trust Anchors in LookupService")
        print("...Error while updating SSL Trust Anchors in LookupService")
        print(color_red("......Failed\n"))
        raise Exception("Error while updating SSL Trust Anchors in LookupService")
    else:
        logging.info("Successfully updated Trust Anchor of endpoints in Lookup Service Registrations")
    #Update Legacy SSO Endpoints - sso:sts, sso:groupcheck and sso:admin
    if not (update_endpoints("vmwLKUPServiceEndpoint","vmwLKUPSslTrustAnchor")):
        logging.error("Error while updating SSL Trust Anchors in LookupService for SSO Legacy Endpoints")
        print("...Error while updating SSL Trust Anchors in LookupService for SSL Legacy Endpoints")
        print(color_red("......Failed\n"))
        raise Exception("Error while updating SSL Trust Anchors in LookupService for SSL Legacy Endpoints")
    else:
        print(color_green("......Success\n"))
        logging.info("Successfully updated Trust Anchor of Legacy endpoints in Lookup Service Registrations")

"""
Backup solution user certificate to the BACKUP_STORE
"""
def backup_solution_certs(user):
    logging.info("Taking backup of %s Solution User Certificate" %user)
    bkp_key_name = constants.result_directory + "/" + user + "_bkp.priv"
    bkp_cert_name = constants.result_directory + "/" + user + "_bkp.crt"
    bkp_alias = "bkp_" + user

    (code, result, err) = vecs_ops.get_cert_tofile(user, user, bkp_cert_name)
    (code, result, err) = vecs_ops.get_key_tofile(user, user, bkp_key_name)
    (code, result, err) = vecs_ops.delete_cert("BACKUP_STORE", bkp_alias)
    (code, result, err) = vecs_ops.create_cert("BACKUP_STORE", bkp_alias, bkp_cert_name, bkp_key_name)
    if code != 0:
        logging.error("Taking Backup of Solution User Failed with error - %s" %err)
    else:
        logging.info("Successfully took backup of %s Solution User Certificate" %user)

"""
Sub function to create new solution user certificate and replace the existing one
Uses function from vecscli, dircli and certool classes to perform the required tasks
"""
def replace_solution_certs_sub(user):
    logging.info("Replacing %s Solution User Certificate" %user)
    print("Replacing %s Solution User Certificate.\n...Waiting for Status" % user)
    user_key_name = constants.result_directory+ "/" + user + ".priv"
    user_pub_name = constants.result_directory+ "/" + user + ".pub"
    user_cert_name = constants.result_directory+ "/" + user + ".crt"
    user_csr_name = constants.result_directory+ "/" + user + ".csr"
    user_openssl_cfg_path = constants.result_directory+ "/" + user + "_openssl.cfg"

    try:
        machineid = environment.Machine_ID
        sol_ou_name = "mID-" + machineid
        if (constants.use_openssl_functions):
            certcfg_ops.create_cert_cfg_openssl(user_openssl_cfg_path, user,sol_ou_name)
            (code, result, err) = openssl_ops.gen_key(user_csr_name,user_key_name,user_openssl_cfg_path,constants.DEFAULT_KEY_SIZE)
            certcfg_ops.add_authKey_in_cfg(user_openssl_cfg_path)
            (code, result, err) = openssl_ops.gen_cert(constants.DEFAULT_VALIDITY, user_csr_name, user_cert_name, constants.vmca_root_path, constants.vmca_key_path, user_openssl_cfg_path)
        else:
            (code, result, err) = certool_ops.gen_key(user_key_name,user_pub_name, environment.DCNAME)
            (code, result, err) = certool_ops.gen_cis_cert(user, user_cert_name, user_key_name, environment.DCNAME)
        (code, result, err) = dircli_ops.service_update(user_cert_name, user, machineid, "Administrator@"+environment.DOMAIN, environment.ssopassword)
        if (code != 0):
            raise Exception("Failed to update the certificate of solution user in VMDIR - %s" %err)
        (code, result, err) = vecs_ops.delete_cert(user, user)
        (code, result, err) = vecs_ops.list_certs(user)
        logging.info(result)
        (code, result, err) = vecs_ops.create_cert(user, user, user_cert_name, user_key_name)
        if code == 0:
            logging.info(result)
            print(color_green("......Success\n"))
            constants.cert_replaced = True
        else:
            print(color_red("......Failed"))
            logging.info("Failed to update Solution User Certificate - %s - Error %s" %(user,err))
            print(color_red("Failed to update Solution User Certificate - %s - Error %s" %(user,err)))
            raise Exception("Failed to update Solution User Certificate - %s" %err)
    except Exception as e:
        logging.error("Failed to replace Solution User Certificate %s" % e)
        print("..Failed to replace Solution User Certificate %s" % e)
        print(color_red("......Failed\n"))
        traceback.print_exc()
        sys.exit()

"""
This function initiates various other sub functions for the Solution User certificate replacement
It calls backup_solution_certs to take backup of Solution user Certificates
And, calls replace_solution_certs_sub to create and replace solution user certificate
If the store name is vpxd-extension:
 it also calls the function update_extension_in_vc_database to update the Certificate in VCDB
"""
def replace_solution_user_certificate(stores):
    logging.info("Replacing Solution Users Certs")
    for store_name in constants.store_names:
        if store_name in stores:
            backup_solution_certs(store_name)
            replace_solution_certs_sub(store_name)
            if store_name == "vpxd-extension":
                extension_cert_path = constants.result_directory+"/vpxd-extension.crt"
                update_extension_in_vc_database(extension_cert_path)
    logging.info("Successfully replaced Solution User Certificates")

"""
Update VPXD extensions independently
"""
def update_vpxd_extensions(store="vpxd-extension"):
    updated_vcdb = False
    extensions_auto_service_restart = False
    logging.info("Updating certificate for extensions registered in vpxd")
    extension_cert_path = constants.result_directory+"/vpxd-extension-cert.crt"
    vecs_ops.get_cert_tofile("vpxd-extension", "vpxd-extension", extension_cert_path)
    updated_vcdb = update_extension_in_vc_database(extension_cert_path)
    if (updated_vcdb):
        print("Restarting the Services %s" %constants.extension_type)
        logging.info("Restarting the Services %s" %constants.extension_type)
        for extension in constants.extension_type:
            service_running_status = check_service_runstate(extension)
            if service_running_status == "RUNNING":
                print("...Restarting %s Service" % extension)
                stop_service(extension)
                start_service(extension)
            elif service_running_status in ["STOPPED"]:
                print("...Skipping service restart of %s as service is in STOPPED state" % extension)
            else:
                print("...Please restart %s service manually using 'service-control' utility" %extension)
            logging.info("Successfully updated certificate for VPXD extensions")
    else:
        print("Skipping Service restart as the script did not update thumbprint for any extensions ")
        logging.warning("Skipping Service restart as script did not update thumbprint for any extensions ")

"""
VPXD extensions rbd,eam and impagebuilder needs to be updated in VCDB while replacing vpxd-extension certificate
These services uses vpxd-extension certificate to connect to VPXD.
In this function, vpxd-extension Thumbprint is updated in VPX_EXT table,
DB update method is used because Certificate expiration, VPXD will not be not be running and utilizing updateExtensionCertInVC.py script will fail
"""
def update_extension_in_vc_database(certificate_path):
    logging.info("Updating Extensions in VPXD")
    print("Updating Thumbprint of Extensions in VPXD.\n...Waiting for Status")
    (code, result, err) = openssl_ops.get_fingerprint(certificate_path)
    if code != 0:
        logging.info("Failed to read thumbprint of vpxd-extension certificate, however script will try to continue - %s\n Error - %s" %(cmd, err.decode('utf-8')))
    else:
        thumbprint = (result.decode('utf-8').split("=")[1].replace('\n',''))
    logging.info("vpxd-extension certificate thumbprint is " + thumbprint)
    status = existing_tumbprint = ""
    db_update = False
    if thumbprint:
        for extension in constants.extensions:
            cmd = '/opt/vmware/vpostgres/current/bin/psql -d VCDB -U postgres -t -c "SELECT THUMBPRINT FROM VPX_EXT WHERE EXT_ID=\'{0}\'" '.format(extension)
            (code, result, err) = execute_cmd(cmd, True, None)
            if code==0:
                existing_tumbprint = result.decode("UTF-8").strip()
            if thumbprint in existing_tumbprint:
                status = "Success"
                print("....Skipping thumprint update for extension %s as VPXD already have the correct thumbprint" %extension)
                logging.warning("Skipping thumprint update for extension %s as the VPXD have the correct thumbprint" %extension)
            else:
                cmd = '/opt/vmware/vpostgres/current/bin/psql -d VCDB -U postgres -c "UPDATE VPX_EXT SET THUMBPRINT=\'{0}\' WHERE EXT_ID=\'{1}\'" '.format(thumbprint,extension)
                logging.info("Updating %s in VPXD" %extension)
                print("....Updating thumbprint of %s" %extension)
                logging.info(cmd)
                (code, result, err) = execute_cmd(cmd, True, None)
                if code==0:
                    status = "Success"
                    db_update = True
                else:
                    status = "Failed"
    if status == "Success":
        print(color_green("......Success\n"))
        logging.info("Successfully updated Certificate Thumbprint in VPXD Database")
    else:
        print(color_red("......Failed"))
        logging.warning("Failed to update the extension rbd,eam and impagebuilder in VPXD, however script will continue, you may manually update the thumbprint using KB https://kb.vmware.com/s/article/57379")
        print(color_red("Failed to update the extension rbd,eam and impagebuilder in VPXD, however script will continue, you may manually update the thumbprint using KB https://kb.vmware.com/s/article/57379"))
    return db_update

"""
Certificate in data-encipherment store is used to encrypt the Administrator password used in Guest Customization Templates.
This function will renew the data-encipherment certificate using the same Private Key
"""
def replace_data_encipherment_certificate(stores):
    logging.info("Replacing data-enciphement Certificate")
    if 'data-encipherment' in stores:
        print("Replacing data-enciphement Certificate.\n...Waiting for Status")
        (code, result, err) = vecs_ops.get_cert_tofile("data-encipherment", "data-encipherment", "/var/tmp/data-encipherment_bkp.crt")
        (code, result, err) = vecs_ops.get_key_tofile("data-encipherment", "data-encipherment", "/var/tmp/data-encipherment_bkp.priv")
        if code == 0:
            logging.info("Checking data-encipherment Certificate Validity")
            (encipherment_cert_validity, encipherment_cert_validity_days) = check_certificate_validity("/var/tmp/data-encipherment_bkp.crt")
            if (encipherment_cert_validity and encipherment_cert_validity_days.days < 0) or constants.force_encipherment_cert:
                logging.info("Proceeding with data-encipherment Certificate as it is expired or force replace is True")
                (code, result, err) = vecs_ops.delete_cert("data-encipherment", "data-encipherment")
                (code, result, err) = certool_ops.gen_cis_cert('data-encipherment', "/var/tmp/data-encipherment.crt", "/var/tmp/data-encipherment_bkp.priv", environment.DCNAME)
                if code == 0:
                    print(color_green("......Success\n"))
                    constants.cert_replaced = True
                    logging.info("Successfully replaced data-encipherment Certificate")
                else:
                    logging.error("Failed to replace data-encipherment certificate using the same private key")
                    (code, result, err) = vecs_ops.create_cert("data-encipherment", "data-encipherment", "/var/tmp/data-encipherment_bkp.crt", "/var/tmp/data-encipherment_bkp.priv")
                    print(color_red("Failed to replace data-encipherment certificate, script will continue and you may follow KB https://kb.vmware.com/s/article/88548 to replace this certificate if it is expired."))
                    print(color_red("......Failed\n"))
            else:
                logging.info("Script did not attempt data-encipherment certificate as it is not expired")
                print(color_green("......Script did not attempt data-encipherment certificate replacement as it is not expired (valid till-%s), please refer https://kb.vmware.com/s/article/88548.\n......It is not recommended to replace this Certificate if it is not expired, you may force it using argument (--force_encipherment_replace True) if it is really required" %encipherment_cert_validity))
                print(color_green("......Skipped"))
        else:
            logging.error("Failed to export data-encipherment certificate or private key")
            print(color_red("Failed to replace data-encipherment certificate, script will continue and you may follow KB https://kb.vmware.com/s/article/88548 to replace this certificate if it is expired."))
            print(color_red("......Failed\n"))
    else:
        logging.info("This vCenter Server does not have data-enciphement VECS store, hence not replacing the Certificate. This store is available from vCenter Server 6.7 onwards")

"""
In upgraded environments, there will be an additional store named STS_INTERNAL_SSL_CERT to store the Certificate for LookupService (port 7444)
Currently certificate-manager utility does not handle this store.
This function will replace the Cert and Key in STS_INTERNAL_SSL_CERT with the certificate and key stored in MACHINE_SSL_CERT
"""
def replace_lookupservice_certificate():
    logging.info("Replacing LookupService Certificate in STS_INTERNAL_SSL_CERT")
    print("Replacing LookupService SSL Cert.\n...Waiting for Status")
    (code, result, err) = vecs_ops.delete_cert("STS_INTERNAL_SSL_CERT", "__MACHINE_CERT")
    if code != 0:
        logging.error("Failed to delete the entries from VECS store STS_INTERNAL_SSL_CERT, however script will try to continue")
        print(color_red("Failed to delete the entries from VECS store STS_INTERNAL_SSL_CERT, however script will try to continue"))
    (code, result, err) = vecs_ops.get_cert_tofile("MACHINE_SSL_CERT", "__MACHINE_CERT", constants.result_directory+"/MACHINE_SSL_CERT.crt")
    if code != 0:
        logging.error("Reading the Machine SSL Certificate failed with error - %s" % err)
        raise Exception("Failed to read the Machine SSL Certificate - %s" %err)
    (code, result, err) = vecs_ops.get_key_tofile("MACHINE_SSL_CERT", "__MACHINE_CERT", constants.result_directory+"/MACHINE_SSL_CERT.priv")
    if code != 0:
        logging.error("Reading the Machine SSL private key failed with error - %s" % err)
        raise Exception("Failed to read the Machine SSL private key - %s" %err)    
    (code, result, err) = vecs_ops.create_cert("STS_INTERNAL_SSL_CERT", "__MACHINE_CERT", constants.result_directory+"/MACHINE_SSL_CERT.crt", constants.result_directory+"/MACHINE_SSL_CERT.priv")
    if code == 0:
        print(color_green("......Success\n"))
        constants.cert_replaced = True
        logging.info("Successfully replaced LookupService Certificate")
    else:
        logging.error("Failed to create new certificate entry in store STS_INTERNAL_SSL_CERT, terminating the script")
        print(color_red("Failed to create new certificate entry in store STS_INTERNAL_SSL_CERT, script is terminating"))
        print(color_red("......Failed\n"))
        raise Exception("Failed to update LookupService Certificate - %s" %err)

"""
This function will replace the SMS self signed certificate only if it is expired
"""
def replace_sms_certificate(stores):
    logging.info("Replacing SMS Certificate if expired")
    print("\nReplacing SMS Certificate.\n...Waiting for Status")
    found_expired_sms_cert = False
    error_verifying_sms_cert = False
    sms_cert_removal_status = False
    if 'SMS' in stores:
        alias = 'sms_self_signed'
        (code, result, err) = vecs_ops.list_certs("SMS")
        if code == 0 and alias in result.decode('utf-8'):
            cert_file = constants.result_directory + "/" + alias + ".crt"
            backup_filename = '/var/tmp'  + "/" + alias + ".crt"
            (code, result, err) = vecs_ops.get_cert_tofile('SMS', alias, cert_file)
            if code == 0:
                if (is_cert_expired(cert_file)):
                    found_expired_sms_cert = True
                    logging.info("Removing expired SMS Certificate")
                    shutil.copy(cert_file, backup_filename)
                    (code, result, err) = vecs_ops.delete_cert('SMS', alias)
                    if code == 0:
                        logging.info("Backup of expired SMS certificate saved to %s" %backup_filename)
                        print("....Backup of expired SMS certificate saved to %s" %backup_filename)
                        sms_cert_removal_status = True
                    else:
                        sms_cert_removal_status = False
            else:
                error_verifying_sms_cert = True
        else:
            error_verifying_sms_cert = True

    if not found_expired_sms_cert:
        logging.info("NO Expired Certs in SMS store")
        print(color_green("....NO Expired Certs in SMS store"))
        print(color_green("......Skipped\n"))
    elif(sms_cert_removal_status):
        print(color_green("......Success\n"))
        constants.cert_replaced = True
        logging.info("Successfully removed expired SMS certificate")
    elif(error_verifying_sms_cert):
        logging.error("Failed to verify SMS Certificate, you may follow KB https://kb.vmware.com/s/article/2146011 to remove it manually")
        print(color_red("Failed to verify SMS Certificate, you may follow KB https://kb.vmware.com/s/article/2146011 to remove it manually"))
        print(color_red("......Failed\n"))
    else:
        logging.error("Failed to verify SMS Certificate, you may follow KB https://kb.vmware.com/s/article/2146011 to remove it manually")
        print(color_red("Failed to verify SMS Certificate, you may follow KB https://kb.vmware.com/s/article/2146011 to remove it manually"))
        print(color_red("......Failed\n"))
        sys.exit()

"""
This function will remove all the expired certificates from TRUSTED_ROOTS VECS store.
It will not perform any replace operation, just will unpublish expired Root Certificates
"""
def remove_expired_certs_from_trusted_roots():
    logging.info("Removing Expired Certificates from TRUSTED_ROOTS store")
    print("\nRemoving Expired Certificates from TRUSTED_ROOTS store.\n...Waiting for Status")
    error_verifying_trusted_roots = False
    trusted_removal_status = False
    found_expired_root_cert = False
    (code, result, err) = vecs_ops.list_certs("TRUSTED_ROOTS")
    if code == 0 and (result):
        trusted_certs = result.decode('utf-8')
        root_aliases = []
        if ('Alias' in trusted_certs):
            trusted_root_entries = trusted_certs.split('\n')
            for value in trusted_root_entries:
                if 'Alias :' in value:
                    root_aliases.append(value.replace('Alias :\t',''))
        for alias in root_aliases:
            cert_file = constants.result_directory + "/" + alias + ".crt"
            backup_filename = '/var/tmp'  + "/" + alias + ".crt"
            (code, result, err) = vecs_ops.get_cert_tofile('TRUSTED_ROOTS', alias, cert_file)
            if code == 0:
                if (is_cert_expired(cert_file)):
                    found_expired_root_cert = True
                    logging.info("Un-publishing Expired Root Certificate with Alias %s" %alias)
                    shutil.copy(cert_file, backup_filename)
                    (code, result, err) = dircli_ops.trustedcert_unpublish(cert_file, "Administrator", environment.ssopassword)
                    if code == 0:
                        logging.info("Backup of expired root certificate saved to %s" %backup_filename)
                        print("....Backup of expired root certificate saved to %s" %backup_filename)
                        trusted_removal_status = True
                    else:
                        trusted_removal_status = False
            else:
                error_verifying_trusted_roots = True
    else:
        error_verifying_trusted_roots = True

    if not found_expired_root_cert:
        logging.info("NO Expired Certs in Trusted_Roots store")
        print(color_green("....NO Expired Certs in Trusted_Roots store"))
        print(color_green("......Skipped\n"))
    elif(trusted_removal_status):
        print(color_green("......Success\n"))
        constants.cert_replaced = True
        logging.info("Successfully removed expired root certificates")
    elif(error_verifying_trusted_roots):
        logging.error("Failed to verify some Root Certificates, you may follow KB https://kb.vmware.com/s/article/2146011 to remove it manually")
        print(color_red("Failed to verify some Root Certificates, you may follow KB https://kb.vmware.com/s/article/2146011 to remove it manually"))
        print(color_red("......Failed\n"))
    else:
        logging.error("Failed to remove expired Root Certificates from TRUSTED_ROOTS store, you may follow KB https://kb.vmware.com/s/article/2146011 to remove it manually")
        print(color_red("Failed to remove expired Root Certificates from TRUSTED_ROOTS store, you may follow KB https://kb.vmware.com/s/article/2146011 to remove it manually"))
        print(color_red("......Failed\n"))

"""
Check for Non-CA Certificate
"""
def is_ca_cert(certificate_path):
    logging.info("Checking CA Status of the Certificate - %s" %certificate_path)
    x509_cert = get_x509_from_file(certificate_path)
    ca_cert = False
    count = 0
    try:
        while (count < x509_cert.get_extension_count()):
            if ( ("CA:TRUE" in str(x509_cert.get_extension(count))) or ("Certificate Sign" in str(x509_cert.get_extension(count))) ) :
                ca_cert = True
                break
            count+=1
        if ca_cert:
            logging.info("Cert %s is CA Certificate" %certificate_path)
            return("ca") 
        else:
            logging.info("Cert %s is Non CA Certificate" %certificate_path) 
            return("non-ca")
    except Exception as e:
        msg = 'Error while fetching certificate extensions : {0}'.format(e)
        logging.error(msg)
        return("Unknown")
        
"""
This function will remove all Non-CA certificates from TRUSTED_ROOTS VECS store.
"""
def remove_non_ca_certs_from_trusted_roots():
    logging.info("Removing Non-CA Certificates from TRUSTED_ROOTS store")
    print("\nRemoving Non-CA Certificates from TRUSTED_ROOTS store.\n...Waiting for Status")
    error_verifying_trusted_roots = False
    non_ca_removal_status = False
    found_non_ca_cert = False
    (code, result, err) = vecs_ops.list_certs("TRUSTED_ROOTS")
    if code == 0 and (result):
        trusted_certs = result.decode('utf-8')
        root_aliases = []
        if ('Alias' in trusted_certs):
            trusted_root_entries = trusted_certs.split('\n')
            for value in trusted_root_entries:
                if 'Alias :' in value:
                    root_aliases.append(value.replace('Alias :\t',''))
        for alias in root_aliases:
            cert_file = constants.result_directory + "/" + alias + ".crt"
            backup_filename = '/var/tmp'  + "/" + alias + ".crt"
            (code, result, err) = vecs_ops.get_cert_tofile('TRUSTED_ROOTS', alias, cert_file)
            if code == 0:
                non_ca_cert = is_ca_cert(cert_file)
                if (non_ca_cert == "non-ca"):
                    found_non_ca_cert = True
                    logging.info("Un-publishing Non CA Certificate with Alias %s" %alias)
                    shutil.copy(cert_file, backup_filename)
                    (code, result, err) = dircli_ops.trustedcert_unpublish(cert_file, "Administrator", environment.ssopassword)
                    if code == 0:
                        logging.info("Backup of Non CA Certificate saved to %s" %backup_filename)
                        print("....Backup of Non CA Certificate saved to %s" %backup_filename)
                        non_ca_removal_status = True
                    else:
                        non_ca_removal_status = False
                elif (non_ca_cert == "Unknown"):
                    error_verifying_trusted_roots = True
            else:
                error_verifying_trusted_roots = True
    else:
        error_verifying_trusted_roots = True

    if not found_non_ca_cert:
        logging.info("Non-CA Certs doesn't exist in Trusted_Roots store")
        print(color_green("....Non-CA Certs doesn't exist in Trusted_Roots store"))
        print(color_green("......Skipped\n"))
    elif(non_ca_removal_status):
        print(color_green("......Success\n"))
        constants.cert_replaced = True
        logging.info("Successfully removed Non-CA certificates")
    elif(error_verifying_trusted_roots):
        logging.error("Failed to verify some Root Certificates, you may follow KB https://kb.vmware.com/s/article/2146011 to remove it manually")
        print(color_red("Failed to verify some Root Certificates, you may follow KB https://kb.vmware.com/s/article/2146011 to remove it manually"))
        print(color_red("......Failed\n"))
    else:
        logging.error("Failed to remove Non-CA Certificates from TRUSTED_ROOTS store, you may follow KB https://kb.vmware.com/s/article/2146011 to remove it manually")
        print(color_red("Failed to remove Non-CA Certificates from TRUSTED_ROOTS store, you may follow KB https://kb.vmware.com/s/article/2146011 to remove it manually"))
        print(color_red("......Failed\n"))

"""
Read the Certificate Validity
"""
def get_cert_details(store, alias, cert_file):
    (code, result, err) = vecs_ops.get_cert_tofile(store, alias, cert_file)
    if code == 0:
        (cert_validity, cert_valid_days) = check_certificate_validity(cert_file)
        cert_expired = is_cert_expired(cert_file)
        return (cert_validity, cert_expired)
    else:
        return(False,False)


"""
Verify the validity of all the existing Certs
"""
def read_all_certs():
    from prettytable import PrettyTable
    Y = "\033[0;33;40m"
    C = "\033[0;36;40m"
    N = "\033[0m"
    R = "\033[0;31;40m" #RED
    G = "\033[0;32;40m" # GREEN
    constants.expired_vmca = constants.expired_sts = constants.expired_machinessl = constants.expired_solutionusers = constants.expired_lookupservice = constants.expired_dataencipherment = constants.expired_sms = constants.expired_trustedroots = False
    cert_details = PrettyTable(['CertificateType', 'Validity(UTC)'])
    root_cert_details = PrettyTable(['TRUSTED_ROOTS_Alias', 'Validity(UTC)', 'Type'])
    store_list = get_vecs_stores()
    if not store_list:
        logging.info("Failed to list the VECS Stores to show the Certificate Validity, script will Continue...")
    else:
        store_list = store_list.split('\n')
        for store in store_list:
            if store in ["MACHINE_SSL_CERT"]:
                cert_file = constants.result_directory + "/current_machine_ssl" + ".crt"
                (cert_validity, cert_expired) = get_cert_details(store,"__MACHINE_CERT",cert_file)
                if (cert_validity):
                    if (cert_expired):
                        constants.expired_machinessl = True
                        cert_details.add_row([C + "MACHINE_SSL_CERT" + N, R + cert_validity.strftime('%b %d %H:%M:%S %Y') + N])
                    else:
                        cert_details.add_row([C + "MACHINE_SSL_CERT" + N, G + cert_validity.strftime('%b %d %H:%M:%S %Y') + N])
            elif store in constants.store_names:
                cert_file = constants.result_directory + "/current_" + store + ".crt"
                (cert_validity, cert_expired) = get_cert_details(store,store,cert_file)
                if (cert_validity):
                    if (cert_expired):
                        constants.expired_solutionusers = True
                        cert_details.add_row([C + store + N, R + cert_validity.strftime('%b %d %H:%M:%S %Y') + N])
                    else:
                        cert_details.add_row([C + store + N, G + cert_validity.strftime('%b %d %H:%M:%S %Y') + N])
            elif store in ["data-encipherment"]:
                cert_file = constants.result_directory + "/current_" + store + ".crt"
                (cert_validity, cert_expired) = get_cert_details(store,store,cert_file)
                if (cert_validity):
                    if (cert_expired):
                        constants.expired_dataencipherment = True
                        cert_details.add_row([C + store + N, R + cert_validity.strftime('%b %d %H:%M:%S %Y') + N])
                    else:
                        cert_details.add_row([C + store + N, G + cert_validity.strftime('%b %d %H:%M:%S %Y') + N])
            elif store in ["STS_INTERNAL_SSL_CERT"]:
                cert_file = constants.result_directory + "/current_" + store + ".crt"
                (cert_validity, cert_expired) = get_cert_details(store,"__MACHINE_CERT",cert_file)
                if (cert_validity):
                    if (cert_expired):
                        constants.expired_lookupservice = True
                        cert_details.add_row([C + store + N, R + cert_validity.strftime('%b %d %H:%M:%S %Y') + N])
                    else:
                        cert_details.add_row([C + store + N, G + cert_validity.strftime('%b %d %H:%M:%S %Y') + N])
            elif store in ["SMS"]:
                cert_file = constants.result_directory + "/current_" + store + ".crt"
                (cert_validity, cert_expired) = get_cert_details(store,"sms_self_signed",cert_file)
                if (cert_validity):
                    if (cert_expired):
                        constants.expired_sms = True
                        cert_details.add_row([C + store + N, R + cert_validity.strftime('%b %d %H:%M:%S %Y') + N])
                    else:
                        cert_details.add_row([C + store + N, G + cert_validity.strftime('%b %d %H:%M:%S %Y') + N])
            elif store in ["TRUSTED_ROOTS"]:
                (code, result, err) = vecs_ops.list_certs_text(store)
                for line in result.decode('utf-8').split('\n'):
                    if re.search("Alias :", line):
                        alias = line.replace("Alias :","").strip()
                        cert_file = constants.result_directory + "/current__root" + alias + ".crt"
                        (cert_validity, cert_expired) = get_cert_details(store,alias,cert_file)
                        ca_type = is_ca_cert(cert_file)
                        if ca_type == "ca":
                            ca_type = "CA"
                        elif (ca_type == "non-ca"):
                            ca_type = "Non-CA"
                        else:
                            ca_type = "Error Fetching Cert Details"
                        if (cert_validity):
                            if (cert_expired):
                                #cert_details.add_row([C + "TRUSTED_ROOTS-Alias-" + alias + N, R + cert_validity.strftime('%b %d %H:%M:%S %Y') + N])
                                constants.expired_trustedroots = True
                                root_cert_details.add_row([C + alias + N, R + cert_validity.strftime('%b %d %H:%M:%S %Y') + N, C + ca_type + N])
                            else:
                                #cert_details.add_row([C + "TRUSTED_ROOTS-Alias-" + alias + N, G + cert_validity.strftime('%b %d %H:%M:%S %Y') + N])
                                root_cert_details.add_row([C + alias + N, G + cert_validity.strftime('%b %d %H:%M:%S %Y') + N, C + ca_type + N])
        (sts_validity,sts_valid_days) = check_sts_certificate()
        if (sts_validity):
            if sts_valid_days.days > 0:
                cert_details.add_row([C + "Signing Cert (STS)" + N, G + sts_validity.strftime('%b %d %H:%M:%S %Y') + N])
            else:
                constants.expired_sts = True
                cert_details.add_row([C + "Signing Cert (STS)" + N, R + sts_validity.strftime('%b %d %H:%M:%S %Y') + N])
        else:
            cert_details.add_row([C + "Signing Cert (STS)" + N, R + "Error Fetching Cert Details" + N])
        if (os.path.exists(constants.vmca_root_path)):
            (vmca_validity,vmca_valid_days) = check_certificate_validity(constants.vmca_root_path)
            if vmca_valid_days.days < 0:
                constants.expired_vmca = True
    return (cert_details, root_cert_details)


"""
Master function to reset all certificates on vCenter Server (root/sts/machine ssl/lookupservice and solution user certificates)
This will call various sub functions to replace the certificates
"""
def replace_certificates(args,argparser):
    #Start time used to calculate the execution time
    start_time = time.time()

    display_warning_message = True

    #Check unsupported replacement
    if unsupported_scenario():
        logging.info("This script does not support Certificate replacement on this node")
        sys.exit()
    
    #Reading SSO Password
    if (constants.silent_execution):
        logging.info("This is a Silent execution")
        environment.ssopassword = args.password
    else:
        environment.ssopassword = getpass.getpass(prompt='Please enter the password for administrator@%s to proceed further : ' % environment.DOMAIN)

    #set ldappassword to escapte $ symbol
    environment.ldapssopassword = environment.ssopassword.replace("$","\\$")
    environment.ldapssopassword = environment.ldapssopassword.replace("`","\\`")
    environment.ldapssopassword = environment.ldapssopassword.replace('"','\\"')

    (certs_validity, root_certificates_validity) = read_all_certs()

    #Initialize Flags to identify the type of Certificates to replace based on CLI arguments
    REPLACE_ROOT = REPLACE_MACHINESSL = REPLACE_STS = REPLACE_SOLUTIONUSERS = REPLACE_DATAENCIPHERMENT = REPLACE_LOOKUPSERVICE = REMOVE_TRUSTEDROOTS = REPLACE_SMS = REMOVE_NON_CA_TRUSTEDROOTS = UPDATE_VPXD_EXTENSIONS = False
    if args.certType == 'machinessl':
        REPLACE_MACHINESSL = True
    elif args.certType == 'sts':
        REPLACE_STS = True
    elif args.certType == 'lookupservice':
        constants.replace_only_lookupservice = True
        REPLACE_LOOKUPSERVICE = True
    elif args.certType == 'solutionusers':
        REPLACE_SOLUTIONUSERS = True
    elif args.certType == 'data-encipherment':
        REPLACE_DATAENCIPHERMENT = True
    elif args.certType == 'sms':
        REPLACE_SMS = True
        constants.replace_only_sms_roots = True
    elif args.storeType in ['trusted_roots', 'trustedroots', 'TRUSTED_ROOTS', 'Trusted_Roots', 'Trusted_roots', 'TRUSTEDROOTS'] and args.certType.lower() in ['expired', 'expired_only', 'expiredonly']:
        REMOVE_TRUSTEDROOTS = True
        constants.remove_only_trusted_roots = True
    elif args.storeType in  ['trusted_roots', 'trustedroots', 'TRUSTED_ROOTS', 'Trusted_Roots', 'Trusted_roots', 'TRUSTEDROOTS'] and args.certType.lower() in ['nonca', 'non-ca']:
        REMOVE_NON_CA_TRUSTEDROOTS = True
        constants.remove_nonca_trusted_roots = True
    elif args.ExtensionType:
        if args.ExtensionType.lower() in ['all', 'eam', 'rbd','imagebuilder']:
            UPDATE_VPXD_EXTENSIONS = True
            constants.update_only_vpxd_extensions = True
            if args.ExtensionType.lower() == "eam":
                constants.extension_type = ["eam"]
                constants.extensions = ["com.vmware.vim.eam"]
            elif args.ExtensionType.lower() == "rbd":
                constants.extension_type = ["rbd"]
                constants.extensions = ["com.vmware.rbd"]
            elif args.ExtensionType.lower() == "imagebuilder":
                constants.extension_type = ["imagebuilder"]
                constants.extensions = ["com.vmware.imagebuilder"]
            else:
                constants.extension_type = ['eam', 'rbd' , 'imagebuilder']
    elif args.certType == 'root':
        REPLACE_ROOT = True
        REPLACE_MACHINESSL = True
        REPLACE_SOLUTIONUSERS = True
        REPLACE_LOOKUPSERVICE = True
        REMOVE_TRUSTEDROOTS = True
    elif args.certType == 'all':
        REPLACE_ROOT = True
        REPLACE_MACHINESSL = True
        REPLACE_STS = True
        REPLACE_SOLUTIONUSERS = True
        REPLACE_LOOKUPSERVICE = True
        REPLACE_DATAENCIPHERMENT = True
        REMOVE_TRUSTEDROOTS = True
        REPLACE_SMS = True
    elif args.certType == 'expired_only':
        if (constants.expired_vmca or constants.expired_sts or constants.expired_machinessl or constants.expired_solutionusers or constants.expired_lookupservice or constants.expired_dataencipherment or constants.expired_sms or constants.expired_trustedroots):
            REPLACE_ROOT = constants.expired_vmca
            REPLACE_STS = constants.expired_sts
            REPLACE_MACHINESSL = constants.expired_machinessl
            REPLACE_SOLUTIONUSERS = constants.expired_solutionusers
            REPLACE_LOOKUPSERVICE = constants.expired_lookupservice
            REPLACE_DATAENCIPHERMENT = constants.expired_dataencipherment
            REPLACE_SMS = constants.expired_sms
            REMOVE_TRUSTEDROOTS = constants.expired_trustedroots
        else:
            print("\nValidity of Certificates:")
            if (constants.remove_only_trusted_roots or constants.remove_nonca_trusted_roots):
                print(root_certificates_validity)
            else:
                print(certs_validity)
                print(root_certificates_validity)
            logging.warning("There are NO EXPIRED CERTIFICATES on this vCenter Server, hence DID NOT replace any Certificates.\nIf you still want to replace the certificates, use any other arguments such as --certType all")
            print("\nThere are NO EXPIRED CERTIFICATES on this vCenter Server, hence DID NOT replace any Certificates.\nIf you still want to replace the certificates, use any other arguments such as --certType all")
            sys.exit(1)
    else:
        print("Please execute the script with valid arguments\n")
        argparser.print_help()
        sys.exit(1)
    
    if (constants.remove_nonca_trusted_roots) or (constants.remove_only_trusted_roots):
        display_warning_message = False
    elif constants.update_only_vpxd_extensions:
        cert_replace_message = (
        "\nThis script will update the certificate thumbprint for VPXD extensions :\n"
        "\t1. Services {0} needs to be restarted after updating the thumbprint\n"
        ).format(constants.extension_type)
    else:
        cert_replace_message = (
        "\nThis script will replace the certificates on vCenter Server, please read below important points :\n"
        "\t1. Services needs to be restarted for certificate replacement, you may do it manually or let the script do it\n"
        "\t2. Services on partner VCs in Linked Mode also needs to be restarted after replacing STS (Secure Token Signing) certificate, as VCs in ELM uses same STS Certificate\n"
        "\t   Note: Point 2 is Not Applicable for vCenter Server 8.0, as service restart is not required for STS Certificate Replacement on 8.0.\n"
        "\t3. Please make sure you have taken OFFLINE SNAPSHOT of all the VCs in the Linked Mode before continuing with the Certificate replacement\n"
        ) 

    #Displaying the Cert validity before replacement
    if not (constants.update_only_vpxd_extensions):
        if (constants.remove_only_trusted_roots or constants.remove_nonca_trusted_roots):
            print(root_certificates_validity)
        else:
            print(certs_validity)
            print(root_certificates_validity)

    #Initial messaging on the console
    if (display_warning_message):
        print(cert_replace_message)
        if not (constants.silent_execution):
            Customeragreement = constants.inputfunction("\nPlease read above points and enter YES to proceed further [[Yes/yes/YES/Y/y]] ? ")
            if Customeragreement.lower() not in ['y','Y','Yes','YES','yes','yES','yeS']:
                print(color_red("\nScript Terminated based on user selection"))
                logging.error("Script Terminated based on user selection")
                sys.exit()
            else:
                logging.info("Entered YES to proceed with operation")
            
    #Read Deployment Type and FQDN Type
    print("\nReading Hostname Type & Deployment Type.\n...Waiting for Status")
    if (get_deployment_parameters()):
        print(color_green("......Success\n"))
    else:
        logging.error("Unable to read the Host Name Type and/or Deployment Type vCenter Server, script is terminating")
        print(color_red("Unable to read the Host Name and/or Deployment Type of vCenter Server.\nPlease check availability of files \'system.hostname.type\' & \'deployment.node.type\' under \'/etc/vmware/install-defaults\' folder and retry."))
        print(color_red("......Failed\n"))
        sys.exit()

    #Customized openssl functions to create the certificate with user specified Validity and Key Size will not work on Management nodes (VC pointing to external PSC), hence ignoring the values
    if environment.deployment_type == "management" and (args.validityDays or args.keySize):
        logging.warning("You have passed validityDays or keySize arguments to the script, these arguments will be ignored for Management Nodes (VC pointing to External PSC)")
        print(color_red("You have passed validityDays or keySize arguments to the script, these arguments will be ignored for Management Nodes (VC pointing to External PSC)"))
        constants.use_openssl_functions = False

    #Performs pre-check to start the required services for certificate replacement, also verifies the SSO Admin password
    precheck()

    #Initialize the Certificate fields such as Country, Organlization etc
    if not (constants.remove_only_trusted_roots or constants.remove_nonca_trusted_roots or constants.update_only_vpxd_extensions):
        certcfg_ops.initialize_cert_fields()

    #User input for replacing STS Certificate if the Certificate is valid more than the mincertvalidity defined in the script(it's defined as 365 days)
    sts_replace_flag = False
    if REPLACE_STS:
        if not (constants.silent_execution):
            (sts_validity,sts_valid_days) = check_sts_certificate()
            if (sts_validity):
                if (sts_valid_days.days > constants.mincertvalidity):
                    sts_user_input = constants.inputfunction("STS (Token Signing) Certificate is Valid for more than 1 YEAR (Till - " + sts_validity.strftime('%Y-%m-%d-%H:%M:%SZ') + "). Do you really want to replace STS Certificate [Y/N] ? ")
                    if sts_user_input.lower() in ['y','Y','Yes','YES','yes','yES','yeS']:
                        logging.info("Script will replace STS Certificate based on User Input")
                        sts_replace_flag = True
                    else:
                        logging.info("Not replacing STS Certificate based on User Input")
                else:
                    sts_replace_flag = True
            else:
                sts_replace_flag = True
        else:
            logging.info("This is a silent execution, so forcefully replacing STS Certificate without verifying the existing certificate validity")
            sts_replace_flag = True
    #User input for replacing VMCA Root Certificate if the Certificate is valid more than the mincertvalidity defined in the script(it's defined as 365 days)
    vmca_replace_flag = False
    if REPLACE_ROOT:
        if not (constants.silent_execution):
            (vmca_validity,vmca_valid_days) = check_certificate_validity(constants.vmca_root_path)
            if vmca_valid_days.days > constants.mincertvalidity:
                rootinput = constants.inputfunction("\nVMCA Root Certificate is valid for more than 1 YEAR (Till - " + vmca_validity.strftime('%Y-%m-%d-%H:%M:%SZ') + "), Do you really want to replace Root Certificate [Y/N] ? ")
                if rootinput.lower() in ['y','Y','Yes','YES','yes','yES','yeS']:
                    logging.info("Script will replace VMCA Root Certificate based on User Input")
                    vmca_replace_flag = True
                else:
                    logging.info("Not replacing VMCA Root Certificate based on User Input")
            else:
                logging.info("VMCA Certificate is already expired")
                vmca_replace_flag = True
        else:
            logging.info("This is a silent execution, so forcefully replacing Root Certificate without verifying the existing certificate validity")
            vmca_replace_flag = True

    if not (vmca_replace_flag):
        if not (constants.silent_execution):
            if is_cert_expired(constants.vmca_root_path):
                rootinput = constants.inputfunction("VMCA Root Certificate is already Expired, VMCA Root and all other Certificates needs to be replaced, Do you want to replace VMCA Root and all other Certificates [Y/N] ? ")
                if rootinput.lower() in ['y','Y','Yes','YES','yes','yES','yeS']:
                    logging.info("Script will replace VMCA Root Certificate as VMCA Root Certificate is already expired")
                    vmca_replace_flag = True
                else:
                    logging.info("Script is exiting based on user input, please execute the script again with 'root' or 'all' argument")
                    sys.exit(1)
        else:
            logging.info("This is a silent execution, so forcefully replacing Root Certificate without user input as VMCA Root is already expired")
            vmca_replace_flag = True

    if (constants.custom_validity):
        if not (vmca_replace_flag):
            adjust_default_cert_validity()

    #List the VECS stores and terminate if the list is empty/None
    vecs_stores = get_vecs_stores()
    if not vecs_stores:
        print(color_red("Failed to list the VECS Stores, script is terminating"))
        sys.exit()
    elif constants.BACKUP_STORE not in vecs_stores:
        vecs_ops.create_store(constants.BACKUP_STORE)

    #Call the specific Certificate replacement function based on the value of Command Line Argument --type, such as machinessl, sts, lookupservice etc.. 
    if environment.deployment_type == "management":
        if (REPLACE_MACHINESSL):
            replace_machine_ssl_certificate()
        if (REPLACE_SOLUTIONUSERS):
            replace_solution_user_certificate(vecs_stores)
        if (REPLACE_DATAENCIPHERMENT):
            replace_data_encipherment_certificate(vecs_stores)
        if (REPLACE_SMS):
            replace_sms_certificate(vecs_stores)
        if (UPDATE_VPXD_EXTENSIONS):
            update_vpxd_extensions()
    elif environment.deployment_type in ["embedded","infrastructure"]:
        if vmca_replace_flag:
            replace_root_certificate()
        if sts_replace_flag:
            replace_sts_certificate()
        if (REPLACE_MACHINESSL):
            replace_machine_ssl_certificate()
        if (REPLACE_LOOKUPSERVICE):
            if "STS_INTERNAL_SSL_CERT" in vecs_stores:
                replace_lookupservice_certificate()
            elif (constants.replace_only_lookupservice):
                print("\nThis vCenter Server DOES NOT have separate STS_INTERNAL_SSL_CERT store for LookupService, hence not taking any action.\nScript is terminating.")
                logging.warning("This vCenter Server DOES NOT have separate STS_INTERNAL_SSL_CERT store for LookupService, hence not taking any action\nScript is terminating.")
                sys.exit()
            else:
                logging.warning("LookupService Store STS_INTERNAL_SSL_CERT DOES NOT EXIST on this vCenter Server")
        if (REPLACE_SOLUTIONUSERS):
            replace_solution_user_certificate(vecs_stores)
        if (REPLACE_DATAENCIPHERMENT):
            replace_data_encipherment_certificate(vecs_stores)
        if (REPLACE_SMS) and environment.deployment_type in ["embedded"]:
            replace_sms_certificate(vecs_stores)
        if (UPDATE_VPXD_EXTENSIONS):
            update_vpxd_extensions()
        if (REMOVE_TRUSTEDROOTS):
            remove_expired_certs_from_trusted_roots()
        if(REMOVE_NON_CA_TRUSTEDROOTS):
            remove_non_ca_certs_from_trusted_roots()
    else:
        logging.error("Deployment Type %s does not match with Management/Embedded/Infrastructure" % environment.deployment_type)
        print(color_red("Deployment Type %s does not match with Management/Embedded/Infrastructure" % environment.deployment_type))
        sys.exit()
    
    #Check user input to restart the services if any Certificate is replaced
    check_service_restart()

    if (constants.auto_service_restart):
        print("\nValidity of Certificates post replacement:")
        (certs_validity, root_certificates_validity) = read_all_certs()
        print(certs_validity)
        print(root_certificates_validity)
        if (constants.services_start_flag):
            print("\nSuccessfully Completed the Certificate Replacement -> Total Execution Time ## %s seconds ##" % round((time.time() - start_time)))
            logging.info("\nSuccessfully Completed the Certificate Replacement -> Total Execution Time ## %s seconds ##" % round((time.time() - start_time)))
        else:
            print("\Completed the Certificate Replacement, however there were failures while restarting Services -> Total Execution Time ## %s seconds ##" % round((time.time() - start_time)))
            logging.info("\nCompleted the Certificate Replacement, however there were failures while restarting Services -> Total Execution Time ## %s seconds ##" % round((time.time() - start_time)))
            logging.error("Script tried to restart the services, howerver there were failures during the restart operation, please restart all the Services manually using command \'service-control --stop --all && service-control --start --all\' for the changes to take effect")
            print("\nScript tried to restart the services, howerver there were failures during the restart operation, please restart all the Services manually using command \'service-control --stop --all && service-control --start --all\' for the changes to take effect")
    elif (not constants.cert_replaced) and constants.remove_only_trusted_roots:
        print("\nSkipped the removal of Certificates from Trusted Roots store as there are no expired Certificates in the Roots Store -> Total Execution Time ## %s seconds ##" % round((time.time() - start_time)))
        logging.info("\nSkipped the removal of Certificates from Trusted Roots store as there are no expired Certificates in the Roots Store -> Total Execution Time ## %s seconds ##" % round((time.time() - start_time)))
    elif (constants.update_only_vpxd_extensions):
        print("\nUpdated the Thumbprint of VPXD Extensions -> Total Execution Time ## %s seconds ##" % round((time.time() - start_time)))
        logging.info("\nUpdated the Thumbprint of VPXD Extensions -> Total Execution Time ## %s seconds ##" % round((time.time() - start_time)))
    elif (not constants.cert_replaced) and constants.remove_nonca_trusted_roots:
        print("\nSkipped the removal of Certificates from Trusted Roots store as it does not have any Non-CA Certificates -> Total Execution Time ## %s seconds ##" % round((time.time() - start_time)))
        logging.info("\nSkipped the removal of Certificates from Trusted Roots store as it does not have any Non-CA Certificates -> Total Execution Time ## %s seconds ##" % round((time.time() - start_time)))
    elif ((constants.replace_only_sms_roots) and (not constants.cert_replaced ) ):
        print("\nSkipped the replacement of SMS Certificate as the the Cert is not Expired -> Total Execution Time ## %s seconds ##" % round((time.time() - start_time)))
        logging.info("\nkipped the replacement of SMS Certificate as the the Cert is not Expired -> Total Execution Time ## %s seconds ##" % round((time.time() - start_time)))
    else: 
        if not (constants.update_only_vpxd_extensions):
            (certs_validity, root_certificates_validity) = read_all_certs()
            if (constants.remove_only_trusted_roots or constants.remove_nonca_trusted_roots or constants.update_only_vpxd_extensions):
                print("\nCertificate status post removal from TRUSTED_ROOTS:")
                print(root_certificates_validity)
            else:
                print("\nValidity of Certificates post replacement:")
                print(certs_validity)
                print(root_certificates_validity)
        print("\nSuccessfully Completed the Certificate Replacement -> Total Execution Time ## %s seconds ##" % round((time.time() - start_time)))
        logging.info("\nSuccessfully Completed the Certificate Replacement -> Total Execution Time ## %s seconds ##" % round((time.time() - start_time)))
        logging.info("Please restart all the Services using command \'service-control --stop --all && service-control --start --all\' for the changes to take effect")
        print("\nPlease restart all the Services using below command for the changes to take effect.")
        print(color_cyan("\tservice-control --stop --all && service-control --start --all"))
    
    #Remove the temporary directory created for certificate replacement
    shutil.rmtree(constants.result_directory,ignore_errors=True)

"""
Initializing the various classes required for the Certificate Replacement Operation
These variables will be used to call the functions in those classes
"""
vecs_ops = VecsCli()
dircli_ops = DirCli()
certool_ops = Certool()
certcfg_ops = CertCfg()
openssl_ops = OpensslCli()
vmafdclient_ops = vmafdClient()

"""
Main function which initializes logging, verifies the arguments
And, calls the replace_certificates function for the certificate replacement operations
"""
def main():
    #setup_logging()
    argparser = parse_arguments()

    if len(sys.argv) == 1:
        argparser.print_help()
        sys.exit(1)
    
    args = argparser.parse_args()

    setup_logging()
    if args.certType not in ['expired_only', 'machinessl', 'sts', 'lookupservice', 'solutionusers', 'root', 'all', 'data-encipherment', 'sms']:
        if args.storeType not in ['trusted_roots', 'trustedroots', 'TRUSTED_ROOTS', 'Trusted_Roots', 'Trusted_roots', 'TRUSTEDROOTS']:
            if args.ExtensionType not in ['all', 'ALL', 'All', 'EAM', 'Eam', 'eam', 'RBD', 'Rbd', 'rbd', 'IMAGEBUILDER', 'Imagebuilder', 'imagebuilder']:
                argparser.print_help()
                sys.exit(1)

    if args.force_encipherment_replace:
        if args.force_encipherment_replace in ['true', 'TRUE', 'True']:
            constants.force_encipherment_cert = True
        elif args.force_encipherment_replace in ['false', 'FALSE', 'False']:
            constants.force_encipherment_cert = False
        else:
            argparser.print_help()
            sys.exit(1)

    if (args.serviceRestart):
        if args.serviceRestart in ['true', 'TRUE', 'True']:
            constants.auto_service_restart = True
        elif args.serviceRestart in ['false', 'FALSE', 'False']:
            constants.auto_service_restart = False
        else:
            argparser.print_help()
            sys.exit(1)
    
    if (args.additionalSAN):
            constants.additional_san = True
            environment.additional_fqdns = ' '.join([str(elem) for elem in args.additionalSAN])
            environment.additional_fqdns = ((environment.additional_fqdns).replace(" ","")).split(",")

    if (args.validityDays):
        try:
            if int(args.validityDays) in range(1,constants.MAX_CERT_VALIDITY):
                constants.use_openssl_functions = True
                constants.DEFAULT_VALIDITY = int(args.validityDays)
                constants.DEFAULT_STS_VALIDITY = int(args.validityDays)
                constants.custom_validity = True
            else:
                print("validityDays will accept number of days as values between 2 to 3650\n")
                argparser.print_help()
                sys.exit(1)
        except ValueError:
            print("validityDays will accept number of days as values between 2 to 3650\n")
            argparser.print_help()
            sys.exit(1)

    if (args.keySize):
        if args.keySize in range(2048, 5120, 1024):
            if args.keySize != "2048":
                constants.DEFAULT_KEY_SIZE = str(args.keySize)
                constants.use_openssl_functions = True
        else:
            print("keySize will not accept any values other than 2048/3072/4096")
            print("Script is Terminating")
            sys.exit(1)

    if (args.silent):
        if args.silent in ['true', 'TRUE', 'True'] and (args.password) and (args.serviceRestart):
            constants.silent_execution = True
            sys.stdout = open(os.devnull, 'w')
        elif args.silent in ['false', 'FALSE', 'False']:
            constants.silent_replace = False
        else:
            argparser.print_help()
            sys.exit(1)    
    
    if (args.debug):
        logging.info("Enabling Debug logging")
        logging.basicConfig(level=logging.DEBUG)

    replace_certificates(args,argparser)

if __name__ == '__main__':
    exit(main())
    
