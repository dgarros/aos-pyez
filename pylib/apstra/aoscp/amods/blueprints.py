import requests
import json
from operator import itemgetter
from copy import copy

from apstra.aoscp.collection import Collection, CollectionItem
from apstra.aoscp.exc import SessionRqstError

__all__ = ['Blueprints', 'BlueprintParamValueTransform']


class BlueprintParamValueTransformer(object):
    def __init__(self, collection,
                 read_given='by_id', read_item=None,
                 write_given='by_name', write_item=None):

        self.collection = collection
        self._read_given = read_given
        self._read_item = read_item or collection.DISPLAY_NAME
        self._write_given = write_given
        self._write_item = write_item or collection.UNIQUE_ID

    def read(self, value):
        """
        transforms the native API stored value (e.g. 'id') into something else,
        (e.g. 'display_name')
        """
        rd_xf = {}
        for _key, _val in value.iteritems():
            item = self.collection.cache[self._read_given][_val]
            rd_xf[_key] = item[self._read_item]

        return rd_xf

    def write(self, value):
        wr_xf = {}
        for _key, _val in value.iteritems():
            item = self.collection.cache[self._write_given][_val]
            wr_xf[_key] = item[self._write_item]

        return wr_xf


class BlueprintItemParamsItem(object):
    Transformer = BlueprintParamValueTransformer

    def __init__(self, blueprint, name, datum):
        self.api = blueprint.api
        self.blueprint = blueprint
        self.name = name
        self._param = {
            'info': datum,
            'value': None
        }

    @property
    def info(self):
        return self._param.get('info')

    @property
    def url(self):
        return "%s/slots/%s" % (self.blueprint.url, self.name)

    # #### ----------------------------------------------------------
    # ####   PROPERTY: value [read, write, delete]
    # #### ----------------------------------------------------------

    @property
    def value(self):
        return self._param.get('value') or self.read()

    @value.setter
    def value(self, replace_value):
        self.write(replace_value)

    @value.deleter
    def value(self):
        self.clear()

    # #### ----------------------------------------------------------
    # ####
    # ####                   PUBLIC METHODS
    # ####
    # #### ----------------------------------------------------------

    def write(self, replace_value):
        got = requests.put(self.url, headers=self.api.headers, json=replace_value)
        if not got.ok:
            raise SessionRqstError(
                resp=got,
                message='unable to clear slot: %s' % self.name)

        self._param['value'] = replace_value

    def read(self):
        got = requests.get(self.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(
                resp=got,
                message='unable to get value on slot: %s' % self.name)

        self._param['value'] = copy(got.json())
        return self._param['value']


    def clear(self):
        self.write({})

    def __str__(self):
        return json.dumps({
            'Blueprint Name': self.blueprint.name,
            'Blueprint ID': self.blueprint.id,
            'Parameter Name': self.name,
            'Parameter Info': self.info,
            'Parameter Value': self.value}, indent=3)


class BlueprintItemParamsCollection(object):
    Item = BlueprintItemParamsItem

    class ItemIter(object):
        def __init__(self, params):
            self._params = params
            self._iter = iter(self._params.names)

        def next(self):
            name = next(self._iter)
            return name, self._params[name].value

    def __init__(self, parent):
        self.api = parent.api
        self.blueprint = parent
        self._slots = None
        self._cache = {}

    @property
    def names(self):
        if not self._cache:
            self.digest()

        return self._cache['names']

    def digest(self):
        got = requests.get("%s/slots" % self.blueprint.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(resp=got, message="error fetching slots")

        get_name = itemgetter('name')
        self._cache['list'] = got.json()
        self._cache['names'] = map(get_name, self._cache['list'])
        self._cache['by_name'] = {get_name(i): i for i in self._cache['list']}

    def __contains__(self, item_name):
        return bool(item_name in self._cache.get('names'))

    def __getitem__(self, item_name):
        if not self._cache:
            self.digest()

        # we want a KeyError to raise if the caller provides an unknown item_name
        return self.Item(self.blueprint, item_name, self._cache['by_name'][item_name])

    def __iter__(self):
        return self.ItemIter(self)


class BlueprintCollectionItem(CollectionItem):

    def __init__(self, parent, datum):
        super(BlueprintCollectionItem, self).__init__(parent, datum)
        self.params = BlueprintItemParamsCollection(self)

    def __repr__(self):
        return str(self.datum)


class Blueprints(Collection):
    RESOURCE_URI = 'blueprints'

    class Item(BlueprintCollectionItem):
        pass
