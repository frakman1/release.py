#!/usr/bin/python

#https://img.rpadovani.com/posts/automation.png

from __future__ import print_function
import errno
import argparse
import os
import sys
from textwrap import dedent
from UserString import *
import pprint
import subprocess
import pexpect
from subprocess import Popen, PIPE
import webbrowser
from path import Path
import getpass

#Adjust these as necessary for your poject.
#Ensure you have your Gitlab personal access token in ~/.tk
#Ensure you have your Gitlab User ID  ~/.uid
#Ensure you have your Jenkins user Token in ~/.jenktok_prod

HOST = "gitlab.xxx.xxx
GROUP = "DPK"
PROJECT_NAME = "DPK_non_secure"
REPO = "git@"+HOST+":"+GROUP+"/"+PROJECT_NAME+".git"
PROJECT_ID = "1515"       # This ID is specific to the DPK_non_secure project
SECURE_PROJECT_ID = "1517"  # This ID is specific to the DPK_secure project
NON_SEC_BRANCH_NAME = "dpk2-signon"
SEC_BRANCH_NAME = "dpk2-signon"

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BLINK = '\033[5m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def execute(cmd):
    popen = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, universal_newlines=True, stderr=subprocess.PIPE)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def insert(originalfile,string):

    temp = "temp"+originalfile
    with open(originalfile,'r') as f:
        with open(temp,'w') as f2:
            f2.write(string)
            f2.write(f.read())


class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass

#Get user Input
parser = argparse.ArgumentParser(description='This script will make a release of the DPK_non_secure repo. Input of version and text file with TDETS is required',
                                 epilog='Examples of Use:\n----------------\nrelease.py -v 1.3.7 -t tdets.txt',
                                 formatter_class=CustomFormatter)
requiredNamed = parser.add_argument_group('required named argument')
requiredNamed.add_argument('-v', '--version', dest='rel_version', required=True, help='[Input] version number of this release')
requiredNamed.add_argument('-t', '--tdets', dest='tdets_file', required=True, help='[Input] text file with TDETS fixed in this build')
results = parser.parse_args()

local_branch_name = "WB20_SIGNON_CAK_Release_"+results.rel_version
branches_url = "http://"+HOST+"/"+GROUP+"/"+PROJECT_NAME+"/branches"
MR_url = "http://"+HOST+"/"+GROUP+"/"+PROJECT_NAME+"/merge_requests"

#Display User Input
print("\n")
print (bcolors.OKBLUE + "Input release version = " + results.rel_version + bcolors.ENDC)
print (bcolors.OKBLUE + "Input TDETS file = " + results.tdets_file + bcolors.ENDC)
print (bcolors.OKBLUE + "TDETS File exists = " + str(os.path.isfile(results.tdets_file)) + bcolors.ENDC)
print (bcolors.OKBLUE + "Branch = " + local_branch_name + bcolors.ENDC)
print (bcolors.OKBLUE + "Repo = " + REPO + bcolors.ENDC)

#MR_url = "http://"+HOST+"/"+GROUP+"/"+PROJECT_NAME+"/merge_requests/new?merge_request[source_branch]="+local_branch_name+"&merge_request[target_branch]="+NON_SEC_BRANCH_NAME+"
#print "\tMR_url = "+MR_url
homedir = os.environ['HOME']
#print homedir
TOKEN_PATH = homedir+"/.tk"
with open (TOKEN_PATH, "r") as tkfile:
    TOKEN=tkfile.read().replace('\n', '')
#print (bcolors.OKBLUE + "GITLAB TOKEN = "+TOKEN +bcolors.ENDC)
UID_PATH = homedir+"/.uid"
with open (UID_PATH, "r") as uidfile:
    USER_ID=uidfile.read().replace('\n', '')
print (bcolors.OKBLUE +  "Gitlab USER_ID = "+USER_ID + bcolors.ENDC)


JENKINS_TOKEN_PATH = homedir+"/.jenktok_prod"
with open (JENKINS_TOKEN_PATH, "r") as jenktokfile:
    JENKINS_TOKEN=jenktokfile.read().replace('\n', '')
#print (bcolors.OKBLUE +  "JENKINS USER TOKEN = "+JENKINS_TOKEN + bcolors.ENDC)

#Print the TDETS.txt file
f = open(results.tdets_file,'r')
tdets = ""
while 1:
    line = f.readline()
    if not line:break
    tdets += line

f.close()
print (bcolors.OKGREEN + "\nTDETS File:\n----------" )
print (tdets)
print (bcolors.ENDC)

