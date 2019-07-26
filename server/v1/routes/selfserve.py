from flask import Blueprint, jsonify, session, request, redirect, url_for, render_template
from flask_dance.consumer import OAuth2ConsumerBlueprint

import json
import oauthlib
import datetime
from datetime import timezone
from operations.enquiry import Enquiry
from operations.repo import RepoOp
from operations.rename import Rename
from clients.gitlab_api import GitlabAPI


from server.config import Config
import os

conf = Config().data

client_id = conf['keycloak']['client_id']
client_secret = conf['keycloak']['client_secret']
oauth_url = conf['keycloak']['url']
oauth_realm = conf['keycloak']['realm']

selfserve = OAuth2ConsumerBlueprint(
    "keycloak", 'selfserve',
    client_id=client_id,
    client_secret=client_secret,
    base_url="%s/auth/realms/%s/protocol/openid-connect/" % (oauth_url, oauth_realm),
    token_url="%s/auth/realms/%s/protocol/openid-connect/token" % (oauth_url, oauth_realm),
    authorization_url="%s/auth/realms/%s/protocol/openid-connect/auth" % (oauth_url, oauth_realm),
    redirect_to="keycloak._selfserve"
)

def get_sae_project (group_list):
    group = group_list[0]
    if group.startswith('/'):
        group = group[1:]
    return group

@selfserve.route("/logout")
def logout():
    # resp = selfserve.session.get("/auth/realms/%s/protocol/openid-connect/logout" % oauth_realm)
    # assert resp.ok
    del selfserve.token
    return redirect(url_for("keycloak.login"))

@selfserve.route("/")
def _selfserve():
    try:
        if not selfserve.session.authorized:
            return redirect(url_for("keycloak.login"))
        resp = selfserve.session.get("/auth/realms/%s/protocol/openid-connect/userinfo" % oauth_realm)
        assert resp.ok

        groups = resp.json()['groups']

        for group in conf['ocwa']['ignoredGroups'].split(','):
            if group in groups:
                groups.remove(group)

        saeProject = get_sae_project(groups)

        if saeProject not in conf['ocwa']['projectWhitelist'].split(','):
            del selfserve.token
            return render_template('error.html', message = "Access Denied - Group not found in whitelist.")

        session['groups'] = groups
        session['username'] = resp.json()['preferred_username']

        return redirect(url_for("keycloak.main"))
    except oauthlib.oauth2.rfc6749.errors.TokenExpiredError as ex:
        return redirect(url_for("keycloak.login"))

@selfserve.route("/main")
def main():
    if not selfserve.session.authorized:
        return redirect(url_for("keycloak.login"))

    saeProject = get_sae_project(session['groups'])

    return render_template('index.html', repo_list=get_linked_repos(), unlinked_repo_list=get_unlinked_repos(), groups=session['groups'], project=get_sae_project(session['groups']), tab={"create":"show active"})


@selfserve.route('/activity',
           methods=['GET'], strict_slashes=False)
def activity() -> object:

    with open('/audit/activity.log', 'r') as f:
        content = f.readlines()
    content = [json.loads(x.strip()) for x in content] 

    content.reverse()

    return json.dumps(content)


@selfserve.route('/projectsc/repository',
           methods=['POST'], strict_slashes=False)
def new_repo() -> object:
    """
    Creates a new repository
    """
    data = request.form

    conf = Config().data

    saeProjectName = get_sae_project(session['groups'])

    private = 'private' in data and data['private'] == 'private'

    try:
        validate (data, ['repository'])

        repoName = data['repository']

        projectsc_host = conf['projectsc']['host']
        projectsc_token = conf['projectsc']['token']

        glapi = GitlabAPI(projectsc_host, projectsc_token)

        RepoOp(glapi).run(saeProjectName, repoName, private)
    except BaseException as error:
        print("Exception %s" % error)
        return do_render_template(success=False, data=data, action="create", tab={"create":"show active"}, message="Failed - %s" % error)

    message = "Shared repository %s created" % data['repository']
    if private:
        message = "Private repository %s created" % data['repository']

    return do_render_template(success=True, data=data, action="create", tab={"create":"show active"}, message=message)

@selfserve.route('/projectsc/repository/rename',
           methods=['POST'], strict_slashes=False)
