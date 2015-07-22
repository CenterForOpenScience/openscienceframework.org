<div class="project-authors">
    % for contributor in contributors:
        <div mod-meta='{
                "tpl": "util/render_user.mako",
                "uri": "/api/v1/profile/${contributor['user_id']}/summary/",
                "view_kwargs": {
                    "formatter": "surname",
                    "separator":"${contributor['separator']}"
                },
                "replace": true
        }'>
        </div>
    % endfor
    % if others_count:
        <a href="${node_url}">${others_count} more</a>
    % endif
</div>

