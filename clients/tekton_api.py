import logging
log = logging.getLogger(__name__)

class TektonAPI():
    def __init__(self, listener_url):
        self.listener_url = listener_url

    def notify ():
        r = requests.get(self.listener_url)
        if r.status_code != 201:
            log.error("Notification to Tekton failed %s" % r)
        return r.text
