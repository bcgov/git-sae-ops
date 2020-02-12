from server.config import Config
import os
from server.v1.routes.selfserve import selfserve
from operations.project import ProjectOp
from operations.repo import RepoOp
from clients.gitlab_api import GitlabAPI
import logging
import sys

def setup():
    log = logging.getLogger(__name__)
    conf = Config().data

    projectsc_host = conf['projectsc']['host']
    projectsc_token = conf['projectsc']['token']

    glapi = GitlabAPI(projectsc_host, projectsc_token)

    pop = ProjectOp(glapi)

    log.debug("SETUP START")
    all_groups = pop.get_all_groups()
    for project in conf['ocwa']['projectWhitelist'].split(','):
        log.debug("Check Exists?  %s" % project)

        exists = False
        for grp in all_groups:
            if grp.name == project:
                exists = True

        if exists == False:
            log.debug("Create Group.. %s" % project)
            pop.create_group(project)

        ## There should not be repos under the Project Groups
        ## If there are, move them to the 'shares' group
        # try:
        #     group = pop.get_group(project)
        #     for proj in group.projects.list():
        #         gl_project = pop.get_project_by_id(proj.id)

        #         if (gl_project.default_branch != "develop"):
        #             RepoOp(glapi).repair(project, gl_project.name)

        #         if gl_project.namespace["id"] == group.id:
        #             log.debug("REPAIR %20s MOVING" % gl_project.name)
        #             pop.transfer(proj.id, "shares")
        #         else:
        #             log.debug("SETUP %20s SKIPPING (%s)" % (gl_project.name, gl_project.namespace["name"]))
        #             #if gl_project.name == "ajc-test-10":
        #             #    pop.transfer(proj.id, "99-t05")
        # except:
        #     log.error("Error - unable to continue setup.")
        #     log.error("Unexpected error:", sys.exc_info()[0])
    log.debug("SETUP DONE")