#create temporary file for DPK_secure tag description
insert(results.tdets_file,"release_description=")

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Tag the DPK_secure project
raw_input("\033[91;5;7m" + "\n\nPress Enter to tag the DPK_secure repo with " + results.rel_version + "-dpk2" + bcolors.ENDC)
tag_file_path = os.path.dirname(os.path.realpath(__file__))+"/temp"+results.tdets_file
cmd = "curl -k --header \"PRIVATE-TOKEN: "+TOKEN+"\" -X POST \"https://"+HOST+"/api/v4/projects/"+SECURE_PROJECT_ID+"/repository/tags?tag_name="+results.rel_version+"-dpk2"+"&ref="+SEC_BRANCH_NAME+"\" --data \"message=CAK tag "+results.rel_version+" for WB2.0 DPK2 release(Signon)\" --data-binary @"+tag_file_path
print (bcolors.OKGREEN + cmd.replace(TOKEN,"******") + bcolors.ENDC)
pexpect.run(cmd, logfile=sys.stdout)
raw_input("\033[91;5;7m" + "\n\nPress Enter once you are satisfied with the tag name/description of DPK_secure project" + bcolors.ENDC)
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#Create Working Dir
try:
    os.mkdir(results.rel_version)
except OSError as e:
    if e.errno != errno.EEXIST:
        print ("ERROR MAKING RELEASE DIRECTORY")
        raise  # raises the error again
os.chdir(results.rel_version)

#Clone Project Repo
print (bcolors.OKGREEN + "Cloning Repo..." + bcolors.ENDC)
cmd = "git clone -b "+NON_SEC_BRANCH_NAME+" --single-branch " + REPO + " DPK_non_secure"
print (bcolors.OKGREEN + cmd + bcolors.ENDC)
pexpect.run(cmd, logfile=sys.stdout, timeout=None)
os.chdir("DPK_non_secure")
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
print (bcolors.OKGREEN + "Sourcing environment..." + bcolors.ENDC)
source_cmd = [ "/bin/bash", "-c", "source ./environ -cwb20 -cak-from-source -bfs-from-source -br-prime && env -0" ]
print (bcolors.OKGREEN + str(source_cmd) + bcolors.ENDC)
proc = Popen(source_cmd, stdout=PIPE)
vars_out, _ = proc.communicate()
if proc.returncode:
    print ("ERROR: Failed to source bashrc. Check output above.")

# Get the vars from the output
for var in vars_out.split("\0"):
    var_name, _, var_value = var.partition("=")
    os.environ[var_name] = var_value
#pprint.pprint(dict(os.environ), width=1)
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Decrypt source code
#print (bcolors.OKGREEN + "Decrypting Source Code..." + bcolors.ENDC)
#os.chdir("DPK_secure/encrypted-src")
#cmd = "./decrypt.sh"
#print (bcolors.OKGREEN + cmd + bcolors.ENDC)
#pexpect.run(cmd, logfile=sys.stdout)
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#os.chdir("../../")
#Update versions.mk with new version number
with open("./build/versions.mk", "r") as fin:
    with open("./build/versions2.mk", "w") as fout:
        lines = fin.readlines()
        master_version, sep, version = lines[1].partition(":=")
        if sep:
            lines[1] = lines[1].replace(version, " "+results.rel_version+"\n")
        fout.writelines(lines)
cmd = "cp ./build/versions2.mk ./build/versions.mk"
print (bcolors.OKGREEN + cmd + bcolors.ENDC)
pexpect.run(cmd, logfile=sys.stdout)
cmd = "rm ./build/versions2.mk"
print (bcolors.OKGREEN + cmd + bcolors.ENDC)
pexpect.run(cmd, logfile=sys.stdout)
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#Build CAK library files
print (bcolors.OKGREEN + "Building all CAK library variants..." + bcolors.ENDC)
cmd = "DPK_secure/tools/build_all.sh -mangle-on"
print (bcolors.OKGREEN + cmd + bcolors.ENDC)
for line in execute([cmd]):
    print(line, end='')

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#verify versions.mk
cmd = "cat ./build/versions.mk"
print (bcolors.OKGREEN + cmd + bcolors.ENDC)
pexpect.run(cmd, logfile=sys.stdout)
#verify build_version
cmd = "cat ./cak/build_version"
print (bcolors.OKGREEN + cmd + bcolors.ENDC)
pexpect.run(cmd, logfile=sys.stdout)

cmd = "git stash"
print (bcolors.OKGREEN + cmd + bcolors.ENDC)
pexpect.run(cmd, logfile=sys.stdout)

cmd = "git checkout -b "+local_branch_name+" --track origin/"+NON_SEC_BRANCH_NAME
print (bcolors.OKGREEN + cmd + bcolors.ENDC)
pexpect.run(cmd, logfile=sys.stdout)

