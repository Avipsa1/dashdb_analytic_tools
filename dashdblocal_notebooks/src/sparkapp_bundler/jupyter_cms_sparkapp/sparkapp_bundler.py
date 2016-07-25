# (c) Copyright IBM Corporation 2016   
# LICENSE: Apache V2, https://opensource.org/licenses/Apache-2.0

import os, io, glob, json, subprocess
from nbconvert import TemplateExporter
from jinja2 import FileSystemLoader
from nbconvert.preprocessors import Preprocessor
from nbconvert import preprocessors

INSTALLDIR = os.path.dirname(os.path.realpath(__file__))

# marker indicating code cells that should not be added to the Spark application
FILTER_CELL_MARKER = "//NOT-FOR-APP"


def export_to_scala(absolute_notebook_path):
    '''convert the notebook source to scala'''
    
    exporter = TemplateExporter(extra_loaders=[FileSystemLoader(INSTALLDIR)],
                                preprocessors=[ScalaAppPreprocessor])
    exporter.template_file = 'scala_sparkapp'
    (body, resources) = exporter.from_file(absolute_notebook_path)
    return body


def export_to_scalafile(absolute_notebook_path, scala_source):
    '''convert the notebook source to scala and save it into the given filename'''
    
    scalacode = export_to_scala(absolute_notebook_path)
    with open(scala_source, 'wt') as sourcefile:
        sourcefile.write(scalacode)

        
def build_scala_project(project_dir, appname):
    '''build the given scala project, replacing the <appname> tag in build.sbt.template
    with the given application name.
    Return the name of the generated JAR'''
            
    with open(project_dir+"/../build.sbt.template", "rt") as buildfile_in:
        with open(project_dir+"/build.sbt", "wt") as buildfile_out:
            for line in buildfile_in:
                buildfile_out.write(line.replace('<appname>', appname))
    subprocess.run(["./build.sh"], cwd=project_dir, check=True)
    
    jars = glob.glob(project_dir + "/target/**/*.jar")
    assert len(jars) == 1, "Expected exactly one output JAR bout found {0}".format(','.join(jars))
    return jars[0]


def add_launcher_scripts(project_dir, jarfile, appname):
    scriptfile = "{0}/upload_{1}.sh".format(project_dir, appname)
    with open(scriptfile, "wt") as script:
        script.write("#!/bin/sh\n")
        script.write("./upload-sparkapp.py {0}\n".format(jarfile))
    os.chmod(scriptfile, 0o755)

    resource = os.path.basename(jarfile)
    scriptfile = "{0}/run_{1}.sh".format(project_dir, appname)
    submit_spec = { "appResource" : resource, "mainClass" : "SampleApp" }
    with open(scriptfile, "wt") as script:
        script.write("#!/bin/sh\n")
        script.write("./run-sparkapp.py '{0}'\n".format(json.dumps(submit_spec)))
    os.chmod(scriptfile, 0o755)


class ScalaAppPreprocessor(Preprocessor):
    """A preprocessor to remove some of the cells of a notebook"""
    
    def keepCell(self, cell):
        return not cell.source.startswith(FILTER_CELL_MARKER)

    def preprocess(self, nb, resources):
        nb.cells = filter(self.keepCell, nb.cells)
        return nb, resources    
