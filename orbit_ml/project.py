import os
from meta_cl import *
from meta_cl.utils import get_cpp_attribute
from types import SimpleNamespace

from .fn_signature import FnSignature
from .workflow import get_workflow


class Project:
    def __init__(self, cmd, workspace=None, template_dir=None):
        self.ast = Ast(cmd=cmd, workdir=workspace, preprocessor=False)       
        self.ast.parse_attributes()  # parse attributes

        self.workspace = self.ast.workdir
        self.cmd = Project._process_cmd(cmd, self.ast)
        self.core = Project._process_core(self.ast)
        self.tb = Project._process_testbench(self.ast)

        if self.core.name is not None and self.tb.name is not None:
            if self.core.name == self.tb.name:
                raise RuntimeError(f"[x] testbench and core functions cannot be the same: '{self.core.name}'!")

        if template_dir is None:
            self.template_dir = os.getcwd()
        else:
            self.template_dir = os.path.abspath(template_dir)

    def _process_cmd(cmd, ast):
        cmd_obj = SimpleNamespace()
        cmd_obj.str = cmd
        cmd_obj.sources = [ s.name for s in ast.sources ]
        cmd_obj.args = ast.source_manager.args
        cmd_obj.defs = ast.source_manager.defs

        return cmd_obj

    def _process_core(ast):
        cnode = None
        tbl = ast.query("fn{FunctionDecl}={1}>b{CompoundStmt}", where=lambda fn: fn.attributes is not None)

        for row in tbl:
            ret = get_cpp_attribute(row.fn, 'orbit::core')
            if ret is not None:
                if len(ret) == 1:
                    if cnode is None:
                        cnode = row.fn
                        core_params = ret[0]
                    else:
                        raise RuntimeError(f"multiple core functions defined ({cnode.name}/{row.fn.name}): only one allowed!")
                else:
                    raise RuntimeError(f"multiple core directives defined on the same function ({row.fn.name}): only one allowed!")                      

        core_obj = SimpleNamespace()

        if cnode is None:
           core_obj.name = None
           core_obj.params = None
           core_obj.sources = None
           core_obj.signature = None            
           return core_obj

        # name
        core_obj.name = cnode.name

        # core params
        core_obj.params = core_params
        
        # sources
        core_obj.sources = Project._collect_srcs(cnode)

        # signature
        core_obj.signature = FnSignature(cnode)

        return core_obj

    def _process_testbench(ast):
        cnode = None
        cmain = None
        tbl = ast.query("fn{FunctionDecl}={1}>b{CompoundStmt}") 
        for row in tbl:
            ret = get_cpp_attribute(row.fn, 'orbit::testbench')            
            if ret is not None:
                print("|||> ", ret)
                if len(ret) == 1:
                    if cnode is None:
                        cnode = row.fn
                    else:
                        raise RuntimeError(f"multiple testbench functions defined ({cnode.name}/{row.fn.name}): only one allowed!")
                else:
                    raise RuntimeError(f"multiple testbench directives defined on the same function ({row.fn.name}): only one allowed!") 
                      
            if row.fn.name == 'main':
                cmain = row.fn
            
        if cnode is None:
            cnode = cmain
        
        tb_obj = SimpleNamespace()
        if cnode is None:
            tb_obj.name = None
            tb_obj.sources = None
        else:
            tb_obj.name = cnode.name
            tb_obj.sources = Project._collect_srcs(cnode)
        
        return tb_obj


    def _collect_srcs(cnode):
        sources = [cnode.srcname]
        to_process = sources.copy()

        ast = cnode.ast

        fns = [ row.fn.name for row in ast.query("fn{FunctionDecl}={1}>b{CompoundStmt}") ]

        processed_calls = set()

        while len(to_process) > 0:
            src_to_process = to_process[0]

            tbl = ast.query("fn{FunctionDecl}=>call{CallExpr}", where=lambda fn, call: fn.srcname == src_to_process and call.name in fns)        

            for row in tbl:
                callfn = row.call.name

                if callfn in processed_calls:
                    continue

                processed_calls.add(callfn)

                tbl2 = ast.query("fn{FunctionDecl}={1}>b{CompoundStmt}", where=lambda fn: fn.name == callfn)

                if tbl2:
                    callfn_srcname = tbl2[0].fn.srcname
                    if callfn_srcname not in to_process:
                        to_process.append(callfn_srcname)
                        sources.append(callfn_srcname)
                
            to_process.pop(0)    

        return sources


    def build(self, *, target, build_args=None, **kwargs):
        if build_args is None:
            build_args = {}

        if self.core.params is not None:
            missing_params = set(self.core.params) - set(build_args.keys())
            if len(missing_params) != 0:
                raise RuntimeError(f"[x] the following parameters for core '{self.core.name}' are missing: {', '.join(missing_params)}")

        workflow = get_workflow(target=target, project=self, build_args=build_args, **kwargs)
        return workflow.build()



        









