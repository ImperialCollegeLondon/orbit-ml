
from itertools import chain
from meta_cl import *
from meta_cl.utils import get_cpp_attribute
import os.path as osp
import os
from jinja2 import Environment, BaseLoader, FileSystemLoader
import itertools
import inspect


class Workflow:
    def __init__(self, *, project, build_args):
        self.project = project
        self.build_args = build_args.copy()

        self.ast_defs = self.project.ast.source_manager.defs.copy()
        
        params = list(chain.from_iterable([['-D', f'ORBIT_PARAM_{k}="{v}"'] for k,v in build_args.items()]))
        self.ast_defs.extend(params)
        self.directives = {}     


    def _render_template(*, template, data):

        # get location of caller module to find 'templates' directory
        module = inspect.getmodule(inspect.stack()[1][0])     
        template_dir = osp.join(osp.abspath(osp.dirname(module.__file__)), 'templates') 
        if not osp.exists(template_dir):
            raise RuntimeError(f"cannot find template path: {template_dir}")  

        jenv = Environment(loader=FileSystemLoader(template_dir))        

        template_obj = jenv.get_template(template + '.template')
        content = template_obj.render(**data)

        return content



    def _render_template_file(*, template, data, file=None, overwrite=True):

        content = Workflow._render_template(template=template, data=data)

        if file is None:
            return content
        else:
            if osp.exists(file):
                if overwrite:
                    os.remove(file)
                else:
                    raise RuntimeError(f"cannot render file '{file}' since it already exists!")    

            with open(file, 'w+') as f:
                f.write(content)    

    def _render_directive_arg(*, arg, workflow, cnode):
        # check if it is a string literal or a file
        if arg[0] == '"' and arg[-1] == '"':
            template = arg[1:-1]
        else:
            template_file = osp.join(workflow.project.template_dir, arg)
            if not osp.exists(template_file):
                raise RuntimeError(f"[x] cannot find template '{template_file}'!")
            with open(template_file,"r") as f:
                template = f.read()

        rtemplate = Environment(loader=BaseLoader).from_string(template)
        params = workflow.build_args
        params['this'] = cnode

        code_instance = rtemplate.render(**params)

        return code_instance

    def directive_permute(*, workflow, cnode, directives):
        if len(directives) != 1: 
            raise RuntimeError(f"[x] invalid number of 'orbit::permute' directives associated to a single construct ({cnode.location})'!")

        # arguments associated to directive
        args = directives[0] 

        if len(args) != 1:
            raise RuntimeError(f"[x] invalid number of arguments: 'orbit::permute({', '.join(args)})'!")

        n = int(Workflow._render_directive_arg(arg=args[0], workflow=workflow, cnode=cnode))

        if not cnode.isentity('CompoundStmt'):
            raise RuntimeError("[x] 'orbit::permute' directive only supports code block!")

        num_stmts = cnode.num_children
        order_list = list(itertools.permutations(range(0, num_stmts)))

        if n >= len(order_list):
            raise RuntimeError(f"[x] 'orbit::permute' error: block has {num_stmts} statements(s): expecting order number to be less than {len(order_list)}!")
        
        order = order_list[n]

        stmts = [cnode.child(i).unparse()  for i in order]

        code = "{"
        for stmt in stmts:
            if stmt[-1] != "}":
                code += stmt + ";"
            else:
                code += stmt
        code += "}"


        cnode.instrument(action=Action.replace, code=code)  
     
    def directive_replace_if(*, workflow, cnode, directives):
        if len(directives) != 1: 
            raise RuntimeError(f"[x] invalid number of 'orbit::replace_if' directives ({cnode.location})',!")

        args = directives[0]

        if len(args) != 2:
            raise RuntimeError(f"[x] invalid number of arguments: 'orbit::replace_if({', '.join(args)})'!")

        condition = args[0]
        if condition[0] == '"' and condition[-1] == '"':
            template = condition[1:-1]  
            rtemplate = Environment(loader=BaseLoader).from_string(template)
            params = workflow.build_args.copy()
            params['this'] = cnode
            val = int(rtemplate.render(**params))
            if val == 0:
                return        
        else:
            raise RuntimeError(f"[x] first argument of 'orbit::replace_if({', '.join(args)})' must be a string!")

        _directives = directives.copy()
        _directives[0] = _directives[0][1:]
        Workflow.directive_replace(workflow=workflow, cnode=cnode, directives=_directives)
        


        
    def directive_replace(*, workflow, cnode, directives):
        if len(directives) != 1: 
            raise RuntimeError(f"[x] invalid number of 'orbit::replace' directives ({cnode.location})'!")

        args = directives[0]

        if len(args) != 1:
            raise RuntimeError(f"[x] invalid number of arguments: 'orbit::replace({', '.join(args)})'!")

        # check if it is a string literal or a file
        val = args[0]
        if val[0] == '"' and val[-1] == '"':
            template = val[1:-1]
        else:
            template_file = osp.join(workflow.project.template_dir, val)
            if not osp.exists(template_file):
                raise RuntimeError(f"[x] cannot find template '{template_file}'!")
            with open(template_file,"r") as f:
                template = f.read()

        rtemplate = Environment(loader=BaseLoader).from_string(template)
        params = workflow.build_args.copy()
        params['this'] = cnode

        code_instance = rtemplate.render(**params)
        cnode.instrument(action=Action.replace, code=code_instance)            


    def directive_ppa(*, workflow, cnode, directives):
        # check if directive is used inside a function definition
        fn = None
        block = None
        for n in cnode.ancestors:
            if n.isentity("CompoundStmt"):
                block = n # ensure we are inside a function definition block
            if n.isentity("FunctionDecl"):
                fn = n
                break
        
        if (fn is None) or (block is None):
            raise RuntimeError("[x] directive 'orbit::ppa' can only be used inside a function definition!")

        fn_code = fn.unparse(changes=True)
        if '#include <fstream>' not in fn_code:
            fn.instrument(action=Action.before, code="#include <fstream>\n")

        code = ""
        for args in directives:
            if len(args) != 2:
                raise RuntimeError(f"[x] invalid number of arguments: 'orbit::ppa({', '.join(args)})'!")   

            code += Workflow._render_template(template='ppa_orbit',
                                              data= {'key': args[0],
                                                     'value': args[1]}        
                                             )        
        cnode.instrument(action=Action.before, code=code)

    def add_directive(self, name, handler):
        self.directives[name] = handler

    def build(self):
        raise RuntimeError("[x] workflow not implemented!")

    def remove_all_attributes(self, ast):
        def orbit_attr_removal(attr):
            for e in attr:
                if e.startswith("orbit::"):
                    return False
            return True     

        nodes_with_attributes = ast.query("n", where=lambda n:n.attributes is not None)

        for node in nodes_with_attributes:        
           node.n.instrument(action=Action.attributes, fn=orbit_attr_removal) 

    def process_directives(self, ast):
        for directive in self.directives:
            fn = self.directives[directive]
            attrs = self.__collect_attributes(ast, directive)
            for attr in attrs:
                fn(workflow=self, cnode=attr[0], directives=attr[1])

    def __collect_attributes(self, ast, attribute_name:str):
        # return a list of names
        nodes_with_attributes = ast.query("n", where=lambda n:n.attributes is not None)

        attrs = []
        for node in nodes_with_attributes:
            cnode = node.n
            attr_val = get_cpp_attribute(cnode, attribute_name)
            if attr_val is not None:
                attrs.append((cnode, attr_val))

        return attrs








    
    
