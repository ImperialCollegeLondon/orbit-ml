from .workflow_sw import Workflow
from ..design import Design
import os.path as osp
import shutil
import subprocess
from types import SimpleNamespace
from bs4 import BeautifulSoup

class WorkflowHW(Workflow):
    def __init__(self, *, project, build_args, outdir=None, force=True, **kwargs):
        super().__init__(project=project, build_args=build_args) 
        self.outdir = outdir
        self.force = force        
        
    # we use vivado HLS
    def _engine_hw(args:list, data, workdir):
        ppa = {}

        print("[i] collecting information from Vivado HLS report... ")   
        xmlfile = data.report_file
        with open(xmlfile, 'r') as f:
            xml_data = f.read()    

        bs_data = BeautifulSoup(xml_data, 'xml') 

        modules = bs_data('ModuleInformation')[0].find_all('Module')        
        fn_module = None
        for m in modules:
            if m.Name.string == data.fn_name:
                fn_module = m
                break

        if fn_module is None:
            raise RuntimeError(f"cannot find report for module: '{data.fn_name}'!")
        
        ppa['hw-avg-latency'] = int(fn_module.PerformanceEstimates.SummaryOfOverallLatency.find('Average-caseLatency').string)
        ppa['hw-ii'] = int(fn_module.PerformanceEstimates.SummaryOfOverallLatency.PipelineInitiationInterval.string)
        ppa['hw-dsp'] = int(fn_module.AreaEstimates.Resources.DSP.string)
        ppa['hw-ff'] = int(fn_module.AreaEstimates.Resources.FF.string)
        ppa['hw-lut'] = int(fn_module.AreaEstimates.Resources.LUT.string)
        ppa['hw-bram'] = int(fn_module.AreaEstimates.Resources.BRAM_18K.string)

        return ppa        
    
    def build(self):        

        if self.outdir is None:
            raise RuntimeError("[x] Workflow 'hw' requires 'outdir' parameter!")

        if self.force and osp.exists(self.outdir):  
            shutil.rmtree(self.outdir)

        # we need core to be specified
        if self.project.core.name is None:
            raise RuntimeError("[x] core function has not been specified!")
       

        if self.force or not osp.exists(osp.join(self.outdir, 'script.tcl')):
            extra_hw_defs = ['-D', '__HLS__']
            defs = self.ast_defs + extra_hw_defs
            new_ast = self.project.ast.clone(name=self.outdir, preprocessor=2, new_defs=defs)    
            new_ast.sync()        

            WorkflowHW._render_template_file(template='hls_make', 
                                            data={'fn_name': self.project.core.name,
                                                'srcs': " ".join(self.project.cmd.sources)},
                                            file=osp.join(self.outdir, 'hls.make'))   

            WorkflowHW._render_template_file(template='script_tcl', 
                                            data={'fn_name': self.project.core.name,
                                                'srcs': " ".join(self.project.cmd.sources),
                                                'defs': (" ".join(defs)).replace('"', ''),
                                                'args': (" ".join(self.project.cmd.args)).replace('"','')},
                                            file=osp.join(self.outdir, 'script.tcl'))     

        report_file = osp.join(self.outdir, 'doCore', 'solution', 'syn', 'report', 'csynth.xml')
        if self.force or not osp.exists(report_file):
            print("[i] running HLS ... ")
            # run makefile       
            try:
                p = subprocess.run(['make', '-f', 'hls.make'], cwd=self.outdir, check=True)        
            except subprocess.CalledProcessError:
                print("[x] error running HLS!")   
                exit(-1)
            print("[i] ... done!")     

        data = SimpleNamespace()
        data.report_file = report_file
        data.fn_name = self.project.core.name

        design = Design(fn=WorkflowHW._engine_hw, data=data,  workdir=osp.abspath(self.outdir))                              

        return design            




    


        



    

