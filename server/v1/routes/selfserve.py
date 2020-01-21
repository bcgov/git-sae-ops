from flask import Blueprint, jsonify, session, request, redirect, url_for, render_template
from flask_dance.consumer import OAuth2ConsumerBlueprint

import json
import oauthlib
import datetime
import traceback
from datetime import timezone
from operations.enquiry import Enquiry
from operations.repo import RepoOp
from operations.rename import Rename
from operations.delete import Delete
from clients.gitlab_api import GitlabAPI
from server.activity.activity import activity

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
    if len(group_list) == 0:
        return ""

    group = group_list[0]
    if group.startswith('/'):
        group = group[1:]
    return group

@selfserve.route("/logout")
def logout():
    # resp = selfserve.session.get("/auth/realms/%s/protocol/openid-connect/logout" % oauth_realm)
    # assert resp.ok
    session.clear()
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
            message = "Access Denied - Group %s not found in whitelist." % saeProject
            activity ('access', '', saeProject, resp.json()['preferred_username'], False, message)
            del selfserve.token
            return render_template('error.html', message = message)

        session['groups'] = groups
        session['username'] = resp.json()['preferred_username']

        activity ('access', '', saeProject, session['username'], True, "Access Granted")

        return redirect(url_for("keycloak.main"))
    except oauthlib.oauth2.rfc6749.errors.TokenExpiredError as ex:
        return redirect(url_for("keycloak.login"))

@selfserve.route("/main")
def main():
    if not selfserve.session.authorized:
        return redirect(url_for("keycloak.login"))

    if not 'groups' in session:
        return render_template('error.html', message = "Access Denied")

    return render_template('index.html', repo_list=get_linked_repos(), unlinked_repo_list=get_unlinked_repos(), noshares_repo_list=get_noshares_repos(), groups=session['groups'], project=get_sae_project(session['groups']), tab={"create":"show active"})


@selfserve.route('/activity',
           methods=['GET'], strict_slashes=False)
def view_activity() -> object:
    if not 'groups' in session:
        return render_template('error.html', message = "Access Denied")

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

    if not 'groups' in session:
        return render_template('error.html', message = "Access Denied")

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
        print(traceback.format_exc())
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

    if not 'groups' in session:
        return render_template('error.html', message = "Access Denied")

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

    if not 'groups' in session:
        return render_template('error.html', message = "Access Denied")

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

    if not 'groups' in session:
        return render_template('error.html', message = "Access Denied")

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

@selfserve.route('/projectsc/repository/delete',
           methods=['POST'], strict_slashes=False)
def delete_repo() -> object:
    """
    Delete a repository
    """
    data = request.form

    conf = Config().data

    if not 'groups' in session:
        return render_template('error.html', message = "Access Denied")

    saeProjectName = get_sae_project(session['groups'])

    newRepoName = ""

    try:
        validate (data, ['repository'])
        repoName = data['repository']

        Delete(conf).delete(repoName)
    except BaseException as error:
        print("Exception %s" % error)
        return do_render_template(success=False, data=data, action="delete", tab={"delete":"show active"}, message="Failed to delete %s - %s" % (repoName, error))

    return do_render_template(success=True, data=data, action="delete", tab={"delete":"show active"}, message="Repository %s deleted" % (repoName))


def get_linked_repos():
    saeProject = get_sae_project(session['groups'])

    projects = Enquiry(Config().data).repo_list()

    repo_list = []
    for project in projects:
        for share in project.shared_with_groups:
            if share['group_name'] == saeProject:
                private = project.issues_enabled
                share_count = len(project.shared_with_groups) - 1
                repo_list.append({"name":project.name, "url":project.http_url_to_repo, "private":private, "share_count":share_count})

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
            private = project.issues_enabled
            share_count = len(project.shared_with_groups) - 1
            repo_list.append({"name":project.name, "url":project.http_url_to_repo, "private":private, "share_count":share_count})

    print(repo_list)

    return repo_list

def get_noshares_repos():
    new_list = []
    repo_list = get_unlinked_repos()
    for r in repo_list:
        if r["share_count"] == 0:
            new_list.append(r)
    return new_list

def validate (data, names):
    for name in names:
        if (name not in data or data[name] == ""):
            raise Exception ("%s is required." % name)

def do_render_template(**args):

    if 'repository' in args['data']:
        team = get_sae_project(session['groups'])
        actor = session['username']
        activity (args['action'], args['data']['repository'], team, actor, args['success'], args['message'])
    return render_template('index.html', **args, repo_list=get_linked_repos(), unlinked_repo_list=get_unlinked_repos(), noshares_repo_list=get_noshares_repos(), groups=session['groups'], project=get_sae_project(session['groups']))


