from django import forms
from django.urls import reverse_lazy

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout

from .models import KPI, KPIEntry


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


class KPIForm(forms.ModelForm):

    class Meta:
        model = KPI
        fields = ['name', 'description', 'category', 'kind', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={"cols": 54, "rows": 4}),
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
                css_class="row"
            )
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
        )


class BeamlineMonthForm(forms.ModelForm):

    class Meta:
        model = KPIEntry
        fields = ['beamline', 'month']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)

        self.body.title = u"New Beamline Report"
        self.body.form_action = reverse_lazy('new-beamline-month')
        self.body.layout = Layout(
            Div(
                Div('beamline', css_class="col-6"),
                Div(Field('month'), css_class="col-6"),
                css_class="row"
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
        )


class KPIEntryForm(forms.ModelForm):

    class Meta:
        model = KPIEntry
        fields = ['value', 'comments']
        widgets = {
            'comments': forms.Textarea(attrs={"cols": 54, "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.body = BodyHelper(self)
        self.footer = FooterHelper(self)
        if self.instance.pk:
            self.body.title = u"{}".format(self.instance.kpi.name)
            self.body.form_action = reverse_lazy('kpientry-edit', kwargs={'pk': self.instance.pk})
        self.body.layout = Layout(
            Div(
                Div('value', css_class="col-3"),
                HTML("<div class='col-9 mt-4'>{}</div>".format(self.instance.kpi.description)),
                Div('comments', css_class="col-12"),
                css_class="row"
            ),
        )
        self.footer.layout = Layout(
            StrictButton('Revert', type='reset', value='Reset', css_class="btn btn-secondary"),
            StrictButton('Save', type='submit', name="submit", value='save', css_class='btn btn-primary'),
        )
