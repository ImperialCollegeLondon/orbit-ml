from orbit_ml import *

prj = Project("tinycore.cpp")

def convert_params(params):
    mlo_params = { }
    for p in params:
        _type = p[1]
        if p[1] == "int":
            if len(p) != 4:
                raise RuntimeError(f"[x] expecting orbit param type with bound limits: {p}!")
            mlo_type = "integer"
            mlo_min = int(p[2])
            mlo_max = int(p[3])
        elif p[1] == "bool":
            mlo_type = "integer"
            mlo_min = 0
            mlo_max = 1
        else:
            raise RuntimeError(f"[x] parameter type not supported: '{p}'!")

        mlo_params[p[0]] = {'type': mlo_type, 'bounds': (mlo_min, mlo_max)}
    return mlo_params
    
mlo_params = convert_params(prj.core.params)

cmlo = ceshmlo.CeshMLO(mlo_params, 'hebo', 4)

for i in range(3):
    print('Iteration', i)
    print('Generating probes...')
    probes = cmlo.get_probes()
    print('Probes (list of dictionarys):')
    print(probes)

    estimates = []
    for probe in probes:
        design = prj.build(target="sw", build_args=probe, outdir="test", force=True)
        ppa = design.run(args=["walk.asm"])
        estimates.append(ppa['num_cycles'])

    print('Performance estimates (list of numbers):')
    print(estimates)
    print('Updating ML model with the estimates...')
    cmlo.update(estimates)    
    print()
    
print('Best solution:', cmlo.get_best())


# # Tuneable parameters
# # Three cache parameters:
# #      setid_width: 1--4
# #      line_width: 1--4
# #      n_ways: 1--16

# BPJ_LIMIT=1 # 0--1 (MAX)
# CR_LIMIT=1 # 0--1  (MAX)
# SW_LIMIT=1 # 1--4  (MAX)
# LW_LIMIT=1 # 1--4  (MAX)
# NW_LIMIT=1 # 1--16 (MAX)

# db_ppa=[]
# for branch_predict_jump in range(0, BPJ_LIMIT+1):
#     for cache_read_scheme in range(0, CR_LIMIT+1):
#         for setid_width in range(1,SW_LIMIT+1):
#             for line_width in range(1,LW_LIMIT+1):
#                 for n_ways in range(1,NW_LIMIT+1):
#                     build_args = {'branch_predict_jump': branch_predict_jump, 'cache_read_scheme': cache_read_scheme, 'setid_width': setid_width, 'line_width': line_width, 'n_ways': n_ways }
#                     design = prj.build(target="sw", build_args=build_args, outdir="test", force=True)
#                     ppa = design.run(args=["walk.asm"])

#                     stored_ppa = build_args.copy()
#                     stored_ppa.update(ppa)

#                     db_ppa.append(stored_ppa)

# print("DB-PPA:")    
# print(db_ppa)    