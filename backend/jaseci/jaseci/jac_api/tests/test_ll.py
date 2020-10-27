from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient

from core.utils.utils import TestCaseHelper
import uuid
import base64


class test_ll(TestCaseHelper):
    """Test the authorized user node API"""

    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user(
            'JSCITfdfdEST_test@jaseci.com',
            'password'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.master = self.user.get_master()
        payload = {'op': 'create_graph', 'name': 'Something'}
        res = self.client.post(reverse(f'jac_api:{payload["op"]}'), payload)
        self.gph = self.master._h.get_obj(uuid.UUID(res.data['jid']))
        payload = {'op': 'create_sentinel', 'name': 'Something'}
        res = self.client.post(reverse(f'jac_api:{payload["op"]}'), payload)
        self.snt = self.master._h.get_obj(uuid.UUID(res.data['jid']))
        ll_file = base64.b64encode(
            open("jac_api/tests/ll.jac").read().encode())
        payload = {'op': 'set_jac_code', 'snt': self.snt.id.urn,
                   'code': ll_file, 'encoded': True}
        res = self.client.post(
            reverse(f'jac_api:{payload["op"]}'), payload, format='json')
        payload = {'op': 'compile', 'snt': self.snt.id.urn}
        res = self.client.post(
            reverse(f'jac_api:{payload["op"]}'), payload)
        self.run_walker('init', {})

    def tearDown(self):
        super().tearDown()

    def run_walker(self, w_name, ctx, prime=None):
        """Helper to make calls to execute walkers"""
        if(not prime):
            payload = {'snt': self.snt.id.urn, 'name': w_name,
                       'nd': self.gph.id.urn, 'ctx': ctx}
        else:
            payload = {'snt': self.snt.id.urn, 'name': w_name,
                       'nd': prime, 'ctx': ctx}
        res = self.client.post(
            reverse(f'jac_api:prime_run'), payload, format='json')
        return res.data

    def test_ll_today_new(self):
        """Test LifeLogify Jac Implementation"""
        data = self.run_walker('get_gen_day', {})
        self.assertEqual(data[0]['kind'], 'day')
        jid = data[0]['jid']
        data = self.run_walker('get_gen_day', {})
        self.assertEqual(data[0]['jid'], jid)

    def test_ll_create_get_workette(self):
        """Test LifeLogify Jac Implementation"""
        data = self.run_walker('get_gen_day', {})
        self.assertEqual(data[0]['kind'], 'day')
        jid = data[0]['jid']
        data = self.run_walker('create_workette', {}, prime=jid)
        self.assertEqual(data[0]['kind'], 'workette')
        data = self.run_walker('create_workette', {}, prime=jid)
        self.assertEqual(data[0]['kind'], 'workette')
        data = self.run_walker('get_workettes', {}, prime=jid)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['kind'], 'workette')
        self.assertEqual(data[1]['kind'], 'workette')
        wjid = data[0]['jid']
        data = self.run_walker('create_workette', {}, prime=wjid)
        data = self.run_walker('create_workette', {}, prime=wjid)
        data = self.run_walker('create_workette', {}, prime=wjid)
        data = self.run_walker('get_workettes', {}, prime=wjid)
        self.assertEqual(len(data), 3)
        data = self.run_walker('get_workettes', {}, prime=jid)
        self.assertEqual(len(data), 2)
        data = self.run_walker('get_workettes_deep', {}, prime=jid)
        self.assertEqual(len(data), 5)

    def test_ll_get_date(self):
        """Test LifeLogify Jac Implementation"""
        data = self.run_walker('get_gen_day', {})
        data = self.run_walker('gen_rand_life', {})
        data = self.run_walker('get_latest_day', {})
        wjid = data[0]['jid']
        data = self.run_walker('get_workettes', {}, prime=wjid)
        self.assertEqual(len(data), 0)
        data = self.run_walker('get_latest_day', {'before_date': '2020-03-01'})
        wjid = data[0]['jid']
        data = self.run_walker('get_workettes', {}, prime=wjid)
        self.assertGreater(len(data), 1)

    def test_ll_carry_forward_simple(self):
        """Test LifeLogify Jac Implementation"""
        data = self.run_walker('gen_rand_life', {})
        data = self.run_walker('get_gen_day', {})
        wjid = data[0]['jid']
        data = self.run_walker('get_workettes', {}, prime=wjid)
        self.assertGreater(len(data), 1)

    def test_ll_delete_workette(self):
        """Test LifeLogify Jac Implementation"""
        data = self.run_walker('get_gen_day', {})
        self.assertEqual(data[0]['kind'], 'day')
        jid = data[0]['jid']
        data = self.run_walker('create_workette', {}, prime=jid)
        self.assertEqual(data[0]['kind'], 'workette')
        data = self.run_walker('create_workette', {}, prime=jid)
        self.assertEqual(data[0]['kind'], 'workette')
        data = self.run_walker('get_workettes', {}, prime=jid)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['kind'], 'workette')
        self.assertEqual(data[1]['kind'], 'workette')
        wjid = data[0]['jid']
        data = self.run_walker('create_workette', {}, prime=wjid)
        data = self.run_walker('create_workette', {}, prime=wjid)
        data = self.run_walker('create_workette', {}, prime=wjid)
        data = self.run_walker('get_workettes', {}, prime=wjid)
        self.assertEqual(len(data), 3)
        data = self.run_walker('delete_workette', {}, prime=wjid)
        data = self.run_walker('get_workettes', {}, prime=jid)
        self.assertEqual(len(data), 1)
        data = self.run_walker('get_workettes_deep', {}, prime=jid)
        self.assertEqual(len(data), 1)

    def test_ll_delete_workette_no_leaks(self):
        """Test LifeLogify Jac Implementation"""
        data = self.run_walker('get_gen_day', {})
        self.assertEqual(data[0]['kind'], 'day')
        jid = data[0]['jid']
        data = self.run_walker('create_workette', {}, prime=jid)
        self.assertEqual(data[0]['kind'], 'workette')
        len_before = len(self.master._h.mem.keys())
        data = self.run_walker('create_workette', {}, prime=jid)
        self.assertEqual(data[0]['kind'], 'workette')
        data = self.run_walker('get_workettes', {}, prime=jid)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['kind'], 'workette')
        self.assertEqual(data[1]['kind'], 'workette')
        wjid = data[1]['jid']
        data = self.run_walker('create_workette', {}, prime=wjid)
        data = self.run_walker('create_workette', {}, prime=wjid)
        data = self.run_walker('create_workette', {}, prime=wjid)
        data = self.run_walker('get_workettes', {}, prime=wjid)
        self.assertEqual(len(data), 3)
        data = self.run_walker('delete_workette', {}, prime=wjid)
        data = self.run_walker('get_workettes', {}, prime=jid)
        self.assertEqual(len(data), 1)
        data = self.run_walker('get_workettes_deep', {}, prime=jid)
        self.assertEqual(len(data), 1)
        len_after = len(self.master._h.mem.keys())
        self.assertEqual(len_before, len_after)
