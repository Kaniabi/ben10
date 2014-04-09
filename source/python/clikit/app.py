from .command import Command
import ConfigParser
import argparse
import os
import sys
import types



#===================================================================================================
# Exceptions
#===================================================================================================

class InvalidCommand(KeyError):
    """
    Exception raised when an unknown command is requested for execution.
    """
    pass



#===================================================================================================
# ConsolePlugin
#===================================================================================================
class ConsolePlugin():
    """
    Options and fixtures for console.
    Note that all Apps have a console, this plugin does not add the console per se, but only the options and fixtures
    associated with the console.
    """

    def __init__(self, console):
        self.__console = console


    def ConfigureOptions(self, parser):
        """
        Implements IClikitPlugin.ConfigureOptions
        """
        parser.add_argument(
            '-v',
            '--verbose',
            dest='console_verbosity',
            action='store_const',
            const=2,
            default=1,
            help='Emit verbose information'
        ),
        parser.add_argument(
            '-q',
            '--quiet',
            dest='console_verbosity',
            action='store_const',
            const=0,
            default=1,
            help='Emit only errors'
        ),
        parser.add_argument(
            '--no-color',
            dest='console_color',
            action='store_false',
            default=True,
            help='Do not colorize output'
        )


    def HandleOptions(self, opts):
        """
        Implements IClikitPlugin.HandleOptions
        """
        self.__console.verbosity = getattr(opts, 'console_verbosity', 1)


    def GetFixtures(self):
        """
        Implements IClikitPlugin.GetFixtures
        """
        return {
            'console_' : self.__console
        }



#===================================================================================================
# ConfPlugin
#===================================================================================================
class ConfPlugin():
    """
    Adds global configuration fixture to App.
    """

    def __init__(self, name, conf_defaults=None, conf_filename=None):
        """
        :param str name:
            The application name, used to deduce the configuration filename.
        :param dict conf_defaults:
            Default values for configuration.
            This is a dictionary of dictionaries. The outer dictionary has the configuration groups
            as keys. The inner dictionary maps names to values inside a group.
        :param str conf_filename:
            The configuration filename. If None generates a default name.
        """
        self.__name = name
        self.conf_defaults = conf_defaults or {}
        self.conf_filename = conf_filename or '~/.%(name)s'


    def ConfigureOptions(self, parser):
        """
        Implements IClikitPlugin.ConfigureOptions
        """
        return


    def HandleOptions(self, opts):
        """
        Implements IClikitPlugin.HandleOptions
        """
        pass


    def GetFixtures(self):
        """
        Implements IClikitPlugin.GetFixtures
        """

        class MyConfigParser(ConfigParser.SafeConfigParser):
            """
            Adds:
            * Filename, so it can "Save" the configuration file.
            """

            def __init__(self, filename):
                ConfigParser.SafeConfigParser.__init__(self)
                self.filename = filename
                self.read(self.filename)

            def Get(self, section, name):
                """
                Returns a value from a section/name.
                """
                return self.get(section, name)

            def Set(self, section, name, value):
                """
                Sets a value on a section.
                """
                return self.set(section, name, value)

            def Save(self):
                """
                Saves the configuration file.
                """
                self.write(file(self.filename, 'w'))


        def GetConfFilename():
            """
            Returns the full configuration file expanding users (~) and names (%(name)s).
            """
            return os.path.expanduser(self.conf_filename % {'name' : self.__name})


        def CreateConf():
            """
            Creates the configuration file applying the defaults values from self.conf_default.
            """
            filename = GetConfFilename()
            conf = MyConfigParser(filename)

            # Set the defaults in the object with the values from conf_default.
            for section, options in self.conf_defaults.iteritems():
                if not conf.has_section(section):
                    conf.add_section(section)
                for name, value in options.iteritems():
                    if not conf.has_option(section, name):
                        conf.set(section, name, str(value))

            return conf

        return {
            'conf_' : CreateConf(),
        }


#===================================================================================================
# MyArgumentParser
#===================================================================================================
class TooFewArgumentError(RuntimeError):
    pass

class MyArgumentParser(argparse.ArgumentParser):

    def error(self, message):
        """
        Overrides original implementation to avoid printing stuff on errors.
        All help and printing is done by clikit. "No soup for you", argparse.
        """
        if message == 'too few arguments':
            raise TooFewArgumentError()


