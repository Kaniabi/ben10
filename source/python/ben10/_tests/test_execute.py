# coding: UTF-8
from __future__ import unicode_literals
from ben10.debug import StripDebugRefs
from ben10.execute import (DEFAULT_ENCODING, EnvironmentContextManager, Execute, ExecuteNoWait,
    ExecutePython, GetSubprocessOutput, GetSubprocessOutputChecked, PrintEnvironment)
from ben10.foundation.exceptions import ExceptionToUnicode
from ben10.foundation.string import Dedent
from txtout.txtout import TextOutput
import io
import mock
import os
import pytest
import subprocess
import sys
import time



#===================================================================================================
# Test
#===================================================================================================
class Test(object):

    def _AssertExecute(self, expected_output, *args, **kwargs):
        if 'input' not in kwargs:
            # Also tests "GetSubprocessOutput" variation if there is no "input" in the test.
            obtained_output, obtained_retcode = GetSubprocessOutput(*args, **kwargs)
            assert obtained_retcode == 0
            self._AssertOutput(obtained_output.splitlines(), expected_output)

        obtained_output = Execute(*args, **kwargs)
        self._AssertOutput(obtained_output, expected_output)


    def _AssertOutput(self, obtained_output, expected_output):
        # Removes known debug files:
        # - Coverage.py warning (travis-ci)
        # - pydev debugging: (inside PyCharm IDE)
        obtained_output = [i for i in obtained_output if not i.startswith("Coverage.py warning:")]
        obtained_output = [i for i in obtained_output if not i.startswith("pydev debugger: ")]
        obtained_output = '\n'.join(obtained_output)
        obtained_output = obtained_output.lstrip('\n')

        assert obtained_output == expected_output


    def testErrorWithIgnoreAutoQuote(self):
        '''
        Tests a bug that messed up the error message when using a string command line with
        ignore_auto_quote. .. seealso:: BEN-65
        '''
        with pytest.raises(RuntimeError) as e:
            Execute('unicode command line', ignore_auto_quote=True)
        assert 'command_line::\n    unicode command line' in ExceptionToUnicode(e.value)


    def testUnknownFileUnicodePath(self):
        # This should raise an error because that file does not exist
        with pytest.raises(RuntimeError) as e:
            Execute('ã_míssing_file dóit')

        # We were able to read the exception and print out the complete information
        error_message = unicode(e.value)
        assert 'environment::' in error_message
        assert 'current working dir::' in error_message
        assert 'command_line::\n    ã_míssing_file' in error_message


    def testExecute(self, embed_data):
        execute_py = os.path.normcase(embed_data['testExecute.py_'])
        self._AssertExecute(
            Dedent(
                '''
                    testExecute
                    Arguments:
                    - 0 - %s
                    - 1 - alpha
                    - 2 - bravo
                ''' % execute_py
            ),
            ['python', execute_py, 'alpha', 'bravo']
        )

        # Tests string argument (instead of list) and its splitting algorithm.
        self._AssertExecute(
            Dedent(
                r'''
                    testExecute
                    Arguments:
                    - 0 - %s
                    - 1 - alpha
                    - 2 - bravo
                    - 3 - charlie is number three
                    - 4 - delta
                '''.replace('\\n', os.linesep) % execute_py
            ),
            'python %(testExecute.py_)s alpha bravo "charlie is number three" delta' % embed_data,
        )


    @pytest.mark.skipif('sys.platform != "win32"')
    def testExecuteBat(self, embed_data):

        def DoTest(slash):
            python_filename = os.path.normcase(embed_data.GetDataFilename('testExecute.py_'))
            cmd_filename = embed_data.GetDataDirectory() + slash + 'testExecute.bat'
            self._AssertExecute(
                Dedent(
                    r'''
                        testExecute
                        Arguments:
                        - 0 - %s
                        - 1 - alpha
                        - 2 - bravo
                    '''.replace('\\n', os.linesep) % python_filename
                ),
                '%s alpha bravo' % cmd_filename,
            )

        DoTest('\\')

        # On Windows, we can't use local path using POSIX slashes.
        # It works for full path using POSIX slashes and local path with Windows slashes.
        # We had to change the command line if we find that case.
        DoTest('/')


    def testExecuteInput(self, embed_data):
        self._AssertExecute(
            Dedent(
                '''
                    testExecuteInput: Hello, planet earth!
                '''
            ),
            ['python', embed_data.GetDataFilename('testExecuteInput.py_')],
            input='planet earth',
        )


    @pytest.mark.slow
    def testExecuteNoWait(self, embed_data):
        text_filename = embed_data['testExecuteNoWait.txt']

        assert not os.path.isfile(text_filename)

        process = ExecuteNoWait(
            ['python', 'testExecuteNoWait.py_'],
            cwd=embed_data.GetDataDirectory(),
        )

        try:
            # The file was not yet generated since the scripts waits a bit to create it.
            assert not os.path.isfile(text_filename)

            # Wait for the script create the file
            for _i in xrange(50):
                time.sleep(0.1)
                if os.path.isfile(text_filename):
                    break
            else:
                # Now the file exists
                assert os.path.isfile(text_filename)
        finally:
            try:
                # Sleep again to avoid access error to the file testExecuteNotWait.txt
                time.sleep(0.3)
                process.terminate()
            except ImportError:
                raise  # Might happen if we can't find win32api
            except:
                pass  # Ignore any other errors on the kill process.


    @mock.patch('subprocess.Popen', autospec=True)
    def testExecuteNoWaitNewConsole(self, mock_popen):
        ExecuteNoWait(['my_command', '--args'], new_console=True)

        if sys.platform == 'win32':
            mock_popen.assert_called_once_with(
                ['my_command', '--args'],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                env=os.environ
            )
        else:
            mock_popen.assert_called_once_with(
                ['xterm', '-e', 'my_command', '--args'],
                env=os.environ
            )


    def testPrintEnvironment(self, embed_data):
        # Create a fake environment
        environment = {
            'var1' : 'value1',
            'var2' : 'value2',
            'PATH' : os.pathsep.join(['path1', 'path2']),
            'PYTHONPATH' : os.pathsep.join(['pythonpath1', 'pythonpath2']),

        }

        # Prepare a controled text output
        obtained = embed_data.GetDataFilename('testPrintEnvironment.txt')

        obtained_file = io.open(obtained, 'w')
        try:
            output = TextOutput(obtained_file)
            PrintEnvironment(environment, output)
        finally:
            obtained_file.close()

        # Compare file contents
        embed_data.AssertEqualFiles(
            obtained,
            'testPrintEnvironment.expected.txt'
        )


    def testEnvironmentContextManager(self, embed_data):
        assert 'testEnvironmentContextManager' not in os.environ

        with EnvironmentContextManager({'testEnvironmentContextManager':''}):
            assert 'testEnvironmentContextManager' in os.environ

        assert 'testEnvironmentContextManager' not in os.environ


    def testIfAPythonProgramReceivesUnicodeArgv(self, embed_data):
        '''
        A spawned python process should be able to access the arguments as unicode.
        '''
        python_script = embed_data['testIfAPythonProgramReceivesUnicodeArgv.py']
        input_file = embed_data['input_file_latin1_ação.txt']

        output, retcode = ExecutePython(python_script, (input_file,))

        assert output == 'OK\n', "Unexpected output:\n%s" % output


    def testPythonExecute(self, embed_data):
        obtained_output, retcode = ExecutePython(embed_data.GetDataFilename('testPythonExecute.py_'))
        assert obtained_output == 'testPythonExecute: Hello, world!\n'


    def testGetSubprocessOutputCheckedNonZero(self, embed_data):
        command_line = [sys.executable, embed_data.GetDataFilename('testHelloExitOne.py_')]
        with pytest.raises(subprocess.CalledProcessError) as exc_info:
            GetSubprocessOutputChecked(command_line)
        assert StripDebugRefs(exc_info.value.output, end_only=False).strip() == 'Hello, world!'
        assert exc_info.value.returncode == 1
        assert exc_info.value.cmd == command_line


    def testGetSubprocessOutputCheckedSuccess(self, embed_data):
        command_line = [sys.executable, embed_data.GetDataFilename('testPythonExecute.py_')]
        assert StripDebugRefs(GetSubprocessOutputChecked(command_line), end_only=False).strip() == "testPythonExecute: Hello, world!"
