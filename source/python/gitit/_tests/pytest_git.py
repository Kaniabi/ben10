        import re
        assert re.match('^git version 1\.[89].*\.\d+$', git('--version')[0]) is not None
            'Date:   2012-07-17 13:33:56 -0300',
            'Date:   2012-07-17 10:37:53 -0300',
            'Date:   2012-02-09 14:51:53 -0200',
            'Date:   2012-07-17 10:37:53 -0300\n\n'
            == '35ff01222f4c79baeccaf98ece11bebff9bec01c [2012-07-17 13:33:56 -0300]'
            == '35ff012  "Added new_file" [2012-07-17 13:33:56 -0300]'
    result.Execute('config --local user.name "test"', result.cloned_remote)
    result.Execute('config --local user.email "test@ben10.com"', result.cloned_remote)
    result.Execute('config --local log.date iso', result.cloned_remote)
    result.Execute('config --local commit.date iso', result.cloned_remote)