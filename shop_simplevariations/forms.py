# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _ 

class SimpleVariationsForm(forms.Form):
    EMPTIES_LABELS = {}

    def __init__(self, instance, *args, **kwargs):
        super (SimpleVariationsForm, self).__init__(*args, **kwargs)
        self._build_form(instance)

    def _get_empty_label_for(self, optiongroup):
        """
        Gets the empty label for an optiongroup slug.
        """
        if self.EMPTIES_LABELS.has_key(optiongroup):
            return self.EMPTIES_LABELS.get(optiongroup)

        return None
    def _build_form(self, instance):
        """
        Builds the form based on the object passed in the instance
        """
        # Generate the fields for the option groups
        for optiongroup in instance.option_groups.all():
            kwargs = {}
            empty_label = self._get_empty_label_for(optiongroup.slug)
            if empty_label:
                kwargs['empty_label'] = empty_label
            field = forms.ModelChoiceField(queryset=optiongroup.option_set.all(), label=optiongroup.name, **kwargs)
            field_name = 'add_item_option_group_%s' % (optiongroup.id, )
            self.fields[field_name] = field

        # Set the value of the add_item_id
        self.fields['add_item_id'].initial = instance.id


    add_item_id = forms.CharField(widget=forms.HiddenInput)
    add_item_quantity = forms.ChoiceField(label=_(u'Quantity'), choices=[(i,i) for i in range(1,11)])
