"""
Data models
"""

import json
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class InterfaceField:
    """Interface field data model with enhanced functionality."""
    row_index: int = 0
    module: str = ''
    if_name: str = ''
    if_desc: str = ''
    field_name: str = ''
    key_flag: str = ''
    obligatory: str = ''
    data_type: str = ''
    field_id:str = ''
    length_total: str = ''
    length_dec: str = ''
    field_text: str = ''
    sample_value: str = ''

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for processing."""
        return {
            'row_index': self.row_index,
            'module': self.module,
            'if_name': self.if_name,
            'if_desc': self.if_desc,
            'field_name': self.field_name,
            'key_flag': self.key_flag,
            'obligatory': self.obligatory,
            'data_type': self.data_type,
            'field_id': self.filed_id,
            'length_total': self.length_total,
            'length_dec': self.length_dec,
            'field_text': self.field_text,
            'sample_value': self.sample_value
        }

    def to_query_string(self) -> str:
        """Generate query string for RAG search."""
        parts = []
        field_map = {
            "field_name": self.field_name,
            "field_desc": self.field_text,
            "is_key": self.key_flag,
            "obligatory": self.obligatory,
            "data_type": self.data_type,
            "field_id": self.filed_id,
            "length_total": self.length_total,
            "length_dec": self.length_dec,
            "sample_value": self.sample_value
        }

        for description, value in field_map.items():
            if value:
                parts.append(f"'{description}':'{value}'")

        return ",".join(filter(None, parts))