#===================================================================================================
# App
#===================================================================================================
class App(object):
    """
    Command Line Interface Application.
    """

    def __init__(
            self,
            name,
            description='',
            color=True,
            colorama=True,
            conf_defaults=None,
            conf_filename=None,
            buffered_console=False,
        ):
        from .console import BufferedConsole, Console

        self.__name = name
        self.description = description
        self.__commands = []
        self.__custom_fixtures = {}

        if buffered_console:
            self.console = BufferedConsole(color=color)
        else:
            self.console = Console(color=color, colorama=colorama)

        self.plugins = {
            'conf' : ConfPlugin(self.__name, conf_defaults, conf_filename),
        }


    def __call__(self, func=None, **kwargs):
        """
        Implement the decorator behavior for App.

        There are two use cases:

        Case 1:
            @app(a=1, b=2)
            def foo()

        Case 2:
            @app
            def foo()

        :param callable func:
            Case 1: In this case, func is None.
            Case 2: In this case, func is the decorated function.

        :return:
            Case 1: Returns a replacement for the function.
            Case 2: Returns a "functor", which in turn returns a replacement for the function.
        """
        if func is None:
            def Decorator(func):
                """
                In "Case 1" we return a simple callable that registers the function then returns it
                unchanged.
                """
                return self.Add(func, **kwargs)
            return Decorator
        else:
            return self.Add(func)


    def Add(
            self,
            func,
            name=None,
            alias=None,
        ):
        """
        Adds a function as a subcommand to the application.

        :param <funcion> func: The function to add.
        :param str name: The name of the command. If not given (None) uses the function name.
        :param list(str) alias: A list of valid aliases for the same command.
        :return Command:
            Command instance for the given function.
        """
        def _GetNames(func, alias):
            """
            Returns a list of names considering the function and all aliases.

            :param funcion func:
            :param list(str) alias:
            """
            result = [self.ConvertToCommandName(name or func.__name__)]
            if alias is None:
                alias = []
            elif isinstance(alias, types.StringTypes):
                alias = [alias]
            else:
                alias = list(alias)
            result.extend(alias)
            return result

        assert not isinstance(func, Command), 'App.Add must receive a function/method, not a Command.'

        names = _GetNames(func, alias)
        command = Command(func, names)

        # Make sure none of the existing commands share a name.
        all_names = self.ListAllCommandNames()
        for i_name in command.names:
            if i_name in all_names:
                command = self.GetCommandByName(i_name)
                raise ValueError(
                    'Command name %s from %s.%s conflicts with name defined in %s.%s' %
                    (
                        i_name,
                        func.__module__, func.__name__,
                        command.func.__module__, command.func.__name__)
                    )

        self.__commands.append(command)
        return command


    def Fixture(self, func=None, name=None):
        """
        This is a decorator that registers a function as a custom fixture.

        Once registered, a command can request the fixture by adding its name as a parameter.

        """
        def _AddFixture(name, func):
            name = self.ConvertToFixtureName(name or func.__name__)
            self.__custom_fixtures[name] = func()

        if func is None:
            def Decorator(func):
                _AddFixture(name, func)
                return func
            return Decorator
        else:
            _AddFixture(name, func)
            return func


    @staticmethod
    def ConvertToCommandName(func_name):
        '''
        Converts a function name to a command name:
            - lower-case
            - dashes separates words

        The command name is used as the argument from the command line.

        Ex.
            CreateDb -> create-db

        :param str func_name:
            The function name, using camel cases standard.

        :return str:
        '''
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', func_name)
        return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()


    @staticmethod
    def ConvertToFixtureName(func_name):
        '''
        Converts a function name to a fixture name:
            - lower-case
            - underscores separates words
            - ends with an underscore

        The fixture name is used as a parameter of a Command function.

        Ex.
            MyDb -> my_db_

        :param str func_name:
            The function name, using camel cases standard.

        :return str:
        '''
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', func_name)
        result = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        if not result.endswith('_'):
            result += '_'
        return result


    def GetCommandByName(self, name):
        """
        Returns a command instance from the given __name.

        :param str __name:
        :return self._Command:
        """
        for j_command in self.__commands:
            if name in j_command.names:
                return j_command
        raise InvalidCommand(name)


    def ListAllCommandNames(self):
        """
        Lists all commands names, including all aliases.

        :return list(str):
        """
        result = []
        for j_command in self.__commands:
            result += j_command.names
        return result


    def GetFixtures(self, argv):
        """
        :return dict:
            Returns a dictionary mapping each available fixture to its implementation.
        """
        result = {
            'argv_' : argv,
        }
        result.update(self.__custom_fixtures)
        for i_plugin in self.plugins.itervalues():
            result.update(i_plugin.GetFixtures())

        return result


    RETCODE_OK = 0
    RETCODE_ERROR = 1

    def Main(self, argv=None):
        """
        Entry point for the commands execution.
        """
        self.plugins['console'] = ConsolePlugin(self.console)

        if argv is None:
            argv = sys.argv[1:]

        parser = self.CreateArgumentParser()
        opts, args = parser.parse_known_args(argv)

        # Print help for the available commands
        if not args:
            self.PrintHelp()
            return self.RETCODE_OK

        cmd, args = args[0], args[1:]

        try:
            command = self.GetCommandByName(cmd)

            # Print help for the specific command
            if opts.help:
                self.PrintHelp(command)
                return self.RETCODE_OK

            # Give plugins change to handle options
            for i_plugin in self.plugins.itervalues():
                i_plugin.HandleOptions(opts.__dict__)

            # Configure parser with command specific parameters/options
            command.ConfigureArgumentParser(parser)

            # Parse parameters/options
            try:
                opts = parser.parse_args(args)
            except TooFewArgumentError:
                self.console.PrintError('<red>ERROR: Too few arguments.</>', newlines=2)
                self.PrintHelp(command)
                return self.RETCODE_ERROR

            fixtures = self.GetFixtures(argv)
            result = command.Call(fixtures, opts.__dict__)
            if result is None:
                result = self.RETCODE_OK
            return result

        except InvalidCommand as exception:
            self.console.PrintError('<red>ERROR: Unknown command %s</>' % str(exception))
            self.PrintHelp()
            return self.RETCODE_ERROR


    def CreateArgumentParser(self):
        """
        Create a argument parser adding options from all plugins (ConfigureOptions)
        """
        r_parser = MyArgumentParser(
            prog=self.__name,
            add_help=False,
        )
        r_parser.add_argument('--help', action='store_true', help='Help about a command')
        for i_plugin in self.plugins.itervalues():
            i_plugin.ConfigureOptions(r_parser)
        return r_parser


    def PrintHelp(self, command=None):
        """
        Print help for all registered commands or an specific one.

        :param Command command: A command to print help or None to print the application help.
        """
        if command is None:
            self.console.PrintQuiet()
            self.console.PrintQuiet('Usage:')
            self.console.PrintQuiet('%s <subcommand> [options]' % self.__name, indent=1)

            self.console.PrintQuiet()
            self.console.PrintQuiet('Commands:')

            # Collect command names and description
            commands = []
            for i_command in self.__commands:
                command_names = [i for i in i_command.names]
                width = sum(map(len, command_names)) + (2 * (len(command_names) - 1))
                if self.console.color:
                    command_names = ['<teal>%s</>' % i for i in command_names]
                commands.append((width, ', '.join(command_names), i_command.description))

            # Prints in columns
            max_width = max([i[0] for i in commands])
            for i_width, i_names, i_description in commands:
                spaces = ' ' * ((max_width - i_width) + 3)
                self.console.PrintQuiet('%s%s%s' % (i_names, spaces, i_description), indent=1)
        else:
            self.console.PrintQuiet(command.description)
            self.console.PrintQuiet()
            self.console.Print(command.FormatHelp())


    def ExecuteCommand(self, cmd, *args, **kwargs):
        """
        Executes a command using normal parameters.

        :param str cmd:
            The name of a previously registered command to execute.

        :param *args:
            Arguments passed to the command function "as is".

        :param *kwargs:
            Keyword arguments passed to the command function "as is".

        TODO: This is not handling fixtures. It ALWAYS passes console as the first parameter.
        """
        from .console import BufferedConsole

        command = self.GetCommandByName(cmd)
        console = BufferedConsole()
        retcode = command(console, *args, **kwargs)
        if retcode is None:
            retcode = self.RETCODE_OK
        return retcode, console.GetOutput()


    def TestScript(self, script):
        """
        Executes a test script, containing command calls (prefixed by ">") and expected results.

        Example:
            app = App('ii')
            app = TestScript(Dedent(
                '''
                > ii list
                - alpha
                - bravo
                '''
            )

        :param str string:
            A multi-line string with command calls and expected results.
        """

        def Execute(cmd, output):
            retcode, obtained = self.TestCall(cmd)
            assert obtained.rstrip('\n') + '\n' == output.rstrip('\n') + '\n'

        cmd = None
        output = ''
        for i_line in script.splitlines():
            if i_line.startswith('>'):
                if cmd is not None:
                    Execute(cmd, output)
                    output = ''
                cmd = i_line[1:]
            else:
                output += i_line + '\n'

        if cmd is not None:
            Execute(cmd, output)


    def TestCall(self, cmd_line, extra_apps={}):
        '''
        Executes the given command line for test purposes.

        Example:
            app = App('ii')
            retcode, output = app.TestCall('ii list')

        :param str cmd_line:
            A command line to execute.
            The first parameter must be the app name as declared in this App instance constructor.

        :param dict(str : App):
            A list of extra-apps available for execution.
            By default only this App instance is available for executing in the command line. With
            this parameter one can add others utilitarian apps for testing.

        :return tuple(int, str):
            Returns the command return code and output.
        '''
        from .console import BufferedConsole
        from ben10.foundation.pushpop import PushPopAttr
        import shlex

        class UnknownApp(RuntimeError):

            def __init__(self, app, apps):
                RuntimeError.__init__(self, 'Unknown app "%s". Valid apps are: %s' % (app, ', '.join(apps)))

        apps = {
            self.__name : self,
        }
        apps.update(extra_apps)

        with PushPopAttr(self, 'console', BufferedConsole()):
            cmd_line = shlex.split(cmd_line)
            app_name, cmd_line = cmd_line[0], cmd_line[1:]
            app = apps.get(app_name)
            if app is None:
                raise UnknownApp(app_name, apps.keys())

            retcode = app.Main(cmd_line)
            return retcode, self.console.GetOutput()
