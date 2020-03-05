import argparse
import gitlab
from clients.git_api import GitAPI
from clients.gitlab_api import GitlabAPI
from clients.file_api import FileUtils
import os
import base64
import logging
from urllib.parse import urlparse
from operations.project import ProjectOp
from operations.repo import RepoOp
from operations.hello import Hello
from operations.request_export import RequestExport
from operations.request_import import RequestImport
from operations.merge import Merge
from operations.push_changes import PushChanges
from operations.cancel import Cancel

GIT_USER_EMAIL = os.environ.get("GIT_USER_EMAIL")
GIT_USER_USERNAME = os.environ.get("GIT_USER_USERNAME")

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

TOKEN = os.environ['PROJECTSC_TOKEN']

OUTPUTCHECKERS = "oc"

SHARES = "shares"

CROSS_PROJECT_CHECKER = "oc"

OCWA_CHECKPOINT = "ocwa-checkpoint"

CROSS_PROJECT_GROUP = ""

log = logging.getLogger(__name__)

logging.basicConfig(level='INFO',
                    format='%(asctime)s - %(levelname)s - %(message)s')

parser = argparse.ArgumentParser(description='SRE Project Management')

parser.add_argument('command')

#parser.add_argument('--host',
#                    help='gitlab host')
parser.add_argument('--project', 
                    help='research project')
parser.add_argument('--token',
                    help='token')
parser.add_argument('--private',  default=False, action='store_true',
                    help='make the repository private so Issues are enabled')
parser.add_argument('--repo',
                    help='repository')
parser.add_argument('--external_url',
                    help='external_url')
parser.add_argument('--branch',
                    help='branch')
parser.add_argument('--team', 
                    help='share team project')
parser.add_argument('--destroy',  default=False, type=bool,
                    help='destroy objects')

parser.add_argument('--hook', 
                    help='Hook for calling back to group-sync')

args = parser.parse_args()

host = os.environ.get('PROJECTSC_HOST')
 
glapi = GitlabAPI("%s" % host, TOKEN)

command = args.command

config = {
    "projectsc": { "host" : os.environ.get('PROJECTSC_HOST'), "token" : os.environ.get('PROJECTSC_TOKEN') },
    "github": { "token" : os.environ.get('GITHUB_TOKEN') },
    "git_user": { "username" : os.environ.get("GIT_USER_USERNAME") , "email" : os.environ.get("GIT_USER_EMAIL") }
}

if command == 'hello' and args.destroy == False:

    Hello().run()

elif command == 'project' and args.destroy == False:
    # glcli --project 99-t05 project
    # glcli --project 99-t05 --repo geekcomputers project
    # glcli --project 99-t05 --external_url https://github.com/ikethecoder/popdata-infra.git project

    saeProjectName = args.project
    repo = args.repo
    if args.external_url is not None:
        o = urlparse(args.external_url)
        parts = o.path.split('/')
        repo = "%s-%s" % (parts[1], parts[2])
        repo = repo[0:-4].lower()
        print ("New repo %s : private? %s" % (repo, args.private))

    if repo is None:
        ProjectOp(glapi).run(saeProjectName)
    else:
        RepoOp(glapi).run(saeProjectName, repo, args.private)

elif command == 'request-export' and args.destroy == False:
    # glcli --branch master --external_url https://github.com/ikethecoder/topbar.git request-export

    branch = args.branch
    external_url = args.external_url
    repo = args.repo

    if args.external_url is not None:
        o = urlparse(external_url)
        parts = o.path.split('/')
        repo = "%s-%s" % (parts[1], parts[2])
        repo = repo[0:-4].lower()
        print ("New repo %s" % repo)

    RequestExport(config).run(repo, external_url, branch)

elif command == 'approve-export-merge' and args.destroy == False:

    branch = args.branch
    repo = args.repo

    Merge(config).approve_export_mr(repo, branch)

elif command == 'push-to-external' and args.destroy == False:
    # glcli --branch develop --repo ikethecoder-topbar --external_url https://github.com/ikethecoder/topbar.git push-export-changes

    proj = args.project
    branch = args.branch
    external_url = None
    if args.external_url is not None:
        external_url = args.external_url
    repo = "%s-repo" % proj # args.repo
    if args.repo is not None:
       repo = args.repo

    PushChanges(config).push_to_external (repo, external_url, branch)

elif command == 'request-import' and args.destroy == False:

    # glcli --branch develop --external_url https://github.com/ikethecoder/topbar.git project-import
    proj = args.project
    branch = args.branch
    external_url = args.external_url
    repo = args.repo
    
    if args.repo is None:
        o = urlparse(args.external_url)
        parts = o.path.split('/')
        repo = "%s-%s" % (parts[1], parts[2])
        repo = repo[0:-4].lower()
        print ("New repo %s" % repo)

    RequestImport(config).run(repo, external_url, branch)

elif command == 'approve-import-merge' and args.destroy == False:

    branch = args.branch
    repo = args.repo

    Merge(config).approve_import_mr(repo, branch)

elif command == 'push-to-sae' and args.destroy == False:
    # glcli --branch develop --repo ikethecoder-topbar --external_url https://github.com/ikethecoder/topbar.git push-export-changes

    proj = args.project
    branch = args.branch
    repo = "%s-repo" % proj # args.repo
    if args.repo is not None:
       repo = args.repo

    PushChanges(config).push_to_sae (repo, branch)

elif command == 'cancel-export' and args.destroy == False:
    proj = args.project
    branch = args.branch
    repo = "%s-repo" % proj # args.repo
    if args.repo is not None:
       repo = args.repo

    Cancel(config).cancel_export (repo, branch)

elif command == 'cancel-import' and args.destroy == False:
    proj = args.project
    branch = args.branch
    repo = "%s-repo" % proj # args.repo
    if args.repo is not None:
       repo = args.repo

    Cancel(config).cancel_import (repo, branch)


elif command == 'init' and args.destroy == False:

    glapi.update_root_create_groups()

    glapi.create_get_group(OCWA_CHECKPOINT)
    glapi.create_get_group(OUTPUTCHECKERS)
    glapi.create_get_group(SHARES)

    token = None
    if 'token' in args:
        token = args.token
    if 'hook' in args:
        glapi.create_hook(args.hook, token)

else:
    raise Exception("Invalid command %s (destroy=%s)" % (command, args.destroy))
