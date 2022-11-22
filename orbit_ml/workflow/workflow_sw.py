import os.path as osp
import subprocess
import shutil
import ast
from .workflow import Workflow
from ..design import Design


class WorkflowSW(Workflow):
    def __init__(self, *, project, build_args, outdir=None, force=True, **kwargs):
        super().__init__(project=project, build_args=build_args) 
        self.outdir = outdir
        self.force = force

    def _engine_sw(args:list, data, workdir):
        print("[i] running sw app... ")        
        try:
           app = data
           cmd =  [app]
           cmd.extend(args)
           p = subprocess.run(cmd, cwd=workdir, check=False)      
           if p.returncode != 0:
              print(f"[!] execution returned: code '{p.returncode}'!") 
           else:   
              print("[i] ... done!")        
        except subprocess.CalledProcessError:
            print(f"[x] error running application!")   
            exit(-1)


        ppa = { }
        ppa_file = osp.join(workdir, 'ppa.orbit')
        if osp.exists(ppa_file):
            with open(ppa_file, 'r') as f:
                for line in f:
                    line = line.rstrip()
                    pos = line.find(':')
                    val = line[pos+1:]
                    try:
                        # attempts to convert C++ string to a python literal
                        val = ast.literal_eval(val)
                    except ValueError:
                        pass

                    ppa[line[0:pos]] = val            

        return ppa

    
    def build(self):        
        if self.outdir is None:
            raise RuntimeError("[x] Workflow 'sw' requires 'outdir' parameter!")


        if self.force and osp.exists(self.outdir):  
            shutil.rmtree(self.outdir)

        sw_make_file = osp.join(self.outdir, 'sw.make')

        if self.force or not osp.exists(sw_make_file):
        
            # push code and pre-process it
            new_ast = self.project.ast.clone(name=self.outdir, preprocessor=2, new_defs=self.ast_defs)
            new_ast.parse_attributes()

            self.add_directive('orbit::replace', Workflow.directive_replace)
            self.add_directive('orbit::replace_if', Workflow.directive_replace_if)
            self.add_directive('orbit::permute', Workflow.directive_permute)
            self.add_directive('orbit::ppa', Workflow.directive_ppa)

            self.process_directives(new_ast)
            self.remove_all_attributes(new_ast)

            new_ast.sync(commit=True)        

            # create makefile to build app
            WorkflowSW._render_template_file(template='sw_make', 
                                            data={'sources': " ".join(self.project.cmd.sources),
                                                'defs': " ".join(self.ast_defs),
                                                'args': " ".join(self.project.cmd.args)},

                                            file=sw_make_file) 

        if self.force or not osp.exists(osp.join(self.outdir, 'app')):
            print("[i] building app... ")
            # run makefile       
            try:
                p = subprocess.run(['make', '-f', 'sw.make'], cwd=self.outdir, check=True)        
            except subprocess.CalledProcessError:
                print("[x] error building application!")   
                exit(-1)
            print("[i] ... done!")

        design = Design(fn=WorkflowSW._engine_sw, data='./app', workdir=osp.abspath(self.outdir))                                       

        return design
