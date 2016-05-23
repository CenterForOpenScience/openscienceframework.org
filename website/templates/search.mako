<%inherit file="base.mako"/>
<%def name="title()">Search</%def>
<%def name="stylesheets()">
    ${parent.stylesheets()}
    <link rel="stylesheet" href="/static/css/pages/search-page.css">
</%def>

<%def name="content()">
    <div id="searchControls" class="scripted">
        <%include file='./search_bar.mako' />
        <div class="row">
            <div class="col-md-12">
                <div class="row m-t-md">
                    <!-- ko if: allCategories().length > 0-->
                    <div class="col-md-3">
                        <div class="row">
                            <div class="col-md-12">
                                <ul class="nav nav-pills nav-stacked" data-bind="foreach: allCategories">

                                    <!-- ko if: $parent.category().name === name -->
                                        <li class="active"> <!-- TODO: simplify markup; only the active class really needs to be conditional -->
                                            <a data-bind="click: $parent.filter.bind($data)"><span data-bind="text: display"></span><span class="badge pull-right" data-bind="text: count"></span></a>
                                        </li>
                                    <!-- /ko -->
                                    <!-- ko if: $parent.category().name !== name -->
                                        <li>
                                            <a data-bind="click: $parent.filter.bind($data)"><span data-bind="text: display"></span><span class="badge pull-right" data-bind="text: count"></span></a>
                                        </li>
                                    <!-- /ko -->
                                </ul>
                            </div>
                        </div>
                        <!-- ko if: tags().length -->
                        <div class="row">
                            <div class="col-md-12">
                                <h4> Improve your search:</h4>
                                <span class="tag-cloud" data-bind="foreach: {data: tags, as: 'tag'}">
                                    <!-- ko if: count === $parent.tagMaxCount() && count > $parent.tagMaxCount()/2  -->
                                    <span class="tag tag-big tag-container"
                                          data-bind="click: $root.addTag.bind($parentContext, tag.name)">
                                        <span class="cloud-text" data-bind="text: name"></span>
                                        <i class="fa fa-times-circle remove-tag big"
                                           data-bind="click: $root.removeTag.bind($parentContext, tag.name)"></i>
                                    </span>
                                    <!-- /ko -->
                                    <!-- ko if: count < $parent.tagMaxCount() && count > $parent.tagMaxCount()/2 -->
                                    <span class="tag tag-med tag-container"
                                          data-bind="click: $root.addTag.bind($parentContext, tag.name)">
                                        <span class="cloud-text" data-bind="text: name"></span>
                                        <i class="fa fa-times-circle remove-tag med"
                                           data-bind="click: $root.removeTag.bind($parentContext, tag.name)"></i>
                                    </span>
                                    <!-- /ko -->
                                    <!-- ko if: count <= $parent.tagMaxCount()/2-->
                                    <span class="tag tag-sm tag-container"
                                          data-bind="click: $root.addTag.bind($parentContext, tag.name)">
                                        <span class="cloud-text" data-bind="text: name"></span>
                                        <i class="fa fa-times-circle remove-tag"
                                           data-bind="click: $root.removeTag.bind($parentContext, tag.name)"></i>
                                    </span>
                                    <!-- /ko -->
                                </span>
                            </div>
                        </div>
                        <br />
                        <!-- /ko -->
                        <div class="row hidden-xs" data-bind="if: showLicenses">
                            <div class="col-md-12">
                                <h4> Filter by license:</h4>
                                <span data-bind="if: licenses">
                                <ul class="nav nav-pills nav-stacked"
                                    data-bind="foreach: {data: licenses, as: 'license'}">
                                  <li data-bind="css: {'active': license.active(), 'disabled': !license.count()}">
                                    <a data-bind="click: license.toggleActive">
                                      <span style="display: inline-block; max-width: 85%;" data-bind="text: license.name"></span>
                                      <span data-bind="text: license.count" class="badge pull-right"></span>
                                    </a>
                                  </li>
                                </ul>
                                </span>
                            </div>
                        </div>
                        <br />
                    </div>
                    <!-- /ko -->
                    <div class="col-md-9">
                        <!-- ko if: searchStarted() && !totalCount() -->
                        <div class="search-results hidden" data-bind="css: {hidden: totalCount() }">No results found.</div>
                        <!-- /ko -->
                        <!-- ko if: totalCount() -->
                        <div data-bind="foreach: results">
                            <div class="search-result" data-bind="template: { name: category, data: $data}"></div>
                        </div>
                        <ul class="pager">
                            <li data-bind="css: {disabled: !prevPageExists()}">
                                <a href="#" data-bind="click: pagePrev">Previous Page </a>
                            </li>
                            <span data-bind="visible: totalPages() > 0">
                                <span data-bind="text: navLocation"></span>
                            </span>
                            <li data-bind="css: {disabled: !nextPageExists()}">
                                <a href="#" data-bind="click: pageNext"> Next Page</a>
                            </li>
                        </ul>
                        <!-- /ko -->
                        <div class="buffer"></div>
                    </div><!--col-->
                </div><!--row-->
            </div><!--col-->
        </div><!--row-->
    </div>

    <script type="text/html" id="SHARE">
        <!-- ko if: $data.links -->
            <h4><a data-bind="attr: {href: links[0].url}, text: title"></a></h4>
        <!-- /ko -->

        <!-- ko ifnot: $data.links -->
            <h4><a data-bind="attr: {href: id.url}, text: title"></a></h4>
        <!-- /ko -->

        <h5>Description: <small data-bind="fitText: {text: description || 'No Description', length: 500}"></small></h5>

        <!-- ko if: contributors.length > 0 -->
        <h5>
            Contributors: <small data-bind="foreach: contributors">
                <span data-bind="text: $data.given + ' ' + $data.family"></span>
            <!-- ko if: ($index()+1) < ($parent.contributors.length) -->&nbsp;- <!-- /ko -->
            </small>
        </h5>
        <!-- /ko -->

        <!-- ko if: $data.source -->
        <h5>Source: <small data-bind="text: source"></small></h5>
        <!-- /ko -->

        <!-- ko if: $data.isResource -->
        <button class="btn btn-primary pull-right" data-bind="click: $parents[1].claim.bind($data, _id)">Curate This</button>
        <br>
        <!-- /ko -->
    </script>
    <script type="text/html" id="file">
        <h4><a data-bind="attr: {href: deep_url}, text: name"></a> (<span data-bind="if: is_registration">Registration </span>File)</h4>
        <h5>
            <!-- ko if: parent_url --> From: <a data-bind="attr: {href: parent_url}, text: parent_title || '' + ' /'"></a> <!-- /ko -->
            <!-- ko if: !parent_url --> From: <span data-bind="if: parent_title"><span data-bind="text: parent_title"></span> /</span> <!-- /ko -->
            <a data-bind="attr: {href: node_url}, text: node_title"></a>
        </h5>
        <!-- ko if: tags.length > 0 --> <div data-bind="template: 'tag-cloud'"></div> <!-- /ko -->
    </script>
    <script type="text/html" id="user">

        <div class="row">
            <div class="col-md-2">
                <img class="social-gravatar" data-bind="visible: gravatarUrl(), attr: {src: gravatarUrl()}">
            </div>
            <div class="col-md-10">
                <h4><a data-bind="attr: {href: url}, text: user"></a></h4>
                <p>
                    <span data-bind="visible: job_title, text: job_title"></span><!-- ko if: job_title && job --> at <!-- /ko -->
                    <span data-bind="visible: job, text: job"></span><!-- ko if: job_title || job --><br /><!-- /ko -->
                    <span data-bind="visible: degree, text: degree"></span><!-- ko if: degree && school --> from <!-- /ko -->
                    <span data-bind="visible: school, text: school"></span><!-- ko if: degree || school --><br /><!-- /ko -->
                </p>
                <!-- ko if: social -->
                <ul class="list-inline">
                    <li data-bind="visible: social.personal">
                        <a data-bind="attr: {href: social.personal}">
                            <i class="fa fa-globe social-icons" data-toggle="tooltip" title="Personal Website"></i>
                        </a>
                    </li>

                    <li data-bind="visible: social.twitter">
                        <a data-bind="attr: {href: social.twitter}">
                            <i class="fa fa-twitter social-icons" data-toggle="tooltip" title="Twitter"></i>
                        </a>
                    </li>
                    <li data-bind="visible: social.github">
                        <a data-bind="attr: {href: social.github}">
                            <i class="fa fa-github-alt social-icons" data-toggle="tooltip" title="Github"></i>
                        </a>
                    </li>
                    <li data-bind="visible: social.linkedIn">
                        <a data-bind="attr: {href: social.linkedIn}">
                            <i class="fa fa-linkedin social-icons" data-toggle="tooltip" title="LinkedIn"></i>
                        </a>
                    </li>
                    <li data-bind="visible: social.scholar">
                        <a data-bind="attr: {href: social.scholar}">
                            <img class="social-icons" src="/static/img/googlescholar.png"data-toggle="tooltip" title="Google Scholar">
                        </a>
                    </li>
                    <li data-bind="visible: social.impactStory">
                        <a data-bind="attr: {href: social.impactStory}">
                            <i class="fa fa-info-circle social-icons" data-toggle="tooltip" title="ImpactStory"></i>
                        </a>
                    </li>
                    <li data-bind="visible: social.orcid">
                        <a data-bind="attr: {href: social.orcid}">
                            <i class="fa social-icons" data-toggle="tooltip" title="ORCiD">iD</i>
                        </a>
                    </li>
                    <li data-bind="visible: social.researcherId">
                        <a data-bind="attr: {href: social.researcherId}">
                            <i class="fa social-icons" data-toggle="tooltip" title="ResearcherID">R</i>
                        </a>
                    </li>
                    <li data-bind="visible: social.researchGate">
                        <a data-bind="attr: {href: social.researchGate}">
                            <img class="social-icons" src="/static/img/researchgate.jpg" style="PADDING-BOTTOM: 7px" data-toggle="tooltip" title="ResearchGate"></i>
                        </a>
                    </li>
                    <li data-bind="visible: social.academiaInstitution + social.academiaProfileID">
                        <a data-bind="attr: {href: social.academiaInstitution + social.academiaProfileID}">
                            <i class="fa social-icons" data-toggle="tooltip" title="Academia">A</i>
                        </a>
                    </li>
                    <li data-bind="visible: social.baiduScholar">
                        <a data-bind="attr: {href: social.baiduScholar}">
                            <img class="social-icons" src="/static/img/baiduscholar.png"data-toggle="tooltip" style="PADDING-BOTTOM: 5px" title="Baidu Scholar">
                        </a>
                    </li>
                </ul>
                <!-- /ko -->
            </div>
        </div>

    </script>
    <script type="text/html" id="institution">
        <div class="row">
            <div class="col-md-2">
                <img class="img-circle" height="75px" width="75px" data-bind="attr: {src: logo_path}">
            </div>
            <div class="col-md-10">
                <h4><a data-bind="attr: {href: url}, text: name"></a></h4>
            </div>
        </div>
    </script>
    <script type="text/html" id="node">
      <!-- ko if: parent_url -->
      <h4><a data-bind="attr: {href: parent_url}, text: parent_title"></a> / <a data-bind="attr: {href: url}, text: title"></a></h4>
        <!-- /ko -->
        <!-- ko if: !parent_url -->
        <h4><span data-bind="if: parent_title"><span data-bind="text: parent_title"></span> /</span> <a data-bind="attr: {href: url}, text: title"></a></h4>
        <!-- /ko -->

        <p data-bind="visible: description"><strong>Description:</strong> <span data-bind="fitText: {text: description, length: 500}"></span></p>

        <!-- ko if: contributors.length > 0 -->
        <p>
            <strong>Contributors:</strong> <span data-bind="foreach: contributors">
                <!-- ko if: url -->
                    <a data-bind="attr: {href: url}, text: fullname"></a>
                <!-- /ko-->
                <!-- ko ifnot: url -->
                    <span data-bind="text: fullname"></span>
                <!-- /ko -->
            <!-- ko if: ($index()+1) < ($parent.contributors.length) -->&nbsp;- <!-- /ko -->
            </span>
        </p>
        <!-- /ko -->
      <!-- ko if: affiliated_institutions.length > 0 -->
        <p><strong>Affiliated institutions:</strong>
            <!-- ko foreach {data: affiliated_institutions, as: 'item'} -->
                <!-- ko if: item == $parent.affiliated_institutions[$parent.affiliated_institutions.length -1] -->
                <span data-bind="text: item"></span>
                <!-- /ko -->
                <!-- ko if: item != $parent.affiliated_institutions[$parent.affiliated_institutions.length -1] -->
                <span data-bind="text: item"></span>,
                <!-- /ko -->
            <!-- /ko -->
        </p>
        <!-- /ko -->
        <!-- ko if: tags.length > 0 -->
        <div data-bind="template: 'tag-cloud'"></div>
        <!-- /ko -->
        <p><strong>Jump to:</strong>
            <!-- ko if: n_wikis > 0 -->
            <a data-bind="attr: {href: wikiUrl}">Wiki</a> -
            <!-- /ko -->
            <a data-bind="attr: {href: filesUrl}">Files</a>
        </p>
    </script>
    <script type="text/html" id="project">
      <div data-bind="template: {name: 'node', data: $data}"></div>
    </script>
    <script type="text/html" id="component">
      <div data-bind="template: {name: 'node', data: $data}"></div>
    </script>
    <script type="text/html" id="registration">
        <!-- ko if: parent_url -->
        <h4><a data-bind="attr: {href: parent_url}, text: parent_title"></a> / <a data-bind="attr: {href: url}, text: title"></a>  (<span class="text-danger" data-bind="if: is_retracted">Withdrawn </span>Registration)</h4>
        <!-- /ko -->
        <!-- ko if: !parent_url -->
        <h4><span data-bind="if: parent_title"><span data-bind="text: parent_title"></span> /</span> <a data-bind="attr: {href: url}, text: title"></a>  (<span class="text-danger" data-bind="if: is_retracted">Withdrawn </span>Registration)</h4>
        <!-- /ko -->
        <strong><span data-bind="text: 'Date Registered: ' + dateRegistered['local'], tooltip: {title: dateRegistered['utc']}"></span></strong>

        <p data-bind="visible: description"><strong>Description:</strong> <span data-bind="fitText: {text: description, length: 500}"></span></p>

        <!-- ko if: contributors.length > 0 -->
        <p>
            <strong>Contributors:</strong> <span data-bind="foreach: contributors">
                <!-- ko if: url -->
                    <a data-bind="attr: {href: url}, text: fullname"></a>
                <!-- /ko-->
                <!-- ko ifnot: url -->
                    <span data-bind="text: fullname"></span>
                <!-- /ko -->


            <!-- ko if: ($index()+1) < ($parent.contributors.length) -->&nbsp;- <!-- /ko -->
            </span>
        </p>
        <!-- /ko -->
        <!-- ko if: tags.length > 0 -->
        <div data-bind="template: 'tag-cloud'"></div>
        <!-- /ko -->
        <p><strong>Jump to:</strong>
            <!-- ko if: n_wikis > 0 -->
            <a data-bind="attr: {href: wikiUrl}">Wiki</a> -
            <!-- /ko -->
            <a data-bind="attr: {href: filesUrl}">Files</a>
        </p>
    </script>
    <script id="tag-cloud" type="text/html">
        <p data-bind="visible: tags.length"><strong>Tags:</strong>
            <div data-bind="foreach: tags">
                <span class="tag pointer tag-container"
                      data-bind="click: $root.addTag.bind($parentContext, $data)">
                    <span class="tag-text" data-bind="text: $data"></span>
                    <i class="fa fa-times-circle remove-tag"
                       data-bind="click: $root.removeTag.bind($parentContext, $data)"></i>
                </span>
            </div>
        </p>
    </script>
</%def>

<%def name="javascript_bottom()">
    <script type="text/javascript">
        window.contextVars = $.extend(true, {}, window.contextVars, {
            search:true
        });
    </script>

    <script src=${"/static/public/js/search-page.js" | webpack_asset}></script>


</%def>
