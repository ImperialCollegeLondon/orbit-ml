hebo_string = 'hebo'
naive_string = 'naive'

# TODO: create a HEBO wrapper rather than using if-else
class CeshMLO:
    def __init__(self, parameter_set, engine_name = 'hebo', num_threads = 4):
        self.num_threads = num_threads
        self.parameter_set = parameter_set
        self.engine_name = engine_name
        self.last_probes = None
        self.last_probes_hebo = None
        
        if engine_name == hebo_string:
            import hebo.optimizers.hebo as hebo
            #from hebo.design_space.design_space import DesignSpace
            hebo_design_space_list = []
            for (para_name, para_value) in parameter_set.items():
                if para_value['type'] == 'integer':
                    hebo_design_space_list.append({'name': para_name,
                                                   'type': 'int',
                                                   'lb': para_value['bounds'][0],
                                                   'ub': para_value['bounds'][1]})
                elif para_value['type'] == 'discrete':
                    hebo_design_space_list.append({'name': para_name,
                                                   'type': 'cat',
                                                   'categories': para_value['options']})
                else:
                    pass
            # print(hebo_design_space_list)
            hebo_design_space = hebo.DesignSpace().parse(hebo_design_space_list)
            self.engine = hebo.HEBO(hebo_design_space)
        else:
            if engine_name == naive_string:
                import naiveengine
            else:
                pass
            self.engine = naiveengine.NaiveEngine(parameter_set)

    def hebo_translate_parameter_set(self, df):
        probes = []
        for index,row in df.iterrows():
            single_probe = {}
            for para_name in self.parameter_set.keys():
                # TODO: handle ordinal parameters here
                single_probe[para_name] = row[para_name]
            probes.append(single_probe)
        return probes
            
    def get_probes(self):
        probes = []
        if self.engine_name == hebo_string:
            suggestions_df = self.engine.suggest(self.num_threads)
            self.last_probes_hebo = suggestions_df
            probes = self.hebo_translate_parameter_set(suggestions_df)
        else:
            probes = self.engine.get_probes(self.num_threads)

        self.last_probes = probes
        return self.last_probes
    
    def update(self, estimates, probes = None):
        if self.engine_name == hebo_string:
            import numpy as np
            estimates_hebo = np.array(estimates).reshape(-1, 1)
            if probes == None:
                probes_hebo = self.last_probes_hebo
            self.engine.observe(probes_hebo, estimates_hebo)
        else:
            if probes == None:
                probes = self.last_probes
            self.engine.update(probes, estimates)

    def get_best(self):
        if self.engine_name == hebo_string:
            return self.hebo_translate_parameter_set(self.engine.best_x), self.engine.best_y
        else:
            return self.engine.best_x, self.engine.best_y