def rename_repo() -> object:
    """
    Rename a repository
    """
    data = request.form

    conf = Config().data

    saeProjectName = get_sae_project(session['groups'])

    newRepoName = ""
    
    try:
        validate (data, ['repository', 'newRepository'])
        repoName = data['repository']
        newRepoName = data['newRepository']

        projectsc_host = conf['projectsc']['host']
        projectsc_token = conf['projectsc']['token']

        glapi = GitlabAPI(projectsc_host, projectsc_token)

        Rename(conf).rename(repoName, newRepoName)
    except BaseException as error:
        print("Exception %s" % error)
        return do_render_template(success=False, data=data, action="rename", tab={"rename":"show active"}, message="Failed to rename to %s - %s" % (newRepoName, error))

    return do_render_template(success=True, data=data, action="rename", tab={"rename":"show active"}, message="Repository %s renamed to %s" % (repoName, newRepoName))

@selfserve.route('/projectsc/repository/join',
           methods=['POST'], strict_slashes=False)
def join_repo() -> object:
    """
    Join a repository
    """
    data = request.form

    conf = Config().data

    saeProjectName = get_sae_project(session['groups'])

    try:
        validate (data, ['repository'])
        repoName = data['repository']

        projectsc_host = conf['projectsc']['host']
        projectsc_token = conf['projectsc']['token']

        glapi = GitlabAPI(projectsc_host, projectsc_token)

        RepoOp(glapi).join(saeProjectName, repoName)
    except BaseException as error:
        print("Exception %s" % error)
        return do_render_template(success=False, data=data, action="join", tab={"join":"show active"}, message="Failed - %s" % error)

    return do_render_template(success=True, data=data, action="join", tab={"join":"show active"}, message="Repository %s shared with %s" % (repoName, saeProjectName))


@selfserve.route('/projectsc/repository/leave',
           methods=['POST'], strict_slashes=False)
def leave_repo() -> object:
    """
    Leave a repository
    """
    data = request.form

    conf = Config().data

    saeProjectName = get_sae_project(session['groups'])

    try:
        validate (data, ['repository'])
        repoName = data['repository']

        projectsc_host = conf['projectsc']['host']
        projectsc_token = conf['projectsc']['token']

        glapi = GitlabAPI(projectsc_host, projectsc_token)

        RepoOp(glapi).leave(saeProjectName, repoName)

    except BaseException as error:
        print("Exception %s" % error)
        return do_render_template(success=False, data=data, action="leave", tab={"leave":"show active"}, message="Failed - %s" % error)

    return do_render_template(success=True, data=data, action="leave", tab={"leave":"show active"}, message="Repository %s access removed for project %s" % (repoName, saeProjectName))

def get_linked_repos():
    saeProject = get_sae_project(session['groups'])

    projects = Enquiry(Config().data).repo_list()

    repo_list = []
    for project in projects:
        for share in project.shared_with_groups:
            if share['group_name'] == saeProject:
                repo_list.append({"name":project.name, "url":project.http_url_to_repo})

    print(repo_list)

    return repo_list

def get_unlinked_repos():
    saeProject = get_sae_project(session['groups'])

    projects = Enquiry(Config().data).repo_list()

    repo_list = []
    for project in projects:
        found = False
        for share in project.shared_with_groups:
            if share['group_name'] == saeProject:
                found = True

        if found == False:
            repo_list.append({"name":project.name, "url":project.http_url_to_repo})

    print(repo_list)

    return repo_list



def validate (data, names):
    for name in names:
        if (name not in data or data[name] == ""):
            raise Exception ("%s is required." % name)

def do_render_template(**args):
    if 'repository' in args['data']:
        activity (args['action'], args['data']['repository'], args['success'], args['message'])
    return render_template('index.html', **args, repo_list=get_linked_repos(), unlinked_repo_list=get_unlinked_repos(), groups=session['groups'], project=get_sae_project(session['groups']))


def activity (action, repo, success, message):

    with open('/audit/activity.log', 'a', 1) as f:

        payload = {
            "action" : action,
            "repository" : repo,
            "team" : get_sae_project(session['groups']),
            "actor" : session['username'],
            "ts" : utc_to_local(datetime.datetime.now()).isoformat(),
            "success": success,
            "message": message
        }
        f.write(json.dumps(payload) + os.linesep)

def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)