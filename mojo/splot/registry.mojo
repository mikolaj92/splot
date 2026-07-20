"""Host-registerable payload readers (not evaluators).

Profile `provider` strings dispatch here. Builtins are always available.
Hosts register *named recipes* that only map already-supplied candidate/state
fields into scalars/gates — no LLM/CV/random inside Splot.

Recipe grammar (signal):
  value | value:<field>     numeric payload/metadata field (default: signal field)
  product:<f1>,<f2>         product of two numeric fields
  sum:<f1>,<f2>             sum of two numeric fields
  min:<f1>,<f2>             min of two fields
  max:<f1>,<f2>             max of two fields
  invert | invert:<field>   1 - clamp01(field)
  bool | bool:<field>       true/1 → 1.0 else 0.0
  const:<number>            constant

Recipe grammar (gate / constraint provider):
  available                 candidate.available builtin
  bool | bool:<field>       pass if field is true/1
  gte:<field>,<threshold>   pass if field >= threshold
  gt / lte / lt             comparisons
"""

from std.collections import List
from splot.builtins import candidate_available, candidate_value, state_is_current
from splot.json_util import clamp01
from splot.models import Candidate, SplotState
from splot.normalize import to_float_json


struct StrPair(Copyable, Movable):
    var left: String
    var right: String

    def __init__(out self, left: String = "", right: String = ""):
        self.left = left
        self.right = right

    def __init__(out self, *, copy: Self):
        self.left = copy.left
        self.right = copy.right


struct GateResult(Copyable, Movable):
    var passed: Bool
    var handled: Bool

    def __init__(out self, passed: Bool = True, handled: Bool = True):
        self.passed = passed
        self.handled = handled

    def __init__(out self, *, copy: Self):
        self.passed = copy.passed
        self.handled = copy.handled


def _split_once(text: String, sep: String) raises -> StrPair:
    var n = text.byte_length()
    var sn = sep.byte_length()
    if sn == 0:
        return StrPair(text, "")
    var i = 0
    while i + sn <= n:
        var matched = True
        var j = 0
        while j < sn:
            if text[byte = i + j] != sep[byte = j]:
                matched = False
                break
            j += 1
        if matched:
            var left = String("")
            var k = 0
            while k < i:
                left += String(text[byte = k])
                k += 1
            var right = String("")
            k = i + sn
            while k < n:
                right += String(text[byte = k])
                k += 1
            return StrPair(left, right)
        i += 1
    return StrPair(text, "")


def _split_csv2(text: String) raises -> StrPair:
    return _split_once(text, ",")


