import tempfile
from git import Repo
from furl import furl

import logging
log = logging.getLogger(__name__)

class GitAPI():
    def __init__(self, git_url, token = None):
        self.repo_dir = tempfile.mkdtemp()
        repo_dir = self.repo_dir
        log.info('{0:30} {1} '.format('gitapi.init', git_url))

        self.git_url = git_url
        self.cloned_repo = Repo.clone_from(self.prepare_url(git_url, token), repo_dir)
        self.cloned_repo.remotes.origin.fetch()

    def set_user (self, username, email):
        log.info('{0:30} U={1} E={2}'.format('gitapi.set_user', username, email))
        self.cloned_repo.config_writer().set_value("user", "name", username).release()
        self.cloned_repo.config_writer().set_value("user", "email", email).release()

    def info(self):
        log.info('{0:30} {1}'.format('gitapi.info', self.cloned_repo.branches))
        log.info('{0:30} {1}'.format('gitapi.info', self.cloned_repo.refs))

    def has_branch(self, branch):
        log.info('{0:30} {1}'.format('gitapi.has_branch', ("origin/%s" % branch)))
        for b in self.cloned_repo.refs:
            log.info('{0:30} ? {1}'.format('gitapi.has_branch', b.name))
            if b.name == ("origin/%s" % branch):
                return True
        return False

    def is_empty(self):
        return len(self.cloned_repo.refs) == 0
        
    def init(self):
        log.info('{0:30}'.format('gitapi.init'))
        repo = self.cloned_repo
        repo.git.init()

    def checkout_new(self, branch):
        log.info('{0:30} {1} '.format('gitapi.checkout_new', branch))
        repo = self.cloned_repo
        repo.git.checkout('-b', branch)
        return repo.head.commit

    def checkout(self, branch):
        log.info('{0:30} {1} '.format('gitapi.checkout', branch))
        repo = self.cloned_repo
        repo.git.checkout(branch)
        origin = repo.remote(name='origin')
        origin.pull(refspec=branch)
        return repo.head.commit

    def head_commit(self):
        repo = self.cloned_repo
        return repo.head.commit

    def pull_from_remote (self, branch, to_branch, git_url, token = None):
        log.info('{0:30} {1} {2}'.format('gitapi.pull_from_remote', git_url, branch))
        repo = self.cloned_repo
        origin = repo.create_remote('public', self.prepare_url(git_url, token))
        assert origin.exists()
        origin.fetch()                  # assure we actually have data. fetch() returns useful information
        # Setup a local tracking branch of a remote branch
        # repo.create_head('master', origin.refs.master)  # create local branch "master" from remote "master"
        # repo.heads.master.set_tracking_branch(origin.refs.master)  # set local "master" to track remote "master
        # repo.heads.master.checkout()  # checkout local "master" to working tree
        # Three above commands in one:
        repo.create_head(to_branch, origin.refs[branch]).set_tracking_branch(origin.refs[branch]).checkout()
        # rename remotes
        # origin.rename('new_origin')
        # push and pull behaves similarly to `git push|pull`
        # origin.pull()
        # origin.push(refspec=(':delete_me'))
        return repo.head.commit

    def push_to_origin (self, branch):
        log.info('{0:30} {1}'.format('gitapi.push_to_origin', branch))
        repo = self.cloned_repo
        # remote = repo.remote(name='origin')
        # remote.push(refspec="%s-incoming" % branch)
        repo.git.push(['origin', branch])
        return branch

    def prepare_url (self, git_url, token = None):
        if token is not None:
            o = furl(git_url)
            o.username = 'oauth2'
            o.password = token
            return o.url
        else:
            return git_url

    def dir (self):
        return self.repo_dir

    def commit (self, branch, message):
        log.info('{0:30} {1} : {2}'.format('gitapi.commit', branch, message))
        repo = self.cloned_repo

        repo.git.add(A=True)
        repo.index.commit(message)

    def commit_and_push (self, branch, message):
        log.info('{0:30} {1} : {2}'.format('gitapi.commit_and_push', branch, message))
        repo = self.cloned_repo

        repo.git.add(A=True)
        repo.index.commit(message)
        origin = repo.remote(name='origin')

        info = origin.push(refspec=branch)[0]
        if info.flags & 8: # 8 = REJECTED https://gitpython.readthedocs.io/en/stable/reference.html?highlight=.push
            raise Exception("Push rejected - %s" % info.summary)

        log.info('{0:30} {1} : {2}'.format('gitapi.commit_and_push', branch, "SUCCESS"))

    def has_changes (self):
        log.info('{0:30}'.format('gitapi.has_changes'))
        repo = self.cloned_repo
        files = []
        for untracked in repo.untracked_files:
            files.append(untracked)

        for item in repo.index.diff(None):
            files.append(item.a_path)

        log.info(files)
        return files
