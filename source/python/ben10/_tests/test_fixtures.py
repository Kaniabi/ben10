from __future__ import unicode_literals
from ben10 import filesystem
from ben10.filesystem import CreateFile, StandardizePath
from ben10.fixtures import InstallFaultHandler, MultipleFilesNotFound
from ben10.foundation import handle_exception
from ben10.foundation.handle_exception import IgnoringHandleException
from ben10.foundation.string import Dedent
import faulthandler
import io
import os
import pytest


pytest_plugins = b'pytester'


def testEmbedData(embed_data, session_tmp_dir):
    expected_dir = StandardizePath(os.path.join(session_tmp_dir, 'data_fixtures__testEmbedData'))

    assert os.path.isdir(expected_dir)

    # Checking if all contents of pytest_fixtures is present
    assert os.path.isfile(embed_data.GetDataFilename('alpha.txt'))
    assert os.path.isfile(embed_data.GetDataFilename('alpha.dist-12.0-win32.txt'))
    assert os.path.isfile(embed_data.GetDataFilename('alpha.dist-12.0.txt'))

    # Checking auxiliary functions
    assert embed_data.GetDataDirectory() == expected_dir
    assert embed_data.GetDataFilename('alpha.txt') == expected_dir + '/alpha.txt'


@pytest.mark.parametrize(('foo',), [('a',), ('b',), ('c',)])
def testEmbedDataParametrize(embed_data, foo):
    '''
    asserts that we get unique data directories when mixing embed_data with pytest.mark.parametrize
    '''
    if foo == 'a':
        assert os.path.basename(embed_data.GetDataDirectory()) == 'data_fixtures__testEmbedDataParametrize_foo0_'
    if foo == 'b':
        assert os.path.basename(embed_data.GetDataDirectory()) == 'data_fixtures__testEmbedDataParametrize_foo1_'
    if foo == 'c':
        assert os.path.basename(embed_data.GetDataDirectory()) == 'data_fixtures__testEmbedDataParametrize_foo2_'


def testEmbedDataAssertEqualFiles(embed_data):
    CreateFile(embed_data.GetDataFilename('equal.txt'), 'This is alpha.txt')
    embed_data.AssertEqualFiles(
        'alpha.txt',
        'equal.txt'
    )

    CreateFile(embed_data.GetDataFilename('different.txt'), 'This is different.txt')
    with pytest.raises(AssertionError) as e:
        embed_data.AssertEqualFiles(
            'alpha.txt',
            'different.txt'
        )
    assert unicode(e.value) == Dedent(
        '''
        FILES DIFFER:
        {alpha}
        {different}
        HTML DIFF: {html}
        ***\w

        ---\w

        ***************

        *** 1 ****

        ! This is alpha.txt
        --- 1 ----

        ! This is different.txt
        '''.replace('\w', ' ').format(
            alpha=embed_data.GetDataFilename('alpha.txt'),
            different=embed_data.GetDataFilename('different.txt'),
            html=embed_data.GetDataFilename('alpha.diff.html'),
        )
    )


    with pytest.raises(MultipleFilesNotFound) as e:
        embed_data.AssertEqualFiles(
            'alpha.txt',
            'missing.txt'
        )

    assert (
        unicode(e.value)
        == 'Files not found: '
        'missing.txt,%s' % (embed_data.GetDataFilename('missing.txt'))
    )


def testEmbedDataFixture(testdir):
    """
    Test that embed_data files are kept around in the session tmp dir.
    """
    testdir.makeini('''
        [pytest]
        addopts = -p ben10.fixtures
    ''')
    testdir.makepyfile(test_foo='''
        def test_foo(embed_data):
            with open(embed_data['file.txt'], 'w') as f:
                f.write('contents')
    ''')
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(['*1 passed*'])

    tmp_dir = testdir.tmpdir.join('tmp')
    assert tmp_dir.exists()
    assert tmp_dir.join('session-tmp-dir-0/data_foo__test_foo/file.txt').read() == 'contents'


