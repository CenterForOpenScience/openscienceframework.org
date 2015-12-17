from website.addons.osfstorage import settings as osfstorage_settings


def create_test_file(node, user):
    osfstorage = node.get_addon('osfstorage')
    root_node = osfstorage.get_root()
    test_file = root_node.append_file('test_file')
    test_file.create_version(user, {
        'object': '06d80e',
        'service': 'cloud',
        osfstorage_settings.WATERBUTLER_RESOURCE: 'osf',
    }, {
        'size': 1337,
        'contentType': 'img/png'
    }).save()
    return test_file
