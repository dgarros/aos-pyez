# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

from os import path
from copy import copy
import json

import requests

from apstra.aosom.exc import SessionRqstError, SessionError

# #############################################################################
# #############################################################################
#
#                                Collection Item
#
# #############################################################################
# #############################################################################


class CollectionItem(object):
    """
    An item within a given :class:`Collection`.  The following public attributes
    are available:

        * :attr:`name` - the user provided item name
        * :attr:`api` - the instance to the :mod:`Session.Api` instance.

    """
    def __init__(self, collection, name, datum):
        self.name = name
        self.collection = collection
        self.api = collection.api
        self.datum = datum
        self._url = None

    # =========================================================================
    #
    #                             PROPERTIES
    #
    # =========================================================================

    # -------------------------------------------------------------------------
    # PROPERTY: id
    # -------------------------------------------------------------------------

    @property
    def id(self):
        """
        Property access for the item AOS unique ID value.

        Returns:
            - id string value if the item exists
            - `None` if the item does not exist.
        """
        return self.datum.get(self.collection.UNIQUE_ID) if self.name in self.collection else None

    # -------------------------------------------------------------------------
    # PROPERTY: url
    # -------------------------------------------------------------------------

    @property
    def url(self):
        """
        Property accessor for item URL.

        :getter: returns the URL string for this specific item
        """
        if self._url:
            return self._url

        if not self.id:
            return None

        self._url = "%s/%s" % (self.collection.url, self.id)
        return self._url

    # -------------------------------------------------------------------------
    # PROPERTY: exists
    # -------------------------------------------------------------------------

    @property
    def exists(self):
        """
        Property accessor to determine if item exists on the AOS-server.

        Returns:
            - True if the item exists
            - False if the item does not exist
        """
        return bool(self.datum and self.id)

    # -------------------------------------------------------------------------
    # PROPERTY: value
    # -------------------------------------------------------------------------

    @property
    def value(self):
        """
        Property accessor for item value.

        :getter: returns the item data dictionary
        :deletter: deletes the item from the AOS-server

        Raises:
            SessionRqstError: upon any HTTP requests issue.
        """
        return self.datum

    @value.deleter
    def value(self):
        """
        Used to delete the item from the AOS-server.  For example:

            >>> del aos.IpPools['Servers-IpAddrs'].value

        """
        got = requests.delete(self.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(
                resp=got,
                message='unable to delete item (%s): %s' %
                        (self.name, got.reason))

        self.collection -= self

    # =========================================================================
    #
    #                             PUBLIC METHODS
    #
    # =========================================================================

    def write(self, value=None):
        """
        Used to write the item value back to the AOS-server.

        Raises:
            SessionRqstError: upon HTTP request issue
        """

        if value:
            self.datum = copy(value)

        if not self.exists:
            return self.create()

        got = requests.put(self.url,
                            headers=self.api.headers,
                            json=self.datum)

        if not got.ok:
            raise SessionRqstError(
                message='unable to update: %s' % got.reason,
                resp=got)

    def read(self):
        """
        Retrieves the item value from the AOS-server.

        Raises:
            SessionRqstError: upon REST call error

        Returns: a copy of the item value, usually a :class:`dict`.
        """
        got = requests.get(self.url, headers=self.api.headers)
        if not got.ok:
            raise SessionRqstError(
                resp=got,
                message='unable to get item name: %s' % self.name)

        self.datum = copy(got.json())
        return self.datum

    def create(self, value=None):
        """
        Creates a new item using the `value` provided.

        Args:
            value (dict): item value dictionary.

        Raises:
            SessionError: upon any HTTP request issue.

        Returns:
            - the result of the :meth:`write` call.
        """
        if self.exists:
            raise SessionError(message='cannot create, already exists')

        if value:
            self.datum = copy(value)

        got = requests.post(self.collection.url,
                            headers=self.api.headers,
                            json=self.datum)

        if not got.ok:
            raise SessionRqstError(
                message='unable to create: %s' % got.reason,
                resp=got)

        body = got.json()
        self.datum[self.collection.UNIQUE_ID] = body[self.collection.UNIQUE_ID]

        # now add this item to the parent collection so it can be used by other
        # invocations

        self.collection += self

    def jsonfile_save(self, dirpath=None, filename=None, indent=3):
        """
        Saves the contents of the item to a JSON file.

        Args:
            dirpath:
                The path to the directory to store the file.  If none provided
                then the file will be stored in the current working directory

            filename:
                The name of the file, stored within the `dirpath`.  If
                not provided, then the filename will be the item name.

            indent:
                The indent spacing in the JSON file.

        Raises:
            IOError: for any I/O related error
        """
        ofpath = path.join(dirpath or '.', filename or self.name) + '.json'
        json.dump(self.value, open(ofpath, 'w+'), indent=indent)

    def jsonfile_load(self, filepath):
        """
        Loads the contents of the JSON file, `filepath`, as the item value.

        Args:
            filepath (str): complete path to JSON file

        Raises:
            IOError: for any I/O related error
        """
        self.datum = json.load(open(filepath))

    def __str__(self):
        return json.dumps({
            'name': self.name,
            'id': self.id,
            'value': self.value
        }, indent=3)
