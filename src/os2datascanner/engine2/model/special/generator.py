from itertools import product

from ..core import Source, Handle, Resource


MAGIC_MIME = "application/x-os2datascanner-generatorsource-handle"


class GeneratorSource(Source):
    type_label = "generator"

    def __init__(self, base, properties):
        self._base = base
        self._properties = properties

    def _generate_state(self, sm):
        yield None

    def _censor(self):
        raise NotImplementedError(
                "GeneratorSource doesn't know enough about the Sources"
                " it creates to be censorable") # XXX

    def handles(self, sm):
        iterables = []
        for k in self._properties.keys():
            v = self._properties[k]
            if not isinstance(v, list):
                v = [v]
            iterables.append([(k, vl) for vl in v])
        for idx, property_pairs in enumerate(product(*iterables)):
            bcp = self._base.copy()
            for k, v in property_pairs:
                bcp[k] = v
            yield GeneratorHandle(self, str(idx), bcp)

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "base": self._base,
            "properties": self._properties
        })

    @staticmethod
    @Source.json_handler(type_label)
    def from_json_object(obj):
        return GeneratorSource(obj["base"], obj["properties"])

    @staticmethod
    @Source.mime_handler(MAGIC_MIME)
    def from_handle(handle):
        return Source.from_json_object(handle.get_json())


class GeneratorHandle(Handle):
    type_label = "generator"

    def __init__(self, source, path, json):
        super().__init__(source, path)
        self._json = json

    def get_json(self):
        return self._json

    def guess_type(self):
        return MAGIC_MIME

    @property
    def presentation(self):
        return "(generated)" # XXX

    def censor(self):
        return GeneratorHandle(self.source._censor(), self.relative_path)

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "json": self._json
        })

    @staticmethod
    @Handle.json_handler(type_label)
    def from_json_object(obj):
        return GeneratorHandle(
                Source.from_json_object(obj["source"]),
                obj["path"], obj["json"])

    def follow(self, sm):
        return GeneratorResource(sm, self)


class GeneratorResource(Resource):
    def compute_type(self):
        return MAGIC_MIME
