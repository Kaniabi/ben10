from ben10.foundation.string import Dedent
from clikit.app import App
from clikit.console import BufferedConsole, Console
import inspect
import pytest
import sys



#===================================================================================================
# TESTS
#===================================================================================================

class Test:
    """
    Tests for App class using py.test
    """

    def _TestMain(self, app, args, output, retcode=App.RETCODE_OK):
        assert app.Main(args.split()) == retcode
        assert app.console.GetOutput() == output


    def testSysArgv(self):
        def Case(console_, argv_, first, second):
            console_.Print('%s..%s' % (first, second))
            console_.Print(argv_)

        app = App('test', color=False, buffered_console=True)
        app.Add(Case)

        old_sys_argv = sys.argv
        sys.argv = [sys.argv[0], 'case', 'alpha', 'bravo']
        try:
            app.Main()
            assert app.console.GetOutput() == "alpha..bravo\n['case', 'alpha', 'bravo']\n"
        finally:
            sys.argv = old_sys_argv


    def testBufferedConsole(self):
        app = App('test', color=False, buffered_console=True)
        assert type(app.console) == BufferedConsole

        app = App('test', color=False)
        assert type(app.console) == Console


    def testHelp(self):

        def TestCmd(console_, first, second, option=1, option_yes=True, option_no=False):
            """
            This is a test.

            :param first: This is the first parameter.
            :param second: This is the second and last parameter.
            :param option: This must be a number.
            :param option_yes: If set, says yes.
            :param option_no: If set, says nop.
            """

        app = App('test', color=False, buffered_console=True)
        app.Add(TestCmd)

        self._TestMain(app, '', Dedent(
            """

            Usage:
                test <subcommand> [options]

            Commands:
                test-cmd   This is a test.

            """
            )
        )

        self._TestMain(app, '--help', Dedent(
            """

            Usage:
                test <subcommand> [options]

            Commands:
                test-cmd   This is a test.

            """
            )
        )

        self._TestMain(
            app,
            'test-cmd --help',
            Dedent(
                """
                    This is a test.

                    Usage:
                        test-cmd <first> <second> [--option=1],[--option_yes],[--option_no]

                    Parameters:
                        first   This is the first parameter.
                        second   This is the second and last parameter.

                    Options:
                        --option   This must be a number. [default: 1]
                        --option_yes   If set, says yes.
                        --option_no   If set, says nop.


                """
            )
        )

        self._TestMain(
            app,
            'test-cmd',
            Dedent(
                """
                    ERROR: Too few arguments.

                    This is a test.

                    Usage:
                        test-cmd <first> <second> [--option=1],[--option_yes],[--option_no]

                    Parameters:
                        first   This is the first parameter.
                        second   This is the second and last parameter.

                    Options:
                        --option   This must be a number. [default: 1]
                        --option_yes   If set, says yes.
                        --option_no   If set, says nop.


                """
            ),
            app.RETCODE_ERROR
        )


    def testApp(self):
        """
        Tests App usage and features.
        """

        def Case1(console_):
            """
            A "hello" message from case 1
            """
            console_.Print('Hello from case 1')

        def Case2(console_):
            """
            A "hello" message from case 2

            Additional help for this function is available.
            """
            console_.Print('Hello from case 2')

        def Case3(console_):
            console_.Print('Hello from case 3')

        app = App('test', color=False, buffered_console=True)
        app.Add(Case1, alias='cs')
        app.Add(Case2)
        case3_cmd = app.Add(Case3, alias=('c3', 'cs3'))

        # Test duplicate name
        with pytest.raises(ValueError):
            app.Add(case3_cmd.func, alias='cs')

        # Test commands listing
        assert app.ListAllCommandNames() == ['case1', 'cs', 'case2', 'case3', 'c3', 'cs3']

        # Tests all commands output
        self._TestMain(app, 'case1', 'Hello from case 1\n')
        self._TestMain(app, 'cs', 'Hello from case 1\n')
        self._TestMain(app, 'case2', 'Hello from case 2\n')
        self._TestMain(app, 'case3', 'Hello from case 3\n')
        self._TestMain(app, 'c3', 'Hello from case 3\n')
        self._TestMain(app, 'cs3', 'Hello from case 3\n')

        # Tests output when an invalid command is requested
        self._TestMain(app, 'INVALID', Dedent(
            """
            ERROR: Unknown command 'INVALID'

            Usage:
                test <subcommand> [options]

            Commands:
                case1, cs        A "hello" message from case 1
                case2            A "hello" message from case 2
                case3, c3, cs3   (no description)

            """),
            app.RETCODE_ERROR
    )


    def testConf(self, tmpdir):
        """
        Tests the configuration plugin (ConfPlugin)
        """
        conf_filename = tmpdir.join('ConfigurationCmd.conf')

        app = App(
            'test',
            color=False,
            conf_defaults={
                'group' : {
                    'value' : 'ALPHA',
                }
            },
            conf_filename=str(conf_filename),
            buffered_console=True
        )

        def ConfigurationCmd(console_, conf_):
            """
            Test Set/Get methods from configuration object.
            """
            console_.Print('conf_.filename: %s' % conf_.filename)
            console_.Print('group.value: %s' % conf_.Get('group', 'value'))

            conf_.Set('group', 'value', 'BRAVO')
            console_.Print('group.value: %s' % conf_.Get('group', 'value'))

            assert not conf_filename.check(file=1)
            conf_.Save()
            assert conf_filename.check(file=1)

        app.Add(ConfigurationCmd)

        self._TestMain(
            app,
            'configuration-cmd',
            'conf_.filename: %s\ngroup.value: ALPHA\ngroup.value: BRAVO\n' % conf_filename
        )

        # Creating an application with an existing configuration file.
        assert conf_filename.check(file=1)
        app = App(
            'test',
            color=False,
            conf_defaults={
                'group' : {
                    'value' : 'ALPHA',
                }
            },
            conf_filename=str(conf_filename),
            buffered_console=True
        )

        def Cmd(console_, conf_):
            console_.Print(conf_.filename)
            console_.Print(conf_.Get('group', 'value'))

        app.Add(Cmd)

        self._TestMain(
            app,
            'cmd',
            '%s\nBRAVO\n' % conf_filename
        )


    def testPositionalArgs(self):
        """
        >command alpha bravo
        alpha..bravo
        """
        app = App('test', color=False, buffered_console=True)

        def Command(console_, first, second):
            console_.Print('%s..%s' % (first, second))

        app.Add(Command)

        app.TestScript(inspect.getdoc(self.testPositionalArgs))


    def testOptionArgs(self):
        """
        >command
        1..2
        >command --first=alpha --second=bravo
        alpha..bravo
        """
        app = App('test', color=False, buffered_console=True)

        def Command(console_, first='1', second='2'):
            console_.Print('%s..%s' % (first, second))

        app.Add(Command)

        app.TestScript(inspect.getdoc(self.testOptionArgs))


    def testColor(self):
        app = App('test', color=True, buffered_console=True)

        assert app.console.color == True

        def Case():
            """
            This is Case.
            """

        app.Add(Case)

        self._TestMain(
            app,
            '',
            Dedent(
                """

                    Usage:
                        test <subcommand> [options]

                    Commands:
                        %(teal)scase%(reset)s   This is Case.

                """ % Console.COLOR_CODES
            )
        )


    def testColorama(self):
        """
        Importing colorama from inside pytest USED TO raise an exception:

            File "D:\Kaniabi\EDEn\dist\12.0-all\colorama-0.2.5\lib\site-packages\colorama\win32.py", line 64
            in GetConsoleScreenBufferInfo
            >           handle, byref(csbi))
            E       ArgumentError: argument 2: <type 'exceptions.TypeError'>: expected LP_CONSOLE_SCREEN_BUFFER_INFO
                                   instance instead of pointer to CONSOLE_SCREEN_BUFFER_INFO
        """
        import colorama


    def testFixture1(self):

        def MyFix():
            return 'This is a custom fixture'

        def Cmd(console_, my_fix_):
            console_.Print(my_fix_)

        app = App('test', color=True, buffered_console=True)
        app.Fixture(MyFix)
        app.Add(Cmd)

        self._TestMain(
            app,
            'cmd',
            'This is a custom fixture\n'
        )


    def testFixture2(self):
        def MyFix():
            return 'This is rubles.'

        def Cmd(console_, rubles_):
            console_.Print(rubles_)

        app = App('test', color=True, buffered_console=True)
        app.Fixture(MyFix, name='rubles')
        app.Add(Cmd)

        self._TestMain(
            app,
            'cmd',
            'This is rubles.\n'
        )


    def testExecuteCommand(self):

        def Cmd(console_, subject='World'):
            console_.Print('Hello, %s!' % subject)

        app = App('test', color=False, buffered_console=True)
        app.Add(Cmd)

        retcode, output = app.ExecuteCommand('cmd')
        assert retcode == app.RETCODE_OK
        assert output == 'Hello, World!\n'

        retcode, output = app.ExecuteCommand('cmd', 'Alpha')
        assert retcode == app.RETCODE_OK
        assert output == 'Hello, Alpha!\n'


    def testCommandDecorator(self):

        app = App('test', color=False, buffered_console=True)

        @app
        def Alpha(console_):
            console_.Print('Alpha')

        @app()
        def Bravo(console_):
            console_.Print('Bravo')

        app.ExecuteCommand('alpha') == (app.RETCODE_OK, 'Alpha\n')
        app.ExecuteCommand('bravo') == (app.RETCODE_OK, 'Bravo\n')


    def testFixtureDecorator(self):

        app = App('test', color=False, buffered_console=True)

        @app.Fixture
        def Alpha():
            return 'alpha'

        @app.Fixture()
        def Bravo():
            return 'bravo'

        def Command(console_, alpha_, bravo_):
            console_.Print('The names are: %(alpha_)s and %(bravo_)s.' % locals())

        app.Add(Command)

        self._TestMain(
            app,
            'command',
            Dedent(
                """
                    The names are: alpha and bravo.

                """
            )
        )
