#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json


class DataTypeConverter:
    def __init__(self, logger=None):
        self._logger = logger

    @staticmethod
    def _to_string(value):
        if isinstance(value, bool):
            return "true" if value else "false"
        elif value is None:
            return "null"
        elif isinstance(value, (list, dict)):
            return json.dumps(value)
        else:
            return str(value)

    @staticmethod
    def _to_int(value):
        if isinstance(value, bool):
            return 1 if value else 0
        elif isinstance(value, str):
            if value.lower() in ["true", "yes", "y"]:
                return 1
            elif value.lower() in ["false", "no", "n"]:
                return 0
            else:
                return int(float(value))  # "3.14" -> 3
        elif value is None:
            return 0
        else:
            return int(value)

    @staticmethod
    def _to_float(value):
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        elif isinstance(value, str):
            if value.lower() in ["true", "yes", "y"]:
                return 1.0
            elif value.lower() in ["false", "no", "n"]:
                return 0.0
            else:
                return float(value)
        elif value is None:
            return 0.0
        else:
            return float(value)

    @staticmethod
    def _to_bool(value):
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return value.lower() in ["true", "yes", "y", "1"]
        elif isinstance(value, (int, float)):
            return value != 0
        elif value is None:
            return False
        else:
            return bool(value)

    @staticmethod
    def _to_list(value):
        if isinstance(value, list):
            return value
        elif isinstance(value, str):
            import json
            try:
                result = json.loads(value)
                return result if isinstance(result, list) else [result]
            except:
                return [value]
        elif isinstance(value, (tuple, set)):
            return list(value)
        elif value is None:
            return []
        else:
            return [value]

    @staticmethod
    def _to_dict(value):
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            import json
            return json.loads(value)
        elif value is None:
            return {}
        else:
            raise ValueError(f"Not changeable data type to dict: {type(value)}")

    @staticmethod
    def _get_default_value(target_type):
        defaults = {
            "string": "",
            "str": "",
            "int": 0,
            "integer": 0,
            "float": 0.0,
            "bool": False,
            "boolean": False,
            "list": [],
            "array": [],
            "dict": {},
            "object": {}
        }
        return defaults.get(target_type.lower(), None)

    def convert(self, value, target_type):
        target_type = target_type.lower()
        value_type = type(value)
        self._logger.debug(f" - converting value '{value}' (type: {type(value).__name__}) to '{target_type}'")
        if target_type == 'any_type' and value:
            target_type = value_type

        result = None

        try:
            if target_type == "string" or target_type == "str":
                result = self._to_string(value)

            elif target_type == "int" or target_type == "integer":
                result = self._to_int(value)

            elif target_type == "float":
                result = self._to_float(value)

            elif target_type == "bool" or target_type == "boolean":
                result = self._to_bool(value)

            elif target_type == "list" or target_type == "array":
                result = self._to_list(value)

            elif target_type == "dict" or target_type == "object":
                result = self._to_dict(value)

            else:
                self._logger.warn(f"not supported data type: {target_type}")
                result = value

            self._logger.debug(f"Conversion successful: '{value}' -> '{result}'")

        except ValueError as e:
            self._logger.warn(f"Not changeable data type: {type(value)}")
            error_msg = f": {value} -> {target_type}, 오류: {str(e)}"
            self._logger.error(error_msg)
        except Exception as e:
            error_msg = f": {value} -> {target_type}, 오류: {str(e)}"
            self._logger.error(error_msg)
        return result

    def convert_with_schema(self, data, schema):
        self._logger.debug(f"Starting schema-based conversion with {len(schema)} fields")
        result = {}

        for field_schema in schema:
            key = field_schema.get("key")
            target_type = field_schema.get("type")

            if key in data:
                result[key] = self.convert(data[key], target_type)
            else:
                default_value = self._get_default_value(target_type)
                self._logger.debug(f"Key '{key}' not found in data, using default value: {default_value}")
                result[key] = default_value
        return result


if __name__ == "__main__":
    import logging

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    converter = DataTypeConverter(logger)

    print("=== common data type converter ===")
    print(converter.convert(False, "string"))  # "false"
    print(converter.convert("123", "int"))  # 123
    print(converter.convert("3.14", "float"))  # 3.14
    print(converter.convert("true", "bool"))  # True
    print(converter.convert("hello", "list"))  # ["hello"]

    print("=== base of schema set converter ===")
    schema = [
        {"key": "test_value", "type": "string"},
        {"key": "count", "type": "int"},
        {"key": "price", "type": "float"},
        {"key": "is_active", "type": "bool"}
    ]

    data = {
        "test_value": False,
        "count": "42",
        "price": "99.99",
        "is_active": "yes"
    }

    result = converter.convert_with_schema(data, schema)
    print(result)
    # {'test_value': 'false', 'count': 42, 'price': 99.99, 'is_active': True}