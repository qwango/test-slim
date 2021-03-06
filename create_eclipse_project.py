

'''
@author: Pierre Thibault (pierre.thibault1 -at- gmail.com)
@license: GPL 3
@since: 2010-06-24

Usage: create_eclipse_project [OPTION]... [SOURCE DIRECTORY]         
Create a Web2py application Eclipse Pydev project.

  -h,  --help          Display this help message.
  
Create a Web2py application Eclipse Pydev project with Maven. The Eclipse
project is created in SOURCE DIRECTORY or in the current directory if
SOURCE DIRECTORY is not specified. SOURCE DIRECTORY must be a Web2py
application directory inside the "applications" directory of a Web2py
installation. 

The result project can be imported in Eclipse using the following command:
(File > Import... > General > Existing Projects into Workspace).

The name of the Eclipse project has the same name as the directory containing
the Web2py application.

When run, the script asks the user the name of Pydev Python interpreter to
use for the project created. The Python grammar version used for the new
project is 2.5.

The script also creates a link to the 'web2py.py' file so a run configuration
can easily be created to start the new application.

If an Eclipse project already exists in the application directory, the script
abort all operations.

If the project uses Mercurial, ".classpath", ".project", ".pydevproject", 
"pom_generated.xml", ".DS_Store", ".deployment" and ".settings" are added to
the files to ignore.

This script needs Apache Maven. Maven must be accessible from PATH.

An internet connection may be needed to allow Maven to load the necessary
dependencies (this especially true the first time the script is run).

The script creates an artefact called "pom_generated.xml" that can be
discarded after the script has run.
'''

from __future__ import with_statement
import cStringIO
import getopt
import os
import re
import subprocess
import sys

# The pom source needed for Maven as a String:
POM_SOURCE = """<project xmlns="http://maven.apache.org/POM/4.0.0" 
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 h
ttp://maven.apache.org/maven-v4_0_0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <properties>
        <project.name>will_be_replaced</project.name>
        <web2py.folder.path>will_be_replaced</web2py.folder.path>
        <PYTHON_PROJECT_INTERPRETER>will_be_replaced</PYTHON_PROJECT_INTERPRETER>
        <PYTHON_PROJECT_VERSION>python 2.5</PYTHON_PROJECT_VERSION>
    </properties>
    <groupId>org.voiceofaccess</groupId>
    <artifactId>${project.name}</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <name>${project.name}</name>
    <description>An archetype to start a UniversalCake project with Eclipse and PyDev.</description>
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-eclipse-plugin</artifactId>
                <version>2.8</version>
                <configuration>
                    <buildcommands>
                        <buildcommand> org.python.pydev.PyDevBuilder</buildcommand>
                    </buildcommands>
                    
                    <projectnatures>
                        <projectnature>org.python.pydev.pythonNature</projectnature>
                    </projectnatures>
                    
                    <linkedResources> 
                       <linkedResource> 
                           <name>web2py.py</name>
                           <type>1</type> 
                           <location>${web2py.folder.path}/web2py.py</location>
                       </linkedResource>
                    </linkedResources>
                    
                    <additionalConfig>
                        <file>
                            <name>.pydevproject</name>
                            <content>
                                <![CDATA[<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<?eclipse-pydev version="1.0"?>

<pydev_project>
<pydev_property name="org.python.pydev.PYTHON_PROJECT_INTERPRETER">${PYTHON_PROJECT_INTERPRETER}</pydev_property>
<pydev_property name="org.python.pydev.PYTHON_PROJECT_VERSION">${PYTHON_PROJECT_VERSION}</pydev_property>
<pydev_pathproperty name="org.python.pydev.PROJECT_SOURCE_PATH">

<!-- These paths were removed in a previous version because there are not in 
the web2py path. But without them, Pydev won't do the static code analysis.
If you find a better solution, email me. --> 
<path>/${project.name}/controllers</path>
<path>/${project.name}/models</path>
<path>/${project.name}/modules</path>
<path>/${project.name}/languages</path>
<!-- <path>/${project.name}</path>  Should I add this one? --> 

</pydev_pathproperty>
<pydev_pathproperty name="org.python.pydev.PROJECT_EXTERNAL_SOURCE_PATH">
<path>${web2py.folder.path}</path>
<path>${web2py.folder.path}/site-packages</path>
</pydev_pathproperty>
</pydev_project>
]]>
                            </content>
                        </file>
                    </additionalConfig>
                    
                </configuration>
            </plugin>
        </plugins>
        
    </build>
</project>
"""

