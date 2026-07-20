from splot.json_util import clamp01


def to_float_json(text: String) raises -> Float64:
    if text == "" or text == "null":
        return 0.0
    if text == "true":
        return 1.0
    if text == "false":
        return 0.0
    # Simple decimal parse
    var neg = False
    var i = 0
    if text.byte_length() > 0 and text[byte=0] == "-":
        neg = True
        i = 1
    var whole: Float64 = 0.0
    while i < text.byte_length():
        var ch = text[byte=i]
        if ch == ".":
            i += 1
            break
        if ch >= "0" and ch <= "9":
            whole = whole * 10.0 + Float64(Int(String(ch)))
        i += 1
    var frac: Float64 = 0.0
    var place: Float64 = 0.1
    while i < text.byte_length():
        var ch2 = text[byte=i]
        if ch2 >= "0" and ch2 <= "9":
            frac += Float64(Int(String(ch2))) * place
            place *= 0.1
        i += 1
    var value = whole + frac
    if neg:
        value = -value
    return value


def normalize_signal(
    value: Float64,
    prefer: String = "higher",
    target: Float64 = 0.5,
) -> Float64:
    if prefer == "boolean":
        return 1.0 if value != 0.0 else 0.0
    if prefer == "lower":
        return 1.0 - clamp01(value)
    if prefer == "target":
        return 1.0 - clamp01(abs(value - target))
    return clamp01(value)