struct ReaderRegistry(Copyable, Movable):
    """Named payload readers. Builtins always work; host may register more."""

    var signal_names: List[String]
    var signal_recipes: List[String]
    var gate_names: List[String]
    var gate_recipes: List[String]

    def __init__(out self):
        self.signal_names = List[String]()
        self.signal_recipes = List[String]()
        self.gate_names = List[String]()
        self.gate_recipes = List[String]()

    def __init__(out self, *, copy: Self):
        self.signal_names = copy.signal_names.copy()
        self.signal_recipes = copy.signal_recipes.copy()
        self.gate_names = copy.gate_names.copy()
        self.gate_recipes = copy.gate_recipes.copy()

    @staticmethod
    def with_builtins() -> ReaderRegistry:
        return ReaderRegistry()

    def register_signal_reader(mut self, name: String, recipe: String) raises:
        if name == "" or name == "candidate.value" or name == "state.is_current":
            raise Error("splot: cannot re-register builtin signal reader: " + name)
        var i = 0
        while i < len(self.signal_names):
            if self.signal_names[i] == name:
                self.signal_recipes[i] = recipe
                return
            i += 1
        self.signal_names.append(name)
        self.signal_recipes.append(recipe)

    def register_gate_reader(mut self, name: String, recipe: String) raises:
        if name == "" or name == "candidate.available":
            raise Error("splot: cannot re-register builtin gate reader: " + name)
        var i = 0
        while i < len(self.gate_names):
            if self.gate_names[i] == name:
                self.gate_recipes[i] = recipe
                return
            i += 1
        self.gate_names.append(name)
        self.gate_recipes.append(recipe)

    def has_signal_reader(self, name: String) -> Bool:
        if name == "candidate.value" or name == "state.is_current":
            return True
        for n in self.signal_names:
            if n == name:
                return True
        return False

    def has_gate_reader(self, name: String) -> Bool:
        if name == "candidate.available" or name == "":
            return True
        for n in self.gate_names:
            if n == name:
                return True
        return False

    def _signal_recipe(self, name: String) raises -> String:
        var i = 0
        while i < len(self.signal_names):
            if self.signal_names[i] == name:
                return self.signal_recipes[i]
            i += 1
        return String("")

    def _gate_recipe(self, name: String) raises -> String:
        var i = 0
        while i < len(self.gate_names):
            if self.gate_names[i] == name:
                return self.gate_recipes[i]
            i += 1
        return String("")

    def _eval_signal_recipe(
        self,
        recipe: String,
        candidate: Candidate,
        field: String,
        state: SplotState,
    ) raises -> Float64:
        var r = recipe
        if r == "" or r == "value":
            return candidate_value(candidate, field)
        var head_tail = _split_once(r, ":")
        var head = head_tail.left
        var rest = head_tail.right
        if head == "value":
            var f = rest if rest != "" else field
            return candidate_value(candidate, f)
        if head == "const":
            return to_float_json(rest)
        if head == "bool":
            var bf = rest if rest != "" else field
            var raw = candidate_value(candidate, bf)
            return 1.0 if raw != 0.0 else 0.0
        if head == "invert":
            var inf = rest if rest != "" else field
            return 1.0 - clamp01(candidate_value(candidate, inf))
        if head == "product":
            var ab = _split_csv2(rest)
            return candidate_value(candidate, ab.left) * candidate_value(candidate, ab.right)
        if head == "sum":
            var ab2 = _split_csv2(rest)
            return candidate_value(candidate, ab2.left) + candidate_value(candidate, ab2.right)
        if head == "min":
            var ab3 = _split_csv2(rest)
            var a = candidate_value(candidate, ab3.left)
            var b = candidate_value(candidate, ab3.right)
            return a if a < b else b
        if head == "max":
            var ab4 = _split_csv2(rest)
            var a2 = candidate_value(candidate, ab4.left)
            var b2 = candidate_value(candidate, ab4.right)
            return a2 if a2 > b2 else b2
        return candidate_value(candidate, r)

    def read_signal(
        self,
        provider: String,
        candidate: Candidate,
        field: String,
        state: SplotState,
    ) raises -> Float64:
        """Read a signal scalar. Unknown unregistered provider → 0 (fail closed)."""
        if provider == "candidate.value" or provider == "":
            return candidate_value(candidate, field)
        if provider == "state.is_current":
            return state_is_current(candidate, state)
        var recipe = self._signal_recipe(provider)
        if recipe == "":
            return 0.0
        return self._eval_signal_recipe(recipe, candidate, field, state)

    def read_gate(
        self,
        provider: String,
        candidate: Candidate,
        state: SplotState,
    ) raises -> GateResult:
        """Return GateResult(passed, handled). handled=False → unknown provider."""
        if provider == "candidate.available":
            return GateResult(candidate_available(candidate), True)
        if provider == "":
            return GateResult(True, True)
        var recipe = self._gate_recipe(provider)
        if recipe == "":
            return GateResult(False, False)
        if recipe == "available":
            return GateResult(candidate_available(candidate), True)
        var head_tail = _split_once(recipe, ":")
        var head = head_tail.left
        var rest = head_tail.right
        if head == "bool" or recipe == "bool":
            var f = rest if rest != "" else "available"
            var v = candidate_value(candidate, f)
            return GateResult(v != 0.0, True)
        if head == "gte" or head == "gt" or head == "lte" or head == "lt":
            var ab = _split_csv2(rest)
            var left = candidate_value(candidate, ab.left)
            var right = to_float_json(ab.right)
            if head == "gte":
                return GateResult(left >= right, True)
            if head == "gt":
                return GateResult(left > right, True)
            if head == "lte":
                return GateResult(left <= right, True)
            return GateResult(left < right, True)
        var v2 = candidate_value(candidate, recipe)
        return GateResult(v2 != 0.0, True)
