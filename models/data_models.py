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
            "length_total": self.length_total,
            "length_dec": self.length_dec,
            "sample_value": self.sample_value
        }

        for description, value in field_map.items():
            if value:
                parts.append(f"'{description}':'{value}'")

        return ",".join(filter(None, parts))


@dataclass
class CDSViewRecord:
    """CDS View record with enhanced parsing capabilities."""
    view_name: str
    view_desc: str
    view_fields: str

    def get_name(self) -> str:
        """Get view name."""
        return self.view_name

    def get_desc(self) -> str:
        """Get view description."""
        return self.view_desc

    def get_fields(self) -> str:
        """Get raw fields string."""
        return self.view_fields

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "view_name": self.view_name,
            "view_desc": self.view_desc,
            "view_fields": self.view_fields,
        }

    def parse_fields(self) -> List[List[Any]]:
        """Parse fields string into structured data."""
        try:
            fields_str = self.view_fields.strip()
            if not (fields_str.startswith('[[') and fields_str.endswith(']]')):
                return []

            try:
                parsed_data = json.loads(fields_str)
                return parsed_data
            except json.JSONDecodeError:
                return self._manual_parse_fields(fields_str)

        except Exception:
            return []

    def _manual_parse_fields(self, fields_str: str) -> List[List[Any]]:
        """Manual parsing fallback for complex field structures."""
        fields_str = fields_str[2:-2]

        parsed_fields = []
        current_field = ""
        bracket_count = 0
        in_quotes = False

        i = 0
        while i < len(fields_str):
            char = fields_str[i]

            if char == '"' and (i == 0 or fields_str[i - 1] != '\\'):
                in_quotes = not in_quotes
                current_field += char
            elif char == '[' and not in_quotes:
                bracket_count += 1
                current_field += char
            elif char == ']' and not in_quotes:
                bracket_count -= 1
                current_field += char

                if bracket_count == 0:
                    field_content = current_field.strip()
                    try:
                        field_array = json.loads(field_content)
                        parsed_fields.append(field_array)
                    except json.JSONDecodeError:
                        if field_content.startswith('[') and field_content.endswith(']'):
                            field_values = self._parse_single_field(field_content[1:-1])
                            parsed_fields.append(field_values)

                    current_field = ""

                    if i + 1 < len(fields_str) and fields_str[i + 1] == ',':
                        i += 1
            elif char == ',' and not in_quotes and bracket_count == 0:
                pass
            else:
                current_field += char

            i += 1

        if current_field.strip():
            field_content = current_field.strip()
            try:
                field_array = json.loads(field_content)
                parsed_fields.append(field_array)
            except json.JSONDecodeError:
                if field_content.startswith('[') and field_content.endswith(']'):
                    field_values = self._parse_single_field(field_content[1:-1])
                    parsed_fields.append(field_values)

        return parsed_fields

    def _parse_single_field(self, field_content: str) -> List[Any]:
        """Parse individual field content."""
        values = []
        current_value = ""
        in_quotes = False

        for i, char in enumerate(field_content):
            if char == '"' and (i == 0 or field_content[i - 1] != '\\'):
                in_quotes = not in_quotes
                current_value += char
            elif char == ',' and not in_quotes:
                if current_value.strip():
                    values.append(self._parse_field_value(current_value.strip()))
                current_value = ""
            else:
                current_value += char

        if current_value.strip():
            values.append(self._parse_field_value(current_value.strip()))

        return values

    def _parse_field_value(self, value_str: str) -> Any:
        """Parse individual field value with type conversion."""
        value_str = value_str.strip()

        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]

        if value_str.lower() == 'true':
            return True
        elif value_str.lower() == 'false':
            return False

        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass

        return value_str


@dataclass
class MatchResult:
    """Field matching result data model."""
    table_id: str = ''
    field_id: str = ''
    key_flag: str = ''
    obligatory: str = ''
    data_type: str = ''
    length_total: str = ''
    length_dec: str = ''
    field_desc: str = ''
    sample_value: str = ''
    notes: str = ''
    match_confidence: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'table_id': self.table_id,
            'field_id': self.field_id,
            'key_flag': self.key_flag,
            'obligatory': self.obligatory,
            'data_type': self.data_type,
            'length_total': self.length_total,
            'length_dec': self.length_dec,
            'field_desc': self.field_desc,
            'sample_value': self.sample_value,
            'notes': self.notes,
            'match_confidence': self.match_confidence
        }
