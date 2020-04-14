try:  # Python 3.5+
    from http import HTTPStatus as HTTPStatus
except ImportError:
    from http import client as HTTPStatus
from flask import Blueprint, jsonify, request

from server.config import Config
import requests
import json
import sys
import traceback
from server.auth.auth import auth
from operations.push_changes import PushChanges
from clients.tekton_api import TektonAPI

from server.activity.activity import activity

import logging
log = logging.getLogger(__name__)

flow = Blueprint('flow', 'flow')

@flow.route('/merge_retry',
           methods=['POST'], strict_slashes=False)
@auth
def gitlab_merge_retry() -> object:
    """
    Allows for a manual retry of the push
    """
    conf = Config().data

    data = request.get_json()

    log.debug("-- MR Merged - initiate mirroring")
    source = data['source_branch']
    target = data['target_branch']
    log.debug("%s --> %s" % (source,target))

    try:
        if source.endswith('-outgoing'):
            repoName = data['repository']
            log.debug("push_to_external (%s, %s, %s)" % (repoName, None, target))
            PushChanges(conf).push_to_external(repoName, None, target)
            log.info("Successful push_to_external mirror")

        elif source.endswith('-incoming'):
            repoName = data['repository']
            log.debug("push_to_sae (%s, %s)" % (repoName, target))
            PushChanges(conf).push_to_sae(repoName, target)
            log.info("Successful push_to_sae mirror")
        else:
            log.debug("ERR: Unexpected source branch %s" % source)
    except BaseException as error:
        track = traceback.format_exc()
        log.error("Trace... %s" % str(track))
        raise error

    return jsonify(status="ok"), HTTPStatus.OK
    
@flow.route('/webhook',
           methods=['POST'], strict_slashes=False)
@auth
def gitlab_webhook() -> object:
    """
    Takes a gitlab webhook event and processes the event
    """
    conf = Config().data

    data = request.get_json()
    log.info("---")
    log.info(data)
    log.info("---")

    if "object_kind" in data and data['object_kind'] == "merge_request" and data['project']['namespace'] == conf.get('checkpointGroup'):
        log.info("Merge Request for a checkpoint project detected: %s" % data['repository']['name'])
        if data['object_attributes']['state'] == 'merged':
            log.debug("-- MR Merged - initiate mirroring")
            source = data['object_attributes']['source_branch']
            target = data['object_attributes']['target_branch']
            log.debug("%s --> %s" % (source,target))

            try:
                if source.endswith('-outgoing'):
                    repoName = data['repository']['name']
                    log.debug("push_to_external (%s, %s, %s)" % (repoName, None, target))
                    PushChanges(conf).push_to_external(repoName, None, target)
                    log.info("Successful push_to_external mirror")
                    activity ('push_to_external', repoName, '', 'gitlab', True, "Push completed")

                elif source.endswith('-incoming'):
                    repoName = data['repository']['name']
                    log.debug("push_to_sae (%s, %s)" % (repoName, target))
                    PushChanges(conf).push_to_sae(repoName, target)
                    log.info("Successful push_to_sae mirror")
                    activity ('push_to_internal', repoName, '', 'gitlab', True, "Push completed")
                else:
                    raise Exception("Unexpected source branch %s" % source)
            except BaseException as error:
                track = traceback.format_exc()
                log.error("Trace... %s" % str(track))
                activity ('push_to_external', repoName, '', 'gitlab', False, "Push failed - %s" % error)
        else:
            log.debug("-- MR Ignored - state %s" % data['object_attributes']['state'])
    elif "event_name" in data:
        log.info("Skipping event NAME: %s" % data['event_name'])
        if data['event_name'] == 'repository_update' \
          and conf.get('bbsae').get('project_name') == data['project']['name'] \
          and conf.get('bbsae').get('enabled'):
            log.info("BBSAE Enabled.  If push of bbsae-applications, then trigger build")
            pipeline_url = conf.get('bbsae').get('pipeline_url')
            api = TektonAPI(pipeline_url)
            log.info("Notifying %s" % pipeline_url)
            try:
                response = api.notify()
                activity ('trigger_image_pipeline', data['project']['name'], '', 'gitlab', True, "%s" % response)
            except BaseException as error:
                track = traceback.format_exc()
                log.error("Trace... %s" % str(track))
                activity ('trigger_image_pipeline', data['project']['name'], '', 'gitlab', False, "%s" % error)

    elif "event_type" in data:
        log.info("Skipping event TYPE: %s" % data['event_type'])
    else:
        log.info("Skipping event")

    return jsonify(status="ok"), HTTPStatus.OK