cmd = "git stash pop"
print (bcolors.OKGREEN + cmd + bcolors.ENDC)
pexpect.run(cmd, logfile=sys.stdout)

cmd = "git add --all"
print (bcolors.OKGREEN + cmd + bcolors.ENDC)
pexpect.run(cmd, logfile=sys.stdout)

cmd = "git status"
print (bcolors.OKGREEN + cmd + bcolors.ENDC)
pexpect.run(cmd, logfile=sys.stdout)
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Commit all changes
header = ":package: Check-in prebuilt libcak libraries for WB2.0 <release> " + results.rel_version
seq = (header,tdets)
commit_msg = '\n\n'.join(seq)
print (commit_msg)
cmd = 'git commit -S -m \"'+commit_msg+ '\"'
print (bcolors.OKGREEN + cmd + bcolors.ENDC)
pexpect.run(cmd, logfile=sys.stdout)

raw_input("\033[91;5;7m" + "\n\nPress Enter once you are satisfied with Commits" + bcolors.ENDC)

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Push upstream
target = local_branch_name
cmd = "git push origin " + target
print (bcolors.OKGREEN + cmd + bcolors.ENDC)
pexpect.run(cmd, logfile=sys.stdout)
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Create Merge Request for this commit
print (bcolors.OKGREEN + "Creating Merge Request..." + bcolors.ENDC)
cmd = "curl -k --header \"PRIVATE-TOKEN: "+TOKEN+"\" -X POST \"https://"+HOST+"/api/v4/projects/"+PROJECT_ID+"/merge_requests\" --data \"source_branch="+local_branch_name+"\" --data \"target_branch="+NON_SEC_BRANCH_NAME+"\" --data \"title="+header+"\" --data \"remove_source_branch=true\" --data \"assignee_id="+USER_ID+"\" "
print (bcolors.OKGREEN + cmd.replace(TOKEN,"******") + bcolors.ENDC)
pexpect.run(cmd, logfile=sys.stdout)

print (bcolors.OKGREEN + "\n\nReview and Accept Merge-Request using a browser:" + bcolors.ENDC)
print (bcolors.WARNING + MR_url + "\n\n" +  bcolors.ENDC)
#webbrowser.open_new(MR_url)

raw_input("\033[91;5;7m" + "\n\nPress Enter once you have accepted the Merge Request and ready to tag the DPK_non_secure Repo\n" + bcolors.ENDC)
#print bcolors.OKGREEN + "\n\n!IMPORTANT! Now Tag the project tree with: wb20-release-tag-"+results.rel_version + bcolors.ENDC
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Tag the DPK_non_secure Project
print (bcolors.OKGREEN + "Tagging DPK_non_secure repo..." + bcolors.ENDC)
cmd = "curl -k --header \"PRIVATE-TOKEN: "+TOKEN+"\" -X POST \"https://"+HOST+"/api/v4/projects/"+PROJECT_ID+"/repository/tags?tag_name=wb20-dpk2-release-tag-"+results.rel_version+"&ref="+NON_SEC_BRANCH_NAME+"\" --data \"message=Release for WB2.0-dpk2(Signon)\" --data-binary @"+tag_file_path
print (bcolors.OKGREEN + cmd.replace(TOKEN,"******") + bcolors.ENDC)
pexpect.run(cmd, logfile=sys.stdout)

raw_input("\033[91;5;7m" + "\n\nPress Enter once you have inspected and are satisfied with the tag and ready to trigger a Jenkins build\n" + bcolors.ENDC)
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Trigger Jenkins Build
print (bcolors.OKGREEN + "Triggering Jenkins Build..." + bcolors.ENDC)
username = getpass.getuser()
#cmd="curl -X POST http://"+username+":"+JENKINS_TOKEN+"@worldbox.lwr.am.thmulti.com:8080/jenkins/job/DPK2_CWB20_SIGNON/build"
cmd="curl -k -X POST http://"+username+":"+JENKINS_TOKEN+"@worldbox.lwr.am.thmulti.com:8080/jenkins/job/DPK2_CWB20_SIGNON/buildWithParameters?tags=wb20-dpk2-release-tag-"+results.rel_version


print (bcolors.OKGREEN + cmd.replace(JENKINS_TOKEN,"******") + bcolors.ENDC)
pexpect.run(cmd, logfile=sys.stdout)
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
print (bcolors.OKGREEN + "Release of " + results.rel_version + " is now complete. Go to Jenkins site to review build status." + bcolors.ENDC)
print (bcolors.WARNING + "http://worldbox.xxx.xxx:8080/jenkins/job/DPK2_CWB20_SIGNON/lastBuild/" + bcolors.ENDC)
exit(0)