def testEmbedDataFixtureUnique(testdir):
    """
    Test that embed_data files always create a unique directory every time, even if a directory
    with the same name somehow already exists in the session-tmp-dir.
    """
    testdir.makeini('''
        [pytest]
        addopts = -p ben10.fixtures
    ''')
    testdir.makepyfile(test_m='''
        import os

        def test_foo(embed_data):
            this_dir = embed_data.GetDataDirectory()
            assert this_dir.endswith('_foo')
            next_test_dir = this_dir.replace('_foo', '_bar')
            os.mkdir(next_test_dir)

        def test_bar(embed_data):
            pass
    ''')
    result = testdir.runpytest('-v')
    result.stdout.fnmatch_lines([
        '*test_foo*PASSED',
        '*test_bar*PASSED',
    ])

    session_dir = testdir.tmpdir.join('tmp/session-tmp-dir-0')
    dirs_created = [os.path.basename(unicode(x)) for x in session_dir.listdir()]
    assert set(dirs_created) == {'data_m__test_foo', 'data_m__test_bar', 'data_m__test_bar-1'}


def testEmbedDataLongParametrize(testdir):
    """
    Test that embed_data successfully truncates and generates unique directories for tests
    with long parametrization parameters.
    """
    testdir.makeini('''
        [pytest]
        addopts = -p ben10.fixtures
    ''')
    testdir.makepyfile(test_m='''
        import os
        import pytest

        xx = b'x' * 1000
        yy = b'y' * 1000

        # two parameters have the same prefix up until the first 1000 chars
        @pytest.mark.parametrize('v', [xx + xx, xx + yy])
        def test_foo(embed_data, v):
            assert os.listdir(embed_data.GetDataDirectory()) == []
            with open(embed_data['foo.txt'], 'w'):
                pass
    ''')
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(['*2 passed*'])


_invalid_chars_for_paths = os.sep + os.pathsep


def testFaultHandler(pytestconfig):
    '''
    Make sure that faulthandler library is enabled during tests
    '''
    assert faulthandler.is_enabled()
    assert pytestconfig.fault_handler_file is None


def testFaultHandlerWithoutStderr(monkeypatch, embed_data):
    """
    Test we are enabling fault handler in a file based on sys.executable in case sys.stderr does not
    point to a valid file. This happens in frozen applications without a console.
    """
    import sys

    class Dummy(object):
        pass

    monkeypatch.setattr(sys, 'stderr', Dummy())
    monkeypatch.setattr(sys, 'executable', embed_data['myapp'])
    config = Dummy()
    InstallFaultHandler(config)
    assert config.fault_handler_file is not None
    assert config.fault_handler_file.name == embed_data['myapp'] + ('.faulthandler-%s.txt' % os.getpid())
    assert os.path.isfile(config.fault_handler_file.name)
    config.fault_handler_file.close()


def testHandledExceptions(handled_exceptions):
    assert not handled_exceptions.GetHandledExceptions()

    with IgnoringHandleException():
        try:
            raise RuntimeError('test')
        except:
            handle_exception.HandleException()

    assert len(handled_exceptions.GetHandledExceptions()) == 1

    with pytest.raises(AssertionError):
        handled_exceptions.RaiseFoundExceptions()

    handled_exceptions.ClearHandledExceptions()


