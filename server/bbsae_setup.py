import os
import sys
import logging
import base64
import traceback
from server.config import Config
from server.v1.routes.selfserve import selfserve
from operations.project import ProjectOp
from operations.repo import RepoOp
from clients.gitlab_api import GitlabAPI
from clients.tekton_api import TektonAPI
from server.activity.activity import activity

def setup():
    log = logging.getLogger(__name__)
    conf = Config().data

    projectsc_host = conf['projectsc']['host']
    projectsc_token = conf['projectsc']['token']

    glapi = GitlabAPI(projectsc_host, projectsc_token)

    rop = RepoOp(glapi)

    log.debug("SETUP BBSAE START")

    user = glapi.create_get_user ('bbsae-tekton-principal', conf.get('bbsae').get('access_token'))

    tok = glapi.create_personal_access_token(user, 'tekton-pat')
    if tok is not None:
        with open ("/tokens/%s.token" % 'tekton-pat', 'w') as outfile:
            outfile.write(tok)

    #pipeline_url = conf.get('bbsae').get('pipeline_url')
    #api = TektonAPI(pipeline_url)
    #log.info("Notifying %s" % pipeline_url)
    #try:
    #    response = api.notify()
    #    activity ('trigger_image_pipeline', '', '', 'gitlab', True, "%s" % response)
    #except BaseException as error:
    #    track = traceback.format_exc()
    #    log.error("Trace... %s" % str(track))
    #    activity ('trigger_image_pipeline', '', '', 'gitlab', False, "%s" % error)

    
    # Setup requires the following:
    # - create a shared project: "bbsae-applications"
    # - configure branches to be 'develop' as default
    # - add default files
    # - add a Deploy Key to the project

    #pub_key_b64 = conf.get('bbsae').get('ssh_key_pub')
    #pub_key = base64.b64decode(pub_key_b64).decode('utf-8')
    repoName = conf.get('bbsae').get('project_name')

    shares = glapi.create_get_group("shares")

    if glapi.project_exists(shares, repoName):
        log.debug("Project %s already exists" % repoName)
    else:
        rop.run(None, repoName, False)

    project = glapi.get_project(shares, repoName)

    glapi.add_project_member (project, user)

    # Create a deploy key
    #glapi.add_deploy_key (project.id, 'bbsae-tekton-access', pub_key, False)

    log.debug("SETUP BBSAE DONE")
