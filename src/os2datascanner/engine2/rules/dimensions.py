from ..conversions.types import OutputType
from .rule import Rule, SimpleRule, Sensitivity


class DimensionsRule(SimpleRule):
    operates_on = OutputType.ImageDimensions
    type_label = "dimensions"

    def __init__(self,
            width_range=range(16, 16385),
            height_range=range(16, 16385),
            min_dim=128, *, sensitivity=None):
        super().__init__(sensitivity=sensitivity)
        self._width_range = width_range
        self._height_range = height_range
        self._min_dim = min_dim

    def match(self, content):
        if content is None:
            return

        (w, h) = content
        max_dim = max(w, h)
        if (w in self._width_range
                and h in self._height_range
                and max_dim >= self._min_dim):
            yield {
                "match": [w, h]
            }

    def to_json_object(self):
        return dict(**super().to_json_object(), **{
            "width": [self._width_range.start, self._width_range.stop],
            "height": [self._height_range.start, self._height_range.stop],
            "minimum": self._min_dim
        })

    @staticmethod
    @Rule.json_handler(type_label)
    def from_json_object(obj):
        return DimensionsRule(
                width_range=range(obj["width"][0], obj["width"][1]),
                height_range=range(obj["height"][0], obj["height"][1]),
                min_dim=obj["minimum"],
                sensitivity=Sensitivity.make_from_dict(obj))
