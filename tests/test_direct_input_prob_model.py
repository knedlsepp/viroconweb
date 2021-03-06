from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from contour.forms import VariableNumber, VariablesForm


class DirectInputProbModelTestCase(TestCase):

    def setUp(self):
        # Login
        self.client = Client()
        self.client.post(reverse('user:authentication'),
                           {'username' : 'max_mustermann',
                            'password': 'Musterpasswort2018'})

    def test_direct_input_prob_model(self):
        # Create a direct input form
        form = VariableNumber({'variable_number' : '2'})
        self.assertTrue(form.is_valid())

        # Open direct input url and check if the html is correct via the
        # numbers of variable form
        response = self.client.post('/models/number-of-variables/',
                                    {'variable_number' : 3},
                                    follow=True)
        self.assertContains(response, "The first character should be "
                                      "capitalized.", status_code=200)

        # Open direct input url and check if the html is correct drectly
        response = self.client.post(reverse('contour:probabilistic_model_add',
                                            args=['02']))
        self.assertContains(response, "The first character should be "
                                      "capitalized.", status_code=200)

        # Create a form containing the information of the model
        form_input_dict = {
                'variable_name_0' : 'significant wave height [m]',
                'variable_symbol_0' : 'Hs',
                'distribution_0' : 'Weibull',
                'scale_0_0' : '2.776',
                'shape_0_0' : '1.471',
                'location_0_0' : '0.888',
                'variable_name_1' : 'peak period [s]',
                'variable_symbol_1' : 'Tp',
                'distribution_1': 'Weibull',
                'scale_dependency_1': '0f2',
                'scale_1_0' : '0.1',
                'scale_1_1' : '1.489',
                'scale_1_2' : '0.1901',
                'shape_dependency_1' : '0f1',
                'shape_1_0' : '0.04',
                'shape_1_1' : '0.1748',
                'shape_1_2' : '-0.2243',
                'location_dependency_1': '!None',
                'location_1_0' : '0',
                'location_1_1' : '0',
                'location_1_2' : '0',
                'collection_name' : 'direct input Vanem2012'
            }
        form = VariablesForm(data=form_input_dict, variable_count=2)
        self.assertTrue(form.is_valid())

        # Test the view method and the html which will be generated
        response = self.client.post(reverse('contour:probabilistic_model_add',
                                            args=['02']),
                                    form_input_dict,
                                    follow=True)
        self.assertContains(response, "Probabilistic models",
                            status_code=200)