def main(argv):                         
    """Parse the arguments and start the main process."""
    try:                                
        opts, args = getopt.getopt(argv, "h", ["help"])
    except getopt.GetoptError:
        exit_with_parsing_error()
    for opt, arg in opts:
        arg = arg  # To avoid a warning from Pydev
        if opt in ("-h", "--help"):
            usage()                     
            sys.exit()
    if len(args) == 0:
        create_eclipse_project(os.curdir)
    elif len(args) == 1:
        create_eclipse_project(*args)
    else:
        exit_with_parsing_error()       
    
def exit_with_parsing_error():              
    """Report invalid arguments and usage."""
    print("Invalid argument(s).")
    usage()
    sys.exit(2)

def usage():
    """Display the documentation"""
    print(__doc__)

def create_eclipse_project(project_path):
    """
    Create the Eclipse Pydev project for the application located at
    project_path.
    @param project_path: The absolute or relative path of the Web2py
    application directory.
    """

    # Find the needed directory paths:
    project_path = os.path.realpath(project_path)
    if not os.path.isdir(project_path):
        print('The project path "%s" is not directory.' % project_path)
        sys.exit(1)
    pom_dest = 'pom_generated.xml'
    web2py_dir_path = os.path.realpath( \
            os.sep.join([project_path, os.pardir, os.pardir]))
    
    # Abort if project file already exist:
    if os.path.exists(''.join([project_path, os.sep, '.project'])):
        print('Eclipse .project file exists. Abort.')
        sys.exit(1)
    
    # Ask the Pydev interpreter name:
    pydev_interpreter = raw_input('Name of Pydev Python interpreter to use ' +
      '(empty string to cancel)? ')
    if not pydev_interpreter:
        sys.exit(0)
    
    # Associate property names with their values for the pom:
    properties_to_values = { 
                    r'project.name': os.path.basename(project_path), 
                    r'web2py.folder.path': web2py_dir_path,
                    r'PYTHON_PROJECT_INTERPRETER': pydev_interpreter,
                     }

    # Process all the lines of source pom and write them in the destination:
    with open(os.sep.join((project_path, pom_dest)), 'w') as dest_file:
        for line in cStringIO.StringIO(POM_SOURCE):
            line = set_values_for_properties(line, properties_to_values)
            dest_file.write(line)
                
    # Call Maven with the generated pom to create the Eclipse project:
    old_current_dir = os.getcwdu()
    try:
        os.chdir(project_path)
	print pom_dest
        subprocess.call(['mvn', '--file', pom_dest, 'eclipse:eclipse'])
        # If the project is under Mercurial control add the Eclipse dot files:
        if os.path.isdir(os.sep.join((project_path, ".hg"))):
            files_to_ignore = [
                               ".classpath", 
                               ".project", 
                               ".pydevproject", 
                               pom_dest, 
                               ".DS_Store", 
                               ".deployment",
                                ".settings", 
                                "~", 
                                ".bak",
                                "cache",
                                "databases",
                                "errors",
                                "private",
                                "sessions",
                                "uploads",
                                ]
            hgignore_path = os.sep.join((project_path, ".hgignore"))
            hgignore_path_temp = hgignore_path + "~"
            # Create the file if it does not exist:
            if not os.path.isfile(hgignore_path):
                open(hgignore_path, "w").close()
            with open(hgignore_path, 'r') as hgignore_file:
                with open(hgignore_path_temp, 'w') as hgignore_tempfile:
                    line = ""
                    # Copy the lines in the temporary file:
                    for line in hgignore_file:
                        hgignore_tempfile.write(line)
                        # Remove line to add that are already there:
                        line_stripped = line.rstrip()
                        if line_stripped in files_to_ignore:
                            files_to_ignore.remove(line_stripped)
                    # Remove line ending of last line if needed:
                    if line in ("\c", "\f", "\n"):
                        hgignore_tempfile.seek(-len(line), os.SEEK_END)
                    # Add the file names:
                    for file_name in files_to_ignore:
                        hgignore_tempfile.write(file_name + "\n")
                    # Swap the files:
                    os.rename(hgignore_path, hgignore_path + "~~")
                    os.rename(hgignore_path_temp, hgignore_path)
                    os.rename(hgignore_path + "~~", hgignore_path_temp)
    finally:
        os.chdir(old_current_dir)
        
def set_values_for_properties(line, properties_to_values):
    """
    Replace property names by their associated values.
    @param line: line of text to process.
    @param properties_to_values: Dictionary associating property names with
    @return: The new line of text with new values for the properties.
    their corresponding values.
    """
    
    for property_name, value in properties_to_values.items():
        property_name = re.escape(property_name)
        line = re.sub(
            r'(<%s>)(.*)(</%s>)' % (property_name, property_name),
            ''.join([r'\1', value, r'\3']), line)
    return line 

if __name__ == "__main__":
    main(sys.argv[1:])  # Start the process (without the application name)
