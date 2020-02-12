
from clients.gitlab_api import GitlabAPI

class Enquiry():
    def __init__(self, config):
        self.projectsc_host = config['projectsc']['host']
        self.projectsc_token = config['projectsc']['token']
        self.github_token = config['github']['token']
        self.git_user = config['git_user']

    def repo_list (self):
        glapi = GitlabAPI(self.projectsc_host, self.projectsc_token)

        shares = glapi.get_group("shares")

        projects = shares.projects.list(all=True, retry_transient_errors=True)
        return projects
