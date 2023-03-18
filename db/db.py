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
import shutil

from sqlalchemy import Column, Integer, String, create_engine, ForeignKey, Float, DateTime, func
from sqlalchemy.engine.default import DefaultDialect
from sqlalchemy.orm import declarative_base, declared_attr, sessionmaker, relationship
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

    measurements = relationship('MeasurementTbl')


class MeasurementTbl(Base, IDMixin):
    datastream_id = foreignkey('DatastreamTbl')
    value = Column(Float)
    timestamp = Column(DateTime, default=func.now())
    relative_time_seconds = Column(Float)
    value_string = stringcolumn(140)


class SessionCTX(object):
    def __init__(self, sess):
        self._sess = sess

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(self._sess, SessionCTX):
            return
        else:
            self._sess.__exit__(exc_type, exc_val, exc_tb)

    def query(self, *args, **kw):
        return self._sess.query(*args, **kw)

    def add(self, *args, **kw):
        return self._sess.add(*args, **kw)

    def flush(self, *args, **kw):
        return self._sess.flush(*args, **kw)

    def commit(self, *args, **kw):
        return self._sess.commit(*args, **kw)


class DBClient(Loggable):
    _session_factory = None

    def build(self):
        engine = self._get_engine()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def get_device(self, name, sess=None):
        with self.session(sess) as sess:
            q = sess.query(DeviceTbl)
            q = q.filter(DeviceTbl.name == name)
            return self._fetch_first(q)

    def get_datastream_names(self, device_name, sess=None):
        with self.session(sess) as sess:
            q = sess.query(DatastreamTbl)
            q = q.join(DeviceTbl)
            q = q.filter(DeviceTbl.name == device_name)
            q = q.order_by(DatastreamTbl.name)

            return [d.name for d in q.all()]

    def get_datastream(self, name, device_name, sess=None):
        with self.session(sess) as sess:
            q = sess.query(DatastreamTbl)
            q = q.join(DeviceTbl)
            q = q.filter(DeviceTbl.name == device_name)
            q = q.filter(DatastreamTbl.name == name)
            q = q.order_by(DatastreamTbl.id.desc())
            return self._fetch_first(q)

    def add_device(self, name):
        with self.session() as sess:
            self._add_unique(sess, DeviceTbl, name)

    def add_datastream(self, name, device_name, unique=True):
        with self.session() as sess:
            d = None
            if unique:
                d = self.get_datastream(name, device_name, sess=sess)

            if not d:
                dev = self.get_device(device_name, sess=sess)
                self._add(sess, DatastreamTbl(name=name, device_id=dev.id))

    def add_measurement(self, name, device_name, **kw):
        with self.session() as sess:
            d = self.get_datastream(name, device_name, sess=sess)
            if d:
                kw = {k: v for k, v in kw.items() if k in ('name', 'value',
                                                           'value_string',
                                                           'relative_time_seconds')}
                self._add(sess, MeasurementTbl(datastream_id=d.id, **kw))

    def backup(self):
        src = paths.database_path
        # dest = paths.database_backup()
        dest = paths.database_backup_path
        shutil.copyfile(src, dest)

    def _add_unique(self, sess, table, idenfitier, attr='name', **kw):
        with self.session(sess) as sess:
            q = sess.query(table)
            q = q.filter(getattr(table, attr) == idenfitier)

            if not self._fetch_first(q):
                kw[attr] = idenfitier
                record = table(**kw)
                self._add(sess, record)

    def _fetch_first(self, q, verbose=False):
        if verbose:
            self.debug(literalquery(q.statement))
        return q.first()

    def _add(self, sess, record, commit=True):
        with self.session(sess) as sess:
            sess.add(record)
            sess.flush()
            if commit:
                sess.commit()

    # def connect(self):
    #     pass
    # sess = self.get_session()
    # self.session_factory = sessionmaker(engine=engine)

    # def get_session(self, force=False):
    #     if not self.session or force:
    #         self.session = self.session_factory()
    #     return self.session

    def _get_engine(self):
        url = paths.database_path
        engine = create_engine(f'sqlite:///{url}')
        return engine

    def session(self, sess=None):
        if sess is None:
            factory = self.session_factory()
            sess = factory()

        sess = SessionCTX(sess)
        return sess

    def session_factory(self):
        factory = self._session_factory
        if not factory:
            factory = sessionmaker(
                bind=self._get_engine(),
                # autoflush=self.autoflush,
                # expire_on_commit=False,
                # autocommit=self.autocommit,
            )
            self._session_factory = factory

        return factory
# ============= EOF =============================================
