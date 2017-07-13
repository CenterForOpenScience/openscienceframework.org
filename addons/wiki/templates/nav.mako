<nav class="wiki-nav">
    <div class="navbar-collapse text-center">
        <ul class="superlist nav navbar-nav" style="float: none">
            % if user['can_edit']:
            <li data-toggle="tooltip" title="New" data-placement="right" data-container="body">
                <a id="openNewWiki" href="#" data-toggle="modal" data-target="#newWiki">
                    <span class="wiki-nav-closed">
                        <i class="fa fa-plus-circle text-success"></i>
                    </span>
                </a>
            </li>
                % if wiki_id and wiki_name != 'home':
                <li data-toggle="tooltip" title="Delete" data-placement="right" data-container="body">
                    <a href="#" data-toggle="modal" data-target="#deleteWiki">
                    <span class="wiki-nav-closed"><i class="fa fa-trash-o text-danger"> </i></span>
                    </a>
                </li>
                % endif
            % endif
            % if wiki_content:
                <li data-toggle="tooltip" title="Export" data-placement="right" data-container="body">
                    <a href="#" data-toggle="modal" data-target="#exportWiki">
                        <span class="wiki-nav-closed"><i class="fa fa-file-pdf-o text-primary"> </i></span>
                    </a>
                </li>
            % endif

        </ul>
    </div>
</nav>