def testDataRegressionFixture(testdir, monkeypatch):
    """
    :type testdir: _pytest.pytester.TmpTestdir

    :type monkeypatch: _pytest.monkeypatch.monkeypatch
    """
    import sys
    import yaml

    testdir.makeini('''
        [pytest]
        addopts = -p ben10.fixtures
    ''')

    monkeypatch.setattr(sys, 'GetData', lambda: {'contents': 'Foo', 'value': 10}, raising=False)
    source = '''
        import sys
        def test_1(data_regression):
            contents = sys.GetData()
            data_regression.Check(contents)
    '''
    testdir.makepyfile(test_file=source)

    # First run fails because there's no yml file yet
    result = testdir.inline_run()
    result.assertoutcome(failed=1)

    def GetYmlContents():
        yaml_filename = str(testdir.tmpdir / 'test_file' / 'test_1.yml')
        assert os.path.isfile(yaml_filename)
        with open(yaml_filename) as f:
            return yaml.load(f)

    # ensure now that the file was generated and the test passes
    assert GetYmlContents() == {'contents': 'Foo', 'value': 10}
    result = testdir.inline_run()
    result.assertoutcome(passed=1)

    # changing the regression data makes the test fail (file remains unchanged)
    monkeypatch.setattr(sys, 'GetData', lambda: {'contents': 'Bar', 'value': 20}, raising=False)
    result = testdir.inline_run()
    result.assertoutcome(failed=1)
    assert GetYmlContents() == {'contents': 'Foo', 'value': 10}

    # force regeneration (test fails again)
    result = testdir.inline_run('--force-regen')
    result.assertoutcome(failed=1)
    assert GetYmlContents() == {'contents': 'Bar', 'value': 20}

    # test should pass again
    result = testdir.inline_run()
    result.assertoutcome(passed=1)


def testDataRegressionFixtureFullPath(testdir, tmpdir):
    """
    Test data_regression with ``fullpath`` parameter.

    :type testdir: _pytest.pytester.TmpTestdir
    """
    fullpath = tmpdir.join('full/path/to').ensure(dir=1).join('contents.yaml')
    assert not fullpath.isfile()

    testdir.makeini('''
        [pytest]
        addopts = -p ben10.fixtures
    ''')

    source = '''
        def test(data_regression):
            contents = {'data': [1, 2]}
            data_regression.Check(contents, fullpath=%s)
    ''' % (repr(str(fullpath)))
    testdir.makepyfile(test_foo=source)
    # First run fails because there's no yml file yet
    result = testdir.inline_run()
    result.assertoutcome(failed=1)

    # ensure now that the file was generated and the test passes
    assert fullpath.isfile()
    result = testdir.inline_run()
    result.assertoutcome(passed=1)


def testDataRegressionFixtureNoAliases(testdir):
    """
    YAML standard supports aliases as can be seen here:
    http://pyyaml.org/wiki/PyYAMLDocumentation#Aliases.

    Even though this is a resourceful feature, data regression intends to be as human readable as
    possible and it was deemed that YAML aliases make it harder for developers to understand
    contents.

    This test makes sure data regression never uses aliases when dumping expected file to YAML.

    :type testdir: _pytest.pytester.TmpTestdir
    """
    testdir.makeini('''
        [pytest]
        addopts = -p ben10.fixtures
    ''')

    source = '''
        def test(data_regression):
            red = (255, 0, 0)
            green = (0, 255, 0)
            blue = (0, 0, 255)

            contents = {
                'color1': red,
                'color2': green,
                'color3': blue,
                'color4': red,
                'color5': green,
                'color6': blue,
            }
            data_regression.Check(contents)
    '''
    testdir.makepyfile(test_file=source)

    result = testdir.inline_run()
    result.assertoutcome(failed=1)

    with open(os.path.join(unicode(testdir.tmpdir), 'test_file', 'test.yml'), 'rb') as yaml_file:
        yaml_file_contents = yaml_file.read()
        assert yaml_file_contents == '''\
color1:
- 255
- 0
- 0
color2:
- 0
- 255
- 0
color3:
- 0
- 0
- 255
color4:
- 255
- 0
- 0
color5:
- 0
- 255
- 0
color6:
- 0
- 0
- 255
'''

    result = testdir.inline_run()
    result.assertoutcome(passed=1)


