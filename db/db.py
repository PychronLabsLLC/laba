# ===============================================================================
# Copyright 2023 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
import os

from sqlalchemy import Column, Integer, String, create_engine, ForeignKey, Float, DateTime, func
from sqlalchemy.engine.default import DefaultDialect
from sqlalchemy.orm import declarative_base, declared_attr, sessionmaker
from sqlalchemy.sql.sqltypes import NullType, String as SQLString

from loggable import Loggable
from paths import paths

Base = declarative_base()


def stringcolumn(size=40, *args, **kw):
    return Column(String(size), *args, **kw)


def foreignkey(name):
    return Column(Integer, ForeignKey("{}.id".format(name)))


class StringLiteral(SQLString):
    """Teach SA how to literalize various things."""

    def literal_processor(self, dialect):
        super_processor = super(StringLiteral, self).literal_processor(dialect)

        def process(value):
            if isinstance(value, int):
                return str(value)
            if not isinstance(value, str):
                value = str(value)
            result = super_processor(value)
            if isinstance(result, bytes):
                result = result.decode(dialect.encoding)
            return result

        return process


class LiteralDialect(DefaultDialect):
    colspecs = {
        # prevent various encoding explosions
        String: StringLiteral,
        # teach SA about how to literalize a datetime
        DateTime: StringLiteral,
        # don't format py2 long integers to NULL
        NullType: StringLiteral,
    }


def literalquery(statement):
    """NOTE: This is entirely insecure. DO NOT execute the resulting strings."""
    # import sqlalchemy.orm
    # if isinstance(statement, sqlalchemy.orm.Query):
    #     statement = statement.statement

    return statement.compile(
        dialect=LiteralDialect(),
        compile_kwargs={"literal_binds": True},
    ).string


class BaseMixin(object):
    @declared_attr
    def __tablename__(self):
        return self.__name__


class IDMixin(BaseMixin):
    id = Column(Integer, primary_key=True)


class NameMixin(IDMixin):
    name = stringcolumn(80)

    def __repr__(self):
        return "{}<{}>".format(self.__class__.__name__, self.name)


class DeviceTbl(Base, NameMixin):
    pass


class DatastreamTbl(Base, NameMixin):
    device_id = foreignkey('DeviceTbl')


class MeasurementTbl(Base, IDMixin):
    datastream_id = foreignkey('DatastreamTbl')
    value = Column(Float)
    timestamp = Column(DateTime, default=func.now())
    relative_time_seconds = Column(Float)
    value_string = stringcolumn(140)


class DBClient(Loggable):
    session = None

    def build(self, drop=False):
        engine = self._get_engine()

        if drop:
            Base.metadata.drop_all(bind=engine)

        Base.metadata.create_all(bind=engine)

    def add_measurement(self, value, name, device_name, **kw):
        d = self.get_datastream(name, device_name)
        if d:
            self._add(MeasurementTbl(value=value,
                                     datastream_id=d.id,
                                     **kw))

    def add_datastream(self, name, device_name):
        d = self.get_datastream(name, device_name)
        if not d:
            dev = self.get_device(device_name)
            self._add(DatastreamTbl(name=name, device_id=dev.id))

    def get_device(self, name):
        sess = self.get_session()
        q = sess.query(DeviceTbl)
        q = q.filter(DeviceTbl.name == name)
        return self._fetch_first(q)

    def get_datastream(self, name, device_name):
        sess = self.get_session()
        q = sess.query(DatastreamTbl)
        q = q.join(DeviceTbl)
        q = q.filter(DeviceTbl.name == device_name)
        q = q.filter(DatastreamTbl.name == name)
        return self._fetch_first(q)

    def add_device(self, name):
        self._add_unique(DeviceTbl, name)

    def _add_unique(self, table, idenfitier, attr='name', sess=None, **kw):
        if sess is None:
            sess = self.get_session()

        q = sess.query(table)
        q = q.filter(getattr(table, attr) == idenfitier)

        if not self._fetch_first(q):
            kw[attr] = idenfitier
            record = table(**kw)
            self._add(record, sess=sess)

    def _fetch_first(self, q, verbose=False):
        if verbose:
            self.debug(literalquery(q.statement))
        return q.first()

    def _add(self, record, commit=True, sess=None):
        if sess is None:
            sess = self.get_session()

        sess.add(record)
        sess.flush()
        if commit:
            sess.commit()

    # def connect(self):
    #     pass
    # sess = self.get_session()
    # self.session_factory = sessionmaker(engine=engine)

    def get_session(self, force=False):
        if not self.session or force:
            self.session = self.session_factory()
        return self.session

    def _get_engine(self):
        url = paths.database_path
        engine = create_engine(f'sqlite:///{url}')
        return engine

    def session_factory(self):
        return sessionmaker(
            bind=self._get_engine(),
            # autoflush=self.autoflush,
            # expire_on_commit=False,
            # autocommit=self.autocommit,
        )()
# ============= EOF =============================================
