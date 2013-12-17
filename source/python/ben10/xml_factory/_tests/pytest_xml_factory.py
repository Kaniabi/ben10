from StringIO import StringIO
from ben10.foundation.string import Dedent
from ben10.xml_factory import WritePrettyXML, WritePrettyXMLElement, XmlFactory
from xml.etree import ElementTree
import pytest
import sys



pytest_plugins = ["ben10.fixtures"]



#===================================================================================================
# Test
#===================================================================================================
class Test(object):

    def testSimplest(self):
        '''
        <?xml version="1.0" ?>
        <user>
          <name>Alpha</name>
          <login>Bravo</login>
        </user>
        '''
        factory = XmlFactory('user')
        factory['name'] = 'Alpha'
        factory['login'] = 'Bravo'

        assert (
            factory.GetContent(xml_header=True)
            == Dedent(self.testSimplest.__doc__)
        )


    def testSimple(self):
        '''
        <user>
          <name>Alpha</name>
          <login>Bravo</login>
          <location>
            <city>Charlie</city>
          </location>
        </user>
        '''
        factory = XmlFactory('user')
        factory['name'] = 'Alpha'
        factory['login'] = 'Bravo'
        factory['location/city'] = 'Charlie'

        assert (
            factory.GetContent()
            == Dedent(self.testSimple.__doc__)
        )


    def testAttributes(self):
        '''
        <root>
          <alpha one="1" two="2">Alpha</alpha>
          <bravo>
            <charlie three="3"/>
          </bravo>
        </root>
        '''
        factory = XmlFactory('root')
        factory['alpha'] = 'Alpha'
        factory['alpha@one'] = '1'
        factory['alpha@two'] = '2'
        factory['bravo/charlie@three'] = '3'

        assert (
            factory.GetContent()
            == Dedent(self.testAttributes.__doc__)
        )


    def testRepeatingTags(self):
        '''
        <root>
          <elements>
            <name>Alpha</name>
            <name>Bravo</name>
            <name>Charlie</name>
          </elements>
          <components>
            <component>
              <name>Alpha</name>
            </component>
            <component>
              <name>Bravo</name>
            </component>
            <component>
              <name>Charlie</name>
            </component>
          </components>
        </root>
        '''
        factory = XmlFactory('root')
        factory['elements/name'] = 'Alpha'
        factory['elements/name+'] = 'Bravo'
        factory['elements/name+'] = 'Charlie'

        factory['components/component+/name'] = 'Alpha'
        factory['components/component+/name'] = 'Bravo'
        factory['components/component+/name'] = 'Charlie'

        assert (
            factory.GetContent()
            == Dedent(self.testRepeatingTags.__doc__)
        )


    def testHudsonJob(self):
        '''
        <project>
          <actions/>
          <description/>
          <logRotator>
            <daysToKeep>7</daysToKeep>
            <numToKeep>7</numToKeep>
          </logRotator>
          <keepDependencies>false</keepDependencies>
          <properties/>
          <scm class="hudson.scm.SubversionSCM">
            <useUpdate>true</useUpdate>
            <excludedRegions/>
            <excludedUsers/>
            <excludedRevprop/>
          </scm>
          <assignedNode>KATARN</assignedNode>
          <canRoam>false</canRoam>
          <disabled>false</disabled>
          <blockBuildWhenUpstreamBuilding>true</blockBuildWhenUpstreamBuilding>
          <concurrentBuild>false</concurrentBuild>
          <buildWrappers/>
          <customWorkspace>WORKSPACE</customWorkspace>
        </project>
        '''
        factory = XmlFactory('project')
        factory['actions']
        factory['description']
        factory['logRotator/daysToKeep'] = '7'
        factory['logRotator/numToKeep'] = '7'
        factory['keepDependencies'] = 'false'
        factory['properties']
        factory['scm@class'] = 'hudson.scm.SubversionSCM'
        factory['scm/useUpdate'] = 'true'
        factory['scm/excludedRegions']
        factory['scm/excludedUsers']
        factory['scm/excludedRevprop']
        factory['assignedNode'] = 'KATARN'
        factory['canRoam'] = 'false'
        factory['disabled'] = 'false'
        factory['blockBuildWhenUpstreamBuilding'] = 'true'
        factory['concurrentBuild'] = 'false'
        factory['buildWrappers']
        factory['customWorkspace'] = 'WORKSPACE'

        assert (
            factory.GetContent()
            == Dedent(self.testHudsonJob.__doc__)
        )


    def testTriggerClass(self):
        '''
        <root>
          <triggers class="vector"/>
        </root>
        '''
        # Simulating the use for HudsonJobGenerator._CreateTriggers
        factory = XmlFactory('root')
        triggers = factory['triggers']
        triggers['@class'] = 'vector'

        assert (
            factory.GetContent()
            == Dedent(self.testTriggerClass.__doc__)
        )


    def testTypeError(self):
        with pytest.raises(TypeError):
            XmlFactory(9)


    def testPrettyXMLToStream(self, embed_data):
        '''
        <root>
          <alpha enabled="true">
            <bravo>
              <charlie/>
            </bravo>
            <bravo.one/>
            <delta>XXX</delta>
          </alpha>
        </root>
        '''
        iss = file(embed_data['input.xml'], 'r')
        oss = StringIO()

        WritePrettyXML(iss, oss)

        assert oss.getvalue() == Dedent(self.testPrettyXMLToStream.__doc__)


    def testPrettyXMLToFile(self, embed_data):
        in_ss = file(embed_data['input.xml'])

        obtained_filename = embed_data['pretty.obtained.xml']
        WritePrettyXML(in_ss, obtained_filename)

        embed_data.AssertEqualFiles('pretty.expected.xml', obtained_filename)


    def testEscape(self):
        element = ElementTree.Element('root')
        element.attrib['name'] = '<no>'
        element.text = '> 3'
        oss = StringIO()
        WritePrettyXMLElement(oss, element)
        assert oss.getvalue() == '<root name="&lt;no&gt;">&gt; 3</root>'

        element = ElementTree.fromstring(oss.getvalue())
        assert element.attrib['name'] == '<no>'
        assert element.text == '> 3'



#===================================================================================================
# Entry Point
#===================================================================================================
if __name__ == '__main__':
    # Executes with specific coverage.
    retcode = pytest.main(['--cov-report=term-missing', '--cov=ben10.xml_factory', __file__])
    sys.exit(retcode)
