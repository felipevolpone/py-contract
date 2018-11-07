import json
from pprint import pprint


class Response:

    def __init__(self, response_as_dict):
        self.__as_dict = response_as_dict
        self.status = response_as_dict['status']
        self.headers = response_as_dict['headers']
        self.body = response_as_dict['body']


class Request:

    def __init__(self, request_as_dict):
        self.__as_dict = request_as_dict
        self.method = request_as_dict['method']
        self.path = request_as_dict['path']
        self.headers = request_as_dict['headers']


class Interaction:

    def __init__(self, interaction_as_dict):
        self.__as_dict = interaction_as_dict
        self.description = interaction_as_dict['description']
        self.provider_state = interaction_as_dict['provider_state']
        self.request = Request(interaction_as_dict['request'])
        self.response = Response(interaction_as_dict['response'])


class ConsumerRepresentation:

    def __init__(self, pact_path):
        self.__pact_path = pact_path
        self.setup()

    def setup(self):
        self.pact = json.loads(open(self.__pact_path, 'r').read())
        self.consumer_name = self.pact['consumer']['name']
        self.provider_name = self.pact['provider']['name']
        self.interactions = [Interaction(interaction_as_dict)
                             for interaction_as_dict in self.pact['interactions']]


class Pact:

    def __init__(self, pact_path):
        self.consumer = ConsumerRepresentation(pact_path)

    def select(self, interaction_description):
        for interaction in self.consumer.interactions:
            if interaction.description == interaction_description:
                self.selected_interaction = interaction
                break

        if self.selected_interaction is None:
            raise Exception("There is no interaction with name {}".format(interaction_description))

        return self

    def assert_it(self):
        self.__assert_status()
        self.__assert_fields()
        self.__assert_values()

    def __assert_status(self):
        print("expected {} ; given {}".format(self.selected_interaction.response.status,
                                              self.response.status_code))
        assert self.response.status_code == self.selected_interaction.response.status

    def __assert_fields(self):
        response_body = self.response.json()
        expected_keys = self.selected_interaction.response.body.keys()
        assert set(expected_keys).issubset(set(response_body.keys())), expected_keys

    def __assert_values(self):
        for key, value in self.selected_interaction.response.body.items():
            message = "expected {} ; given {}".format(value, self.response.json()[key])
            assert value == self.response.json()[key], message

        return self

    def mount_request(self):
        self.url = self.selected_interaction.request.path
        self.headers = self.selected_interaction.request.headers
        self.method = self.selected_interaction.request.method
        return self

    def call(self, client):
        if self.method != 'get':
            raise Exception("Only HTTP GET is supported for now")

        self.response = getattr(client, self.method)(self.url)
        return self

    def debug(self):
        pprint(self.response.json())
        return self
