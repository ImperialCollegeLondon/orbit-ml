import re
import clang.cindex as ci
from meta_cl.utils import get_basetype_from_typedef, shape_type
from types import SimpleNamespace


class FnSignature:       
    SCALAR=0
    POINTER=1
    ARRAY=2         
    def __init__(self, fn):
        self.fn = fn
        self.data = []           
        self.index = { } # name => info

        sig = fn.signature        

        if sig.rettype.kind != ci.TypeKind.VOID:
            raise RuntimeError(f"[x] error processing function '{fn.name}': return type must be 'void'!")

        for p in sig.params:
            info = FnSignature.__compute_type_info(p[0], p[1])
            

            if len(self.fn.query("var{DeclRefExpr}", where=lambda var: var.name == p[1])) == 0:
                #print(f"[!] variable '{p[1]}' not referenced!")
                info.referenced = False
            else:
                info.referenced = True

            self.data.append(info)
            self.index[info.name] = info

    def get(self, name):
        return self.index.get(name, None)

    def expect(self, name):
        info = self.get(name)
        if info is None:
            raise RuntimeError(f"[x] cannot find parameter '{name}'!")
        return info

    @property
    def params(self):
        return self.data

    @staticmethod
    def __convert_type(type_str):
        # returns (name, arg1, arg2, arg3)
        type_str = type_str.strip()
        type_str = type_str.split("::")
        if (len(type_str) == 1):
            namespace=""
            type_str = type_str[0]
        else:
            namespace = type_str[0]
            type_str = type_str[1]

        pattern = r"^([\w ]+)[ ]*(<[ ]*(.+)[ ]*>)?$"
        m = re.match(pattern, type_str)
        if m:
            if m.group(3) is None:
                return m.group(1)
            else:
                e = [m.group(1)]
                e.extend(m.group(3).split(','))
                return tuple(e)
        else:
            return None        

    # Each element is a tuple: (name, type, base_type_info, kind:scalar=0, pointer=1, array=2, num_elements)
    @staticmethod
    def __compute_type_info(t, name):
        if t.kind == ci.TypeKind.TYPEDEF:
            base_type = get_basetype_from_typedef(t)
            return FnSignature.__compute_type_info(base_type, name)

        kind = FnSignature.SCALAR 
        num_elems = 1  # we change this variable for constant arrays
        shape = None # only arrays have shape

        if t.kind == ci.TypeKind.POINTER:
            base_type = t.get_pointee()
            kind = FnSignature.POINTER
        elif t.kind == ci.TypeKind.CONSTANTARRAY:
            _shape = shape_type(t)
            ne = 1
            for d in _shape.dim:
                if not isinstance(d, int):
                    raise RuntimeError(f"[x] error processing function parameter: type '{t.spelling}' not supported: array indices must be constant!")
                ne *= d
            shape = _shape.dim
            base_type = _shape.base_type
            num_elems = ne
            kind = FnSignature.ARRAY
        else:
            base_type = t

        if base_type.kind == ci.TypeKind.TYPEDEF:
            base_type = get_basetype_from_typedef(base_type)

        base_type_info = FnSignature.__convert_type(base_type.spelling)
        if base_type_info is None:
           raise RuntimeError(f"[x] error processing function parameter: type '{t.spelling}' not supported!")

        # for now, we do not accept multi-dim arrays
        if shape and len(shape) > 1:
           raise RuntimeError(f"[x] error processing function parameter '{name}': multi-dim arrays not supported!")       


        signature = SimpleNamespace()

        signature.name = name
        signature.type = t
        signature.base_type_info = base_type_info
        signature.base_type_name = base_type_info if type(base_type_info) == str else f"{base_type_info[0]}<{', '.join(base_type_info[1:])}>"
        signature.kind = kind
        signature.shape = shape
        signature.num_elems = num_elems  
        signature.referenced = None
    
        return signature
