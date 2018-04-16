from framework.routing import Rule, json_renderer

from addons.cloudfiles import views

api_routes = {
    'rules': [
        Rule(
            [
                '/settings/cloudfiles/accounts/',
                '/project/<pid>/cloudfiles/settings/',
            ],
            'post',
            views.cloudfiles_add_user_account,
            json_renderer,
        ),
        Rule(
            [
                '/settings/cloudfiles/accounts/',
            ],
            'get',
            views.cloudfiles_account_list,
            json_renderer,
        ),
        Rule(
            [
                '/project/<pid>/cloudfiles/settings/',
                '/project/<pid>/node/<nid>/cloudfiles/settings/',
            ],
            'put',
            views.cloudfiles_set_config,
            json_renderer,
        ),
        Rule(
            [
                '/project/<pid>/cloudfiles/settings/',
                '/project/<pid>/node/<nid>/cloudfiles/settings/',
            ],
            'get',
            views.cloudfiles_get_config,
            json_renderer,
        ),
        Rule(
            [
                '/project/<pid>/cloudfiles/user-auth/',
                '/project/<pid>/node/<nid>/cloudfiles/user-auth/',
            ],
            'put',
            views.cloudfiles_import_auth,
            json_renderer,
        ),
        Rule(
            [
                '/project/<pid>/cloudfiles/user-auth/',
                '/project/<pid>/node/<nid>/cloudfiles/user-auth/',
            ],
            'delete',
            views.cloudfiles_deauthorize_node,
            json_renderer,
        ),
        Rule(
            [
                '/project/<pid>/cloudfiles/containers/',
                '/project/<pid>/node/<nid>/cloudfiles/containers/',
            ],
            'get',
            views.cloudfiles_folder_list,
            json_renderer,
        ),
        Rule(
            [
                '/project/<pid>/cloudfiles/newcontainer/',
                '/project/<pid>/node/<nid>/cloudfiles/newcontainer/',
            ],
            'post',
            views.cloudfiles_create_container,
            json_renderer
        ),
    ],
    'prefix': '/api/v1',
}
