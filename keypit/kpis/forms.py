from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django.template.defaultfilters import linebreaksbr
from django.urls import reverse_lazy

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout

from .models import KPI, KPIEntry, KPICategory, Unit


class BodyHelper(FormHelper):
    def __init__(self, form):
        super().__init__(form)
        self.form_tag = False
        self.use_custom_control = True
        self.form_show_errors = False


class FooterHelper(FormHelper):
    def __init__(self, form):
        super().__init__(form)
        self.form_tag = False
        self.disable_csrf = True
        self.form_show_errors = False


class UnitForm(forms.ModelForm):
    admin_roles = SimpleArrayField(forms.CharField())

    class Meta:
        model = Unit
        fields = ['name', 'acronym', 'parent', 'admin_roles', 'acronyms', 'kind']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)
        if self.instance.pk:
            self.body.title = u"{}".format(self.instance.name)
            self.body.form_action = reverse_lazy('unit-edit', kwargs={'pk': self.instance.pk})
        else:
            self.body.title = u"New Unit"
            self.body.form_action = reverse_lazy('new-unit')
        self.body.layout = Layout(
            Div(
                Div('name', css_class="col-12"),
                Div('acronym', css_class="col-6"),
                Div('kind', css_class="col-6"),
                Div('parent', css_class="col-12"),
                Div('admin_roles', css_class="col-12"),
                Div('acronyms', css_class="col-12"),
                css_class="row"
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
        )


class KPIForm(forms.ModelForm):

    class Meta:
        model = KPI
        fields = ['name', 'description', 'category', 'kind', 'priority', 'units']
        widgets = {
            'description': forms.Textarea(attrs={"cols": 54, "rows": 4, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)
        if self.instance.pk:
            self.body.title = u"Edit KPI"
            self.body.form_action = reverse_lazy('kpi-edit', kwargs={'pk': self.instance.pk})
        else:
            self.body.title = u"New KPI"
            self.body.form_action = reverse_lazy('new-kpi')
        self.body.layout = Layout(
            Div(
                Div('category', css_class="col-10"),
                Div('priority', css_class="col-2"),
                Div('name', css_class="col-12"),
                Div('description', css_class="col-12"),
                css_class="row"
            ),
            Div(
                Div('kind', css_class="col-12"),
                Div(Field('units', css_class="select"), css_class="col-12"),
                css_class="row"
            )
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
        )


class KPIEntryForm(forms.ModelForm):

    class Meta:
        model = KPIEntry
        fields = ['value', 'comments', 'unit', 'kpi', 'month']
        widgets = {
            'comments': forms.Textarea(attrs={"rows": 8, "class": "form-control"}),
            'unit': forms.HiddenInput(),
            'kpi': forms.HiddenInput(),
            'month': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)
        if self.instance.pk:
            self.body.form_action = reverse_lazy('kpientry-edit', kwargs={'pk': self.instance.pk})
            kpi = self.instance.kpi
        else:
            self.body.form_action = reverse_lazy('kpientry-new')
            kpi = self.initial['kpi']
        if kpi.kind == KPI.TYPE.TEXT:
            self.fields['value'].widget = forms.HiddenInput()
        self.body.title = u"{}".format(kpi.name)
        self.body.layout = Layout(
            Div(
                'unit', 'kpi', 'month',
                HTML("<div class='jumbotron p-3 mb-2 col-12'>{}</div>".format(linebreaksbr(kpi.description))),
                Div(Field('value', css_class="form-control"), css_class="col-3"),
                Div('comments', css_class="col-12"),
                css_class="row"
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
        )


class KPICategoryForm(forms.ModelForm):

    class Meta:
        model = KPICategory
        fields = ['name', 'description', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={"cols": 54, "rows": 4, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)
        if self.instance.pk:
            self.body.title = u"{}".format(self.instance.name)
            self.body.form_action = reverse_lazy('category-edit', kwargs={'pk': self.instance.pk})
        else:
            self.body.title = u"New KPI Category"
            self.body.form_action = reverse_lazy('new-category')
        self.body.layout = Layout(
            Div(
                Div('priority', css_class="col-2"),
                Div('name', css_class="col-10"),
                Div('description', css_class="col-12 w-100"),
                css_class="row"
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
        )
