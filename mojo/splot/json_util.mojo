"""Small JSON helpers for Splot Mojo (EmberJson)."""

from emberjson import Value, to_string


def parse_json(text: String) raises -> Value:
    return Value(parse_string=text)


def dump_json(value: Value) raises -> String:
    return to_string(value)


def obj_string(root: Value, key: String, default: String = "") raises -> String:
    if not root.is_object() or key not in root.object():
        return default
    var item = root.object()[key].copy()
    if item.is_string():
        return item.string()
    if item.is_null():
        return default
    if item.is_int():
        return String(item.int())
    if item.is_float():
        return String(item.float())
    if item.is_bool():
        return "true" if item.bool() else "false"
    return to_string(item)


def obj_float(root: Value, key: String, default: Float64 = 0.0) raises -> Float64:
    if not root.is_object() or key not in root.object():
        return default
    var item = root.object()[key].copy()
    if item.is_float():
        return item.float()
    if item.is_int():
        return Float64(item.int())
    if item.is_uint():
        return Float64(item.uint())
    if item.is_bool():
        return 1.0 if item.bool() else 0.0
    if item.is_string():
        # best-effort numeric string
        var s = item.string()
        if s == "true":
            return 1.0
        if s == "false" or s == "":
            return 0.0
        try:
            return Float64(atol(s))  # may fail for decimals
        except err:
            return default
    return default


def obj_bool(root: Value, key: String, default: Bool = False) raises -> Bool:
    if not root.is_object() or key not in root.object():
        return default
    var item = root.object()[key].copy()
    if item.is_bool():
        return item.bool()
    if item.is_int():
        return item.int() != 0
    if item.is_string():
        var s = item.string()
        return s == "true" or s == "1"
    return default


def obj_has(root: Value, key: String) raises -> Bool:
    return root.is_object() and key in root.object()


def nested(root: Value, key: String) raises -> Value:
    if not root.is_object() or key not in root.object():
        return Value(parse_string="{}")
    return root.object()[key].copy()


def quote(value: String) -> String:
    var result = "\""
    for i in range(value.byte_length()):
        var ch = value[byte=i]
        if ch == "\\":
            result += "\\\\"
        elif ch == "\"":
            result += "\\\""
        elif ch == "\n":
            result += "\\n"
        else:
            result += String(ch)
    result += "\""
    return result


def clamp01(value: Float64) -> Float64:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value
