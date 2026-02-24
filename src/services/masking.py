from typing import Any, Dict, Optional

def mask_name(full_name: Optional[str]) -> Optional[str]:
    if full_name is None:
        return None
    s = full_name.strip()
    if not s:
        return s

    parts = s.split()
    masked_parts = []
    for p in parts:
        if len(p) <= 1:
            masked_parts.append("*")
        else:
            masked_parts.append(p[0] + "***")
    return " ".join(masked_parts)

def mask_customer_row(row: Dict[str, Any], salt: str) -> Dict[str, Any]:
    out = dict(row)
    out["full_name"] = mask_name(out["full_name"])
    return out