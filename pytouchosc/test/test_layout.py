import unittest
import os
import sys

from StringIO import StringIO
from zipfile import ZipFile
from lxml import etree

sys.path.append(os.path.abspath('../src'))
from pytouchosc.layout import Layout

layoutPath = os.path.abspath('./layouts')
layoutFile = 'ROS-Demo-iPad.touchosc'
layoutBare = 'index.xml'

class LayoutTest(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(layoutPath, layoutFile)
        self.layout = Layout.createFromExisting(self.path)
        
    def test_getNumberTabpages(self):
        self.assertEqual(self.layout.getNumberTabpages(),2)
        
    def test_getTabpageNames_base64(self):
        tabpageNames = self.layout.getTabpageNames(encoded=True)
        self.assertEqual(tabpageNames[0],"MQ==")
        self.assertEqual(tabpageNames[1],"VGV4dERlbW8=")
            
    def test_getTabpageNames_plainText(self):
        tabpageNames = self.layout.getTabpageNames()
        self.assertEqual(tabpageNames[0],'1')
        self.assertEqual(tabpageNames[1],'TextDemo')
        
    def test_walkDict(self):
        aDict = {'toggle1': {None: 0.0, 'z': False}}
        testDict = {'/toggle1': 0.0, '/toggle1/z': False}
        newDict = dict(self.layout.walkDict(aDict))
        self.assertEqual(newDict, testDict)
        
    def test_walkDict_withPath(self):
        aDict = {'toggle1': {None: 0.0, 'z': False}}
        testDict = {'/1/toggle1': 0.0, '/1/toggle1/z': False}
        path = '/1'
        newDict = dict(self.layout.walkDict(aDict, path))
        self.assertEqual(newDict, testDict)
        # Check for side effects
        self.assertEqual(path,'/1')

    def test_setOrientation(self):
        self.layout.orientation = 'vertical'
        self.assertEqual(self.layout.orientation, 'vertical')
        self.layout.orientation = 'horizontal'
        self.assertEqual(self.layout.orientation, 'horizontal')
        self.layout.orientation = 'vertical'
        self.assertEqual(self.layout.orientation, 'vertical')
        self.layout.orientation = 'horizontal'
        self.assertEqual(self.layout.orientation, 'horizontal')
        with self.assertRaises(ValueError) as cm:
            self.layout.orientation = 'bob'


class LayoutTest_CreateFromExistingZip(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(layoutPath, layoutFile)
        self.layout = Layout.createFromExisting(self.path)

    def testCreateFromExisting(self):
        self.assertIsInstance(self.layout,Layout,"Not an instance")
        
    def testCreateFromExistingMode(self):
        self.assertEqual(self.layout.mode,"1","Mode isn't iPad")
        
    def testCreateFromExistingOrientation(self):
        self.assertEqual(self.layout.orientation,"horizontal","Orientation wrong")
        
    def testCreateFromExistingVersion(self):
        self.assertEqual(self.layout.version,"10")

    def testCreateFromExistingName(self):
        self.assertEqual(self.layout.name, "ROS-Demo-iPad")
 

class LayoutTest_CreateFromExistingFile(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(layoutPath, layoutBare)
        self.layout = Layout.createFromExisting(self.path)

    def testCreateFromExisting(self):
        self.assertIsInstance(self.layout,Layout,"Not an instance")
        
    def testCreateFromExistingMode(self):
        self.assertEqual(self.layout.mode,"1","Mode isn't iPad")
        
    def testCreateFromExistingOrientation(self):
        self.assertEqual(self.layout.orientation,"horizontal","Orientation wrong")
        
    def testCreateFromExistingVersion(self):
        self.assertEqual(self.layout.version,"10")

    def testCreateFromExistingName(self):
        """Creating from an XML file should not set name"""
        self.assertEqual(self.layout.name, None)


class LayoutWriteTest(unittest.TestCase):
    def setUp(self):
        self.layoutFile = layoutFile
        self.layoutPath = layoutPath
        self.layoutJoinPath = os.path.join(self.layoutPath, self.layoutFile)

        self.layout = Layout.createFromExisting(self.layoutJoinPath)

        self.testFile = 'test'
        self.testFileExt = 'test.touchosc'
        self.testPath = layoutPath
        self.testJoinPath = os.path.join(self.testPath, self.testFileExt)

    def tearDown(self):
        """Clean up after ourselves if the file was written"""
        if os.path.exists(self.testJoinPath):
            os.remove(self.testJoinPath)

    def test_writeToFile_badPath(self):
        """Should fail on non-existant path"""
        with self.assertRaises(ValueError) as cm:
            self.layout.writeToFile('a','test.touchosc')
        self.assertEqual(cm.exception.message, "path does not exist: 'a'")

    def test_writeToFile_unwritablePath(self):
        """Should fail on an unwritable path"""
        # First check to make sure /root exists and is not writable
        if not os.path.isdir('/bin'):
            self.fail("/bin doesn't exist")
        if os.access('/bin', os.W_OK):
            self.fail("/bin is writable, stopping")
        
        with self.assertRaises(IOError) as cm:
            self.layout.writeToFile('/bin', 'test')
        self.assertEqual(cm.exception.message, "Permission Denied: '/bin'")

    def test_writeToFile_withExtension(self):
        """Should check to see if the argument already has the extension, and not add another"""
        self.layout.writeToFile(self.testPath, self.testFileExt)

        self.assertFalse(os.path.exists(self.testJoinPath + '.touchosc'))
        self.assertTrue(os.path.exists(self.testJoinPath), "Didn't create file")

    def test_writeToFile_withoutExtension(self):
        """Should check to see if the argument doesn't have the extension, and add it"""
        self.layout.writeToFile(self.testPath, self.testFile)

        self.assertFalse(os.path.exists(self.testJoinPath + '.touchosc'))
        self.assertTrue(os.path.exists(self.testJoinPath), "Didn't create file")

    def test_writeToFile_alreadyExists(self):
        """Raise an IOError if the file already exists"""
        with self.assertRaises(IOError) as cm:
            self.layout.writeToFile(self.layoutPath, self.layoutFile)

    def test_writeToFile_withReplacement(self):
        """Optional parameter to silence the IOError and go ahead and write the file."""
        f = open(self.testJoinPath, 'w')
        f.close()

        self.layout.writeToFile(self.testPath, self.testFileExt, replace_existing=True)
        self.assertGreater(os.path.getsize(self.testJoinPath), 0)

    def test_writeToFile_usingNameProperty(self):
        """Leaving off the name parameter should use the "name" property"""
        self.layout.name = self.testFile 
        self.layout.writeToFile(self.testPath)

        self.assertTrue(os.path.exists(self.testJoinPath), "Didn't create file")

    def test_writeToFile_noNameProperty(self):
        """Leaving off the name parameter should use the "name" property 
        If name isn't set, it should raise a ValueError"""
        self.layout.name = None
        with self.assertRaises(ValueError) as cm:
            self.layout.writeToFile(self.layoutPath)
        self.assertEqual(cm.exception.message, "Layout has no property: name, and filename parameter was not set")


def suite():
    load = unittest.TestLoader()
    suite = load.loadTestsFromTestCase(LayoutTest)
    suite.addTests(load.loadTestsFromTestCase(LayoutTest_CreateFromExistingZip))
    suite.addTests(load.loadTestsFromTestCase(LayoutTest_CreateFromExistingFile))
    suite.addTests(load.loadTestsFromTestCase(LayoutWriteTest))
    return suite

def rostest():
    suite = []
    suite.append(['LayoutTest', LayoutTest])
    suite.append(['CreateFromExistingFile', LayoutTest_CreateFromExistingFile])
    suite.append(['CreateFromExistingZip', LayoutTest_CreateFromExistingZip])
    suite.append(['WriteLayout', LayoutWriteTest])
    return suite

if __name__ == "__main__":
    unittest.main()