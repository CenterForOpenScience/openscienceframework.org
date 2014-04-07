import re

from website.models import Node
from website.app import init_app

from website.addons.gitlab.api import client
from website.addons.gitlab.utils import setup_user, setup_node

app = init_app('website.settings', set_backends=True, routes=True)
app.test_request_context().push()

email_regex = re.compile(r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$', re.I)

def migrate_node(node):

    # Quit if no creator
    if not node.contributors[0]:
        return

    # Quit if no files
    if not node.files_current:
        return

    # Ensure Gitlab project
    user_settings = setup_user(node.contributors[0])
    node_settings = setup_node(node, check_ready=False)

    # Hack: Remove contributor from project list; we'll add them back soon
    client.deleteprojectmember(
        node_settings.project_id,
        user_settings.user_id
    )

    # Ensure Gitlab users
    for contrib in node.contributors:
        if not contrib or not contrib.username:
            continue
        if not email_regex.search(contrib.username):
            continue
        if contrib.is_active() and contrib != node.contributors[0]:
            setup_user(contrib)
        node_settings.after_add_contributor(node, contrib)


def migrate_nodes():

    for node in Node.find():
        migrate_node(node)


if __name__ == '__main__':
    migrate_nodes()
