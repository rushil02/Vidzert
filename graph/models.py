from django.db import models
from django.contrib.postgres.fields import HStoreField


class Graph(models.Model):
    graph_model = HStoreField()
    graph_file = models.FileField()
    graph_user = HStoreField()
    user_pos = HStoreField()
    stats = HStoreField()
    create_time = models.DateTimeField(auto_now_add=True)

    def get_pos(self, pos):
        coins_won = self.graph_model[str(pos)]
        user_graph_position = self.user_pos[str(pos)]
        user_graph_dict = self.graph_user
        x_data = []
        y_data = []
        ch = 1
        while ch <= int(user_graph_position):
            x_data.append(ch)
            y_data.append(int(user_graph_dict[str(ch)]))
            ch += 1
        return x_data, y_data, int(coins_won)

    def __unicode__(self):
        return str(self.id)


class GraphCreationMetaManager(models.Manager):
    def get_queryset(self):
        return super(GraphCreationMetaManager, self).get_queryset()

    def get_graph_meta(self, graph_type):
        try:
            graph_creation_meta = self.get_queryset().filter(graph_type=graph_type, active=True).latest('create_time')
        except:
            return None, None
        else:
            meta = graph_creation_meta.graph_meta
            win_model = graph_creation_meta.graph_win_model
            meta_values = {}
            win_model_values = {}

            for key in meta:
                meta_values.update({key: float(meta[key])})

            for key in win_model:
                win_model_values.update({float(key): float(win_model[key])})

            return win_model_values, meta_values

    # TODO: validate both models
    @staticmethod
    def validate_graph_meta(graph_type, graph_meta, graph_win_model):
        error_meta = {}
        flag = True

        try:
            if not (0 < float(graph_meta["expense_percentage"]) < 100):
                raise AssertionError
        except:
            flag = False
            error_meta.update({"ER112": "expense_percentage not defined properly"})

        try:
            if not (0 < float(graph_meta["per_person_cost"])):
                raise AssertionError
        except:
            flag = False
            error_meta.update({"ER325": "per_person_cost not defined properly"})

        try:
            if not (0 < float(graph_meta["featured_cost_percentage"]) < 100):
                raise AssertionError
        except:
            flag = False
            error_meta.update({"ER456": "featured_cost_percentage not defined properly"})

        try:
            init_peak = float(graph_meta['init_peak'])
            load_balancer_value = float(graph_meta['load_balancer_value'])
            base_limit = float(graph_meta['base_limit'])
        except:
            flag = False
            error_meta.update({"ER3": "Meta values not defined properly"})
        else:
            total = 0
            graph_win_model_float = {}
            try:
                for ch in graph_win_model:
                    graph_win_model_float.update({
                        float(ch): float(graph_win_model[ch])
                    })
                    total += float(graph_win_model[ch])
            except:
                flag = False
                error_meta.update({"ER4": "Win model is empty"})
            else:
                if not (total == 1.0):
                    error_meta.update({"ER1": "Total win model probability should be '1.0'"})
                    flag = False
                if init_peak < max(graph_win_model_float.keys()):
                    error_meta.update({"ER2": "Initial peak model percentage is lower than win_model peaks"})
                    flag = False
        return flag, error_meta

    def create_graph_meta(self, graph_type, graph_meta, graph_win_model):
        flag, error_meta = self.validate_graph_meta(graph_type, graph_meta, graph_win_model)

        if flag:
            try:
                self.get_queryset().get(graph_type=graph_type, graph_meta=graph_meta, graph_win_model=graph_win_model)
            except GraphCreationMeta.DoesNotExist:
                self.create(graph_type=graph_type, graph_meta=graph_meta, graph_win_model=graph_win_model)
            return True, error_meta
        else:
            return False, error_meta


class GraphCreationMeta(models.Model):
    GRAPH_TYPE = (('V', 'Video Graph'),
                  ('S', 'Survey graph'),
                  )
    graph_type = models.CharField(max_length=1, choices=GRAPH_TYPE)
    graph_meta = HStoreField()
    graph_win_model = HStoreField()
    active = models.BooleanField(default=True)
    create_time = models.DateTimeField(auto_now_add=True)

    objects = GraphCreationMetaManager()

    def __unicode__(self):
        return "%s" % self.graph_type
