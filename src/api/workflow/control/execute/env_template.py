# -*- coding: utf-8 -*-
#!/usr/bin/env python

from jinja2 import Template, Environment, meta
from typing import Dict, Any, List


class AutoTemplateRenderer:
    def __init__(self, logger):
        self._logger = logger
        self.env = Environment()

    def _extract_variables(self, template_string: str) -> List[str]:
        """템플릿에서 변수들을 추출"""
        ast = self.env.parse(template_string)
        return list(meta.find_undeclared_variables(ast))

    def _create_mapping(self, template_string: str, data_source: Dict[str, Any]) -> Dict[str, Any]:
        print("""템플릿 변수와 데이터 소스를 자동 매핑""")
        required_vars = self._extract_variables(template_string)
        template_map = {}
        missing_vars = []

        for var in required_vars:
            if var in data_source:
                template_map[var] = data_source[var]
            else:
                missing_vars.append(var)

        if missing_vars:
            print(f"경고: 다음 변수들의 값을 찾을 수 없습니다: {missing_vars}")
        print(template_map)
        print("-" * 100)
        return template_map

    def auto_render(self, template_string: str, data_source: Dict[str, Any]) -> str:
        print("""자동 매핑 후 렌더링""")
        template_map = self._create_mapping(template_string, data_source)
        template = Template(template_string)
        return template.render(**template_map)

    def analyze_and_render(self, template_string: str, data_source: Dict[str, Any]) -> Dict[str, Any]:
        print("""분석 정보와 함께 렌더링""")
        required_vars = self._extract_variables(template_string)
        template_map = self._create_mapping(template_string, data_source)

        template = Template(template_string)
        rendered = template.render(**template_map)

        rederer_info = {
            'required_variables': required_vars,
            'template_map': template_map,
            'missing_variables': [var for var in required_vars if var not in template_map],
            'rendered_result': rendered
        }
        print(rederer_info)
        return rederer_info