def testSessionTmpDir(testdir):

    testdir.makeini('''
        [pytest]
        addopts = -p ben10.fixtures
    ''')

    source = '''
        import os
        def test_1(session_tmp_dir):
            assert os.path.exists(session_tmp_dir)
            for i in xrange(10):
                filename = os.path.join(session_tmp_dir, 'file%d.txt' % i)
                if not os.path.exists(filename):
                    file(filename, 'w')
                    break
    '''
    testdir.makepyfile(test_file=source)

    def CheckSessionDir(session_dir, contents):
        assert session_dir.exists()
        assert set(os.listdir(unicode(session_dir))) == contents

    result = testdir.inline_run()
    result.assertoutcome(passed=1)

    # Check directories created
    tmp_dir = testdir.tmpdir.join('tmp')
    assert tmp_dir.exists()

    session_0_dir = tmp_dir.join('session-tmp-dir-0')
    CheckSessionDir(session_0_dir, {'.lock', 'file0.txt'})

    # New run, new session tmp dir
    result = testdir.inline_run()
    result.assertoutcome(passed=1)

    session_1_dir = tmp_dir.join('session-tmp-dir-1')
    CheckSessionDir(session_1_dir, {'.lock', 'file0.txt'})

    # Check if we can re-use the last session tmp dir
    result = testdir.inline_run('--last-session-tmp-dir')
    result.assertoutcome(passed=1)
    # Make sure the test created a new file
    CheckSessionDir(session_1_dir, {'.lock', 'file0.txt', 'file1.txt'})

    # Check if we can re-use a previous existing tmp dir
    result = testdir.inline_run('--session-tmp-dir=%s' % unicode(session_0_dir))
    result.assertoutcome(passed=1)
    # Make sure the test created a new file
    CheckSessionDir(session_0_dir, {'.lock', 'file0.txt', 'file1.txt'})


def testSessionTmpDirXDist(testdir):
    testdir.makeini('''
        [pytest]
        addopts = -p ben10.fixtures
    ''')

    source = '''
        import os
        import pytest

        @pytest.mark.parametrize('i', range(4))
        def test_foo(i, session_tmp_dir):
            assert os.path.isdir(session_tmp_dir)
    '''
    testdir.makepyfile(test_file=source)

    result = testdir.inline_run('-n2')
    result.assertoutcome(passed=4)
    assert {'session-tmp-dir-0'}.issubset(os.listdir(str(testdir.tmpdir.join('tmp'))))

    result = testdir.inline_run('-n4')
    result.assertoutcome(passed=4)
    assert {'session-tmp-dir-0', 'session-tmp-dir-1'}.issubset(os.listdir(str(testdir.tmpdir.join('tmp'))))


def testFakeTr(testdir, embed_data):
    testdir.makeini('''
        [pytest]
        addopts = -p ben10.fixtures
    ''')

    foo_ts = embed_data['foo.ts']
    bar_ts = embed_data['bar.ts']
    source = '''
        def test_foo(fake_tr):
            fake_tr.SetRelativeLocation(None)
            fake_tr.AddTranslations('{}')
            fake_tr.AddTranslations('{}')

            assert tr('foo') == 'translated foo'
            assert tr('bar') == 'translated bar'
    '''.format(foo_ts, bar_ts)

    test_file = testdir.makepyfile(test_file=source)

    with io.open(foo_ts, 'w', encoding='utf-8') as foo_ts_file:
        foo_ts_file.write('''\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.0" language="en_US">
<context>
    <name>test_file</name>
    <message>
        <location filename="{}" line="42"/>
        <source>foo</source>
        <translation>translated foo</translation>
    </message>
</context>
</TS>
'''.format(filesystem.StandardizePath(str(test_file)))
        )

    with io.open(bar_ts, 'w', encoding='utf-8') as foo_ts_file:
        foo_ts_file.write('''\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.0" language="en_US">
<context>
    <name>test_file</name>
    <message>
        <location filename="{}" line="42"/>
        <source>bar</source>
        <translation>translated bar</translation>
    </message>
</context>
</TS>
'''.format(filesystem.StandardizePath(str(test_file)))
        )

    result = testdir.inline_run()
    result.assertoutcome(passed=1)
