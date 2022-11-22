from orbit_ml import *

prj = Project("tinycore.cpp")

# Tuneable parameters
# Three cache parameters:
#      setid_width: 1--4
#      line_width: 1--4
#      n_ways: 1--16

BPJ_LIMIT=1 # 0--1 (MAX)
CR_LIMIT=1 # 0--1  (MAX)
SW_LIMIT=1 # 1--4  (MAX)
LW_LIMIT=1 # 1--4  (MAX)
NW_LIMIT=1 # 1--16 (MAX)

db_ppa=[]
for branch_predict_jump in range(0, BPJ_LIMIT+1):
    for cache_read_scheme in range(0, CR_LIMIT+1):
        for setid_width in range(1,SW_LIMIT+1):
            for line_width in range(1,LW_LIMIT+1):
                for n_ways in range(1,NW_LIMIT+1):
                    build_args = {'branch_predict_jump': branch_predict_jump, 'cache_read_scheme': cache_read_scheme, 'setid_width': setid_width, 'line_width': line_width, 'n_ways': n_ways }
                    design = prj.build(target="sw", build_args=build_args, outdir="test", force=True)
                    ppa = design.run(args=["walk.asm"])

                    stored_ppa = build_args.copy()
                    stored_ppa.update(ppa)

                    db_ppa.append(stored_ppa)

print("DB-PPA:")    
print(db_ppa)    