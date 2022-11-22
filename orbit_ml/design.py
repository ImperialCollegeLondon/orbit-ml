class Design:
    def __init__(self, *, fn, data, workdir):
        self.fn = fn
        self.data = data
        self.workdir = workdir

    def run(self, *, args:list=None):
        if args is None:
            args = []
        ppa = self.fn(args=args, data=self.data, workdir=self.workdir)
        return ppa



    


