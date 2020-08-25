from django.db import models
from django.db.models import F, Value, IntegerField, TextField
from django.db.models.functions import Concat

from django_cte import CTEManager, With


class TreeModel(models.Model):
    tree = CTEManager()

    class Meta:
        abstract = True

    def _get_descendants(self, cte):
        model = self.__class__
        return model.tree.filter(
            # start with current nodes
            parent=self.pk
        ).values(
            "pk",
            depth=Value(0, output_field=IntegerField()),
        ).union(
            # recursive union: get descendants
            cte.join(model, parent=cte.col.pk).values(
                "pk",
                depth=cte.col.depth + Value(1, output_field=IntegerField()),
            ),
            all=True,
        )

    def _get_ancestors(self, cte):
        model = self.__class__
        return model.tree.filter(
            # start with current node
            pk=self.pk
        ).values(
            "parent_id",
            depth=Value(0, output_field=IntegerField()),
        ).union(
            # recursive union: get ancestors
            cte.join(model, pk=cte.col.parent_id).values(
                "parent_id",
                depth=cte.col.depth - Value(1, output_field=IntegerField()),
            ),
            all=True,
        )

    def descendants(self):
        cte = With.recursive(self._get_descendants)
        model = self.__class__
        return cte.join(model.tree.all(), pk=cte.col.pk).with_cte(cte).annotate(
            depth=cte.col.depth
        ).order_by('depth')

    def ancestors(self):
        cte = With.recursive(self._get_ancestors)
        model = self.__class__
        return cte.join(model.tree.all(), pk=cte.col.parent_id).with_cte(cte).annotate(
            depth=cte.col.depth
        ).order_by('depth')


