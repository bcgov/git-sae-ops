
from clients.git_api import GitAPI
from clients.file_api import FileUtils
from clients.gitlab_api import GitlabAPI

import logging
log = logging.getLogger(__name__)

class RequestExport():
    def __init__(self, config):
        self.projectsc_host = config['projectsc']['host']
        self.projectsc_token = config['projectsc']['token']
        self.github_token = config['github']['token']
        self.git_user = config['git_user']

    def run (self, repoName, importUrl, branch):
        glapi = GitlabAPI(self.projectsc_host, self.projectsc_token)

        checkpoint = glapi.create_get_group("ocwa-checkpoint")
        cpRepo = glapi.get_project(checkpoint, repoName)

        self.init_pri_branch(repoName, branch)

        if glapi.has_branch (checkpoint, repoName, "%s-outgoing" % branch):
            raise Exception("Export request rejected.  Branch '%s' already exists." % ("%s-outgoing" % branch))

        self.verify_external_repo(importUrl)

        #tgit = self.prep_checkpoint_from_external(repoName, importUrl, branch, branch, self.github_token)

        # Source (SRE)
        sreShares = glapi.create_get_group("shares")
        glRepo = glapi.get_project(sreShares, repoName)

        sgit = GitAPI(glRepo.http_url_to_repo, self.projectsc_token)
        sgit.info()
        sgit.checkout(branch)
        commitRef = sgit.head_commit()

        # Target (Temporary outgoing branch based on the prepped branch)
        tgit = GitAPI(cpRepo.http_url_to_repo, self.projectsc_token)
        tgit.info()
        tgit.checkout("%s" % branch)
        tgit.checkout_new("%s-outgoing" % branch)
        tgit.set_user(self.git_user['username'], self.git_user['email'])

        # Do a full copy from source to target
        fileutils = FileUtils()
        fileutils.copytree (sgit.dir(), tgit.dir())
        fileutils.sync_deletions (sgit.dir(), tgit.dir(), ["/.gitlab-ci.yml"])

        if len(tgit.has_changes()) == 0:
            print("-- Exiting.  No changes to export.")
            return None

        # tgit.commit_and_push("%s" % branch, "Merged sae changes (%s)" % commitRef.hexsha[0:7])
        tgit.commit_and_push("%s-outgoing" % branch, "Merged sae changes (%s)" % commitRef.hexsha[0:7])

        # ciYaml = 'scanjob:\n   script: ocwa-scanner\n'
        # glapi.add_file(shareRepoId, "%s-outgoing" % branch, '.gitlab-ci.yml', ciYaml)

        glapi.set_custom_attribute (cpRepo.id, 'external_url', importUrl)

        return glapi.create_get_merge_request (cpRepo.id, "Export Request (%s)" % commitRef.hexsha[0:7], "%s-outgoing" % branch, "%s" % branch, None, ['ocwa-export'])


    def prep_checkpoint_from_external (self, repoName, url, branch, to_branch, token = None):
        glapi = GitlabAPI(self.projectsc_host, self.projectsc_token)

        # Pull latest from external repo into the checkpoint branch
        cp = glapi.create_get_group("ocwa-checkpoint")

        cpRepo = glapi.get_project(cp, repoName)

        tgit = GitAPI(cpRepo.http_url_to_repo, self.projectsc_token)
        tgit.info()

        commitRef = tgit.pull_from_remote(branch, to_branch, url, token)
        #tgit.push_to_origin(to_branch)

        return tgit


    def init_pri_branch (self, repoName, branch):
        glapi = GitlabAPI(self.projectsc_host, self.projectsc_token)

        checkpoint = glapi.create_get_group("ocwa-checkpoint")
        repo = glapi.create_get_project(checkpoint, repoName)


        ciYaml = 'scanjob:\n   script: ocwa-scanner\n'
        glapi.create_get_branch (checkpoint, repoName, branch, 'private')
        glapi.protect_branch(repo, branch)
        glapi.add_file(repo, branch, '.gitlab-ci.yml', ciYaml)

    def verify_external_repo (self, url):

        try:
            git = GitAPI(url, self.github_token)
            git.info()
            return git
        except BaseException as ex:
            err = str(ex).replace('oauth2', "*****").replace(self.github_token, "*****")
            log.info('{0:30} {1}'.format('verify_external_repo', err))
            raise Exception("There was a problem accessing %s.  Please check there is access and repo exists. (%s)" % (url, err))